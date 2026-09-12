from __future__ import annotations

from pathlib import Path
import sys
from urllib.error import URLError

import pytest

from lib import build_guard, pipeline
from lib.models import ProjectConfig, RepoConfig, RuleCategory, UpstreamSource


class Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body[:size] if size >= 0 else self.body


@pytest.fixture
def sources(tmp_path, monkeypatch):
    for attribute, name in (("RAW_CACHE_DIR", "raw"), ("NORMALIZED_CACHE_DIR", "normalized"),
                            ("MERGED_CACHE_DIR", "merged"), ("CUSTOM_DIR", "custom")):
        directory = tmp_path / name
        directory.mkdir()
        monkeypatch.setattr(pipeline, attribute, directory)
    for name in ("a", "b"):
        (tmp_path / "raw" / (name + ".txt")).write_text(f"DOMAIN,old-{name}.test\n")
        (tmp_path / "custom" / (name + ".txt")).write_text("# No custom rules\n")
    return ProjectConfig(RepoConfig("fixture", "fixture"),
        [RuleCategory(name, name, name, name + ".txt") for name in ("a", "b")],
        [UpstreamSource(name, name, "surge", f"https://example.test/{name}") for name in ("a", "b")])


def response_sequence(monkeypatch, values):
    values = iter(values)

    def open_mock(*args, **kwargs):
        item = next(values)
        if isinstance(item, Exception):
            raise item
        return Response(item)

    monkeypatch.setattr(pipeline, "urlopen", open_mock)


def cache_bytes():
    return {p.name: p.read_bytes() for p in pipeline.RAW_CACHE_DIR.glob("*")}


@pytest.mark.parametrize("bad", [URLError("offline"), b"", b"# comment only\n",
    b"<!DOCTYPE html><html>error</html>", b"<body>DOMAIN,valid.test</body>",
    b"DOMAIN,%%%\n", b"IP-CIDR,not-an-ip\n", b"\xff\xfe",
    b"DOMAIN,good.test\nDOMAIN,\n", b"DOMAIN,good.test\nIP-CIDR,\n"])
def test_any_failed_or_invalid_source_preserves_entire_strict_cache(sources, monkeypatch, bad):
    before = cache_bytes()
    response_sequence(monkeypatch, [b"DOMAIN,new.test\n", bad])
    with pytest.raises(RuntimeError, match="incomplete upstream"):
        pipeline.fetch_upstream_sources(sources, strict=True)
    assert cache_bytes() == before


def test_valid_refresh_updates_all_sources(sources, monkeypatch):
    response_sequence(monkeypatch, [b"\xef\xbb\xbfDOMAIN,a.test\nDOMAIN,a.test\n", b"DOMAIN,b.test\n"])
    results = pipeline.fetch_upstream_sources(sources, strict=True)
    assert [count for _, count in results] == [1, 1]
    assert cache_bytes()["a.txt"] == b"DOMAIN,a.test\nDOMAIN,a.test\n"
    assert cache_bytes()["b.txt"] == b"DOMAIN,b.test\n"


def test_best_effort_does_not_destroy_failed_source(sources, monkeypatch):
    response_sequence(monkeypatch, [b"DOMAIN,new.test\n", URLError("offline")])
    pipeline.fetch_upstream_sources(sources, strict=False)
    assert cache_bytes()["a.txt"] == b"DOMAIN,new.test\n"
    assert cache_bytes()["b.txt"] == b"DOMAIN,old-b.test\n"


def test_oversized_response_is_rejected_before_cache_update(sources, monkeypatch):
    before = cache_bytes()
    monkeypatch.setattr(pipeline, "MAX_SOURCE_BYTES", 32)
    response_sequence(monkeypatch, [b"DOMAIN,a.test\n" * 5, b"DOMAIN,b.test\n"])
    with pytest.raises(RuntimeError):
        pipeline.fetch_upstream_sources(sources, strict=True)
    assert cache_bytes() == before


def test_strict_normalization_rejects_missing_raw(sources):
    (pipeline.RAW_CACHE_DIR / "a.txt").unlink()
    with pytest.raises(RuntimeError, match="Missing raw"):
        pipeline.normalize_upstream_sources(sources, strict=True)


def test_strict_merge_rejects_missing_normalized(sources, monkeypatch):
    monkeypatch.setenv("MYSHUNTRULES_STRICT_FETCH", "1")
    with pytest.raises(RuntimeError, match="Missing normalized"):
        pipeline.merge_group_rules(sources)


def rules(count):
    return "".join(f"DOMAIN,d{i}.test\n" for i in range(count)).encode()


def test_large_rule_loss_uses_previous_release_as_baseline():
    before = {"dist/surge/a.list": rules(100)}
    build_guard.check_rule_changes(before, {"dist/surge/a.list": rules(80)})
    with pytest.raises(RuntimeError, match="100 -> 79"):
        build_guard.check_rule_changes(before, {"dist/surge/a.list": rules(79)})
    build_guard.check_rule_changes(before, {"dist/surge/a.list": rules(1)}, allow_large_drop=True)


def test_large_drop_override_never_allows_empty_output():
    with pytest.raises(RuntimeError, match="no effective rules"):
        build_guard.check_rule_changes({"dist/surge/a.list": rules(100)},
            {"dist/surge/a.list": b"# Still nonempty text\n"}, allow_large_drop=True)


def miniature_project(tmp_path):
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "dist/surge").mkdir(parents=True)
    (root / "dist/surge/a.list").write_bytes(rules(3))
    (root / "README.md").write_text("old readme\n")
    for script in ("validate.py", "validate_rules.py"):
        (root / "scripts" / script).write_text("# Fixture validation command\n")
    (root / "tests/test_ok.py").write_text("def test_ok():\n    assert True\n")
    return root


def test_failed_build_step_never_changes_release(tmp_path):
    root = miniature_project(tmp_path)
    before = build_guard.published_snapshot(root)
    code = "from pathlib import Path; Path('dist/surge/a.list').write_text('broken'); raise SystemExit(7)"
    assert build_guard.run_guarded_build(root, [("broken", [sys.executable, "-c", code])]) == 7
    assert build_guard.published_snapshot(root) == before


def test_validation_failure_leaves_old_release(tmp_path):
    root = miniature_project(tmp_path)
    (root / "scripts/validate_rules.py").write_text("raise SystemExit(9)\n")
    before = build_guard.published_snapshot(root)
    assert build_guard.run_guarded_build(root, []) == 1
    assert build_guard.published_snapshot(root) == before


def test_guard_detects_tests_that_rewrite_release(tmp_path):
    root = miniature_project(tmp_path)
    (root / "tests/test_ok.py").write_text(
        "from pathlib import Path\ndef test_bad():\n    Path('README.md').write_text('mutated')\n")
    before = build_guard.published_snapshot(root)
    assert build_guard.run_guarded_build(root, []) == 1
    assert build_guard.published_snapshot(root) == before


def test_successful_build_publishes_validated_candidate(tmp_path):
    root = miniature_project(tmp_path)
    code = "from pathlib import Path; Path('README.md').write_text('new readme\\n')"
    assert build_guard.run_guarded_build(root, [("render", [sys.executable, "-c", code])]) == 0
    assert (root / "README.md").read_text() == "new readme\n"


@pytest.mark.parametrize("persistent", [False, True])
def test_failed_file_replacement_rolls_back_all_prior_changes(tmp_path, monkeypatch, persistent):
    before = {"dist/a.txt": b"old a", "dist/b.txt": b"old b"}
    after = {"dist/a.txt": b"new a", "dist/b.txt": b"new b"}
    build_guard.publish_snapshot(tmp_path, {}, before)
    original = build_guard._write_atomic
    failed = False

    def fail_once(path, content):
        nonlocal failed
        if path.name == "b.txt" and (persistent or not failed):
            failed = True
            raise OSError("simulated disk failure")
        original(path, content)

    monkeypatch.setattr(build_guard, "_write_atomic", fail_once)
    with pytest.raises(OSError):
        build_guard.publish_snapshot(tmp_path, before, after)
    assert build_guard.published_snapshot(tmp_path) == before


def test_rollback_continues_after_one_restore_fails(tmp_path, monkeypatch):
    before = {f"dist/{name}.txt": f"old {name}".encode() for name in ("a", "b", "c")}
    after = {f"dist/{name}.txt": f"new {name}".encode() for name in ("a", "b", "c")}
    build_guard.publish_snapshot(tmp_path, {}, before)
    original = build_guard._write_atomic

    def failed_write(path, content):
        if path.name == "c.txt" or (path.name == "b.txt" and content == b"old b"):
            raise PermissionError("simulated persistent failure")
        original(path, content)

    monkeypatch.setattr(build_guard, "_write_atomic", failed_write)
    with pytest.raises(RuntimeError, match="rollback incomplete for: dist/b.txt"):
        build_guard.publish_snapshot(tmp_path, before, after)
    assert (tmp_path / "dist/a.txt").read_bytes() == b"old a"
    assert (tmp_path / "dist/c.txt").read_bytes() == b"old c"


def test_build_help_can_be_displayed():
    import subprocess

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "build.py"), "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "--allow-large-drop" in result.stdout
