from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DIR = ROOT / "sources" / "custom"
HKMA_API = "https://api.hkma.gov.hk/public/bank-svf-info/acctopen-banks-contact?lang=en&offset=0"
FDIC_API = (
    "https://api.fdic.gov/banks/institutions?"
    "filters=ACTIVE%3A1&fields=NAME%2CWEBADDR%2CCERT&limit=10000"
)
V2FLY_FINANCE_SOURCES = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/schwab",
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/ibkr",
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/wise",
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/stripe",
)
HEADERS = {
    "Accept": "application/json",
    "Connection": "close",
    "User-Agent": "MyShuntRules/1.0",
}
HK_VIRTUAL_BANK_DOMAINS = {
    "airstarbank.com",
    "antbank.hk",
    "fusionbank.com",
    "livibank.com",
    "mox.com",
    "paob.com.hk",
    "welab.bank",
    "za.group",
}
US_CONSUMER_BANK_DOMAINS = {
    "chase.com",
    "comerica.com",
    "discover.com",
    "santanderbank.com",
    "zionsbank.com",
}
US_FINANCIAL_SERVICE_DOMAINS = {
    "acorns.com",
    "affirm.com",
    "alpaca.markets",
    "betterment.com",
    "cash.app",
    "chime.com",
    "current.com",
    "empower.com",
    "etrade.com",
    "fidelity.com",
    "fidelitycharitable.org",
    "fidelityinstitutional.com",
    "fidelityinvestments.com",
    "firstrade.com",
    "goldmansachs.com",
    "ibkr.ca",
    "ibkr.co.in",
    "ibkr.co.uk",
    "ibkr.com",
    "ibkr.com.au",
    "ibkr.com.hk",
    "ibkr.com.sg",
    "ibkr.eu",
    "ibkr.ie",
    "ibkrguides.com",
    "ibllc.com",
    "interactivebrokers.ca",
    "interactivebrokers.co.in",
    "interactivebrokers.co.jp",
    "interactivebrokers.co.uk",
    "interactivebrokers.com",
    "interactivebrokers.com.au",
    "interactivebrokers.com.hk",
    "interactivebrokers.com.sg",
    "interactivebrokers.eu",
    "interactivebrokers.ie",
    "klarna.com",
    "marcus.com",
    "merrilledge.com",
    "ml.com",
    "moomoo.com",
    "morganstanley.com",
    "netbenefits.com",
    "ninjatrader.com",
    "payoneer.com",
    "plaid.com",
    "public.com",
    "remitly.com",
    "revolut.com",
    "robinhood.com",
    "schwab.com",
    "schwab.com.hk",
    "schwab.com.sg",
    "schwabassetmanagement.com",
    "schwabplan.com",
    "sofi.com",
    "squareup.com",
    "tastytrade.com",
    "tradestation.com",
    "tradier.com",
    "vanguard.com",
    "varomoney.com",
    "venmo.com",
    "wealthfront.com",
    "webull.com",
    "zelle.com",
    "zellepay.com",
}
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$")


def _fetch_json(url: str) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 3:
                print(f"Warning: bank data request failed (attempt {attempt}/3): {exc}")
                time.sleep(attempt)
    raise RuntimeError(f"bank data request failed after 3 attempts: {last_error}")


def _fetch_text(url: str) -> str:
    request = Request(url, headers={**HEADERS, "Accept": "text/plain"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def _domains_from_url(value: object) -> set[str]:
    if not isinstance(value, str) or not value.strip():
        return set()

    domains: set[str] = set()
    for candidate in re.split(r"[;\n]+", value):
        candidate = candidate.strip()
        candidate = re.sub(r"^www[,:]", "www.", candidate, flags=re.IGNORECASE)
        if not candidate:
            continue
        if "://" not in candidate:
            candidate = f"https://{candidate}"
        hostname = urlsplit(candidate).hostname
        if not hostname:
            continue
        hostname = hostname.lower().rstrip(".")
        if hostname.startswith("www."):
            hostname = hostname[4:]
        try:
            hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError:
            continue
        if DOMAIN_RE.fullmatch(hostname):
            domains.add(hostname)
    return domains


def _fetch_hong_kong_domains() -> set[str]:
    payload = _fetch_json(HKMA_API)
    result = payload.get("result")
    records = result.get("records") if isinstance(result, dict) else None
    if not isinstance(records, list) or len(records) < 20:
        raise RuntimeError("HKMA response did not contain the expected bank contact records")

    domains = set(HK_VIRTUAL_BANK_DOMAINS)
    for record in records:
        if not isinstance(record, dict):
            continue
        for key, value in record.items():
            if key.endswith("_url"):
                domains.update(_domains_from_url(value))
    if len(domains) < 35:
        raise RuntimeError(f"HKMA bank domain coverage unexpectedly low: {len(domains)}")
    return domains


def _fetch_us_domains() -> set[str]:
    payload = _fetch_json(FDIC_API)
    data = payload.get("data")
    if not isinstance(data, list) or len(data) < 4_000:
        raise RuntimeError("FDIC response did not contain the expected active institution records")

    domains: set[str] = set(US_CONSUMER_BANK_DOMAINS)
    institutions_with_websites = 0
    for wrapper in data:
        record = wrapper.get("data") if isinstance(wrapper, dict) else None
        if not isinstance(record, dict) or not record.get("WEBADDR"):
            continue
        institutions_with_websites += 1
        domains.update(_domains_from_url(record["WEBADDR"]))
    if institutions_with_websites < 4_000 or len(domains) < 3_500:
        raise RuntimeError(
            "FDIC website coverage unexpectedly low: "
            f"institutions={institutions_with_websites}, domains={len(domains)}"
        )
    return domains


def _fetch_us_financial_service_domains() -> set[str]:
    domains = set(US_FINANCIAL_SERVICE_DOMAINS)
    successful_sources = 0
    failed_sources = 0
    for source_url in V2FLY_FINANCE_SOURCES:
        try:
            text = _fetch_text(source_url)
        except OSError as exc:
            print(f"Warning: skip GitHub finance source {source_url}: {exc}")
            failed_sources += 1
            continue
        successful_sources += 1
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or line.startswith(("include:", "regexp:", "full:")):
                continue
            domains.update(_domains_from_url(line.removeprefix("domain:")))
    if successful_sources == 0:
        raise RuntimeError("all GitHub financial service sources failed")
    if failed_sources:
        existing_path = CUSTOM_DIR / "us-financial-services.txt"
        if existing_path.exists():
            existing_domains = {
                line.partition(",")[2].strip()
                for line in existing_path.read_text(encoding="utf-8").splitlines()
                if line.startswith("DOMAIN-SUFFIX,")
            }
            domains.update(existing_domains)
            print(
                "Warning: merged existing US financial service rules because "
                f"{failed_sources} GitHub source(s) failed"
            )
    if len(domains) < 50:
        raise RuntimeError(f"US financial service coverage unexpectedly low: {len(domains)}")
    return domains


def _write_rules(path: Path, title: str, source_urls: tuple[str, ...], domains: set[str]) -> None:
    lines = [
        f"# {title}",
        "# Generated by scripts/update_bank_rules.py; do not edit manually.",
        *[f"# Source: {url}" for url in source_urls],
        f"# Unique domains: {len(domains)}",
        "",
        *[f"DOMAIN-SUFFIX,{domain}" for domain in sorted(domains)],
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _update_with_fallback(
    path: Path,
    title: str,
    source_urls: tuple[str, ...],
    fetcher: Callable[[], set[str]],
    *,
    strict: bool,
) -> int:
    try:
        domains = fetcher()
    except Exception as exc:
        if not path.exists():
            raise
        existing_count = sum(
            1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("DOMAIN-SUFFIX,")
        )
        if existing_count == 0:
            raise RuntimeError(f"cannot use empty fallback for {path.name}") from exc
        mode = "strict mode fallback" if strict else "fallback"
        print(f"Warning: keep {existing_count} existing rules in {path.name} ({mode}): {exc}")
        return existing_count

    _write_rules(path, title, source_urls, domains)
    return len(domains)


def main() -> int:
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    strict = os.environ.get("MYSHUNTRULES_STRICT_FETCH", "").strip().lower() in {"1", "true", "yes"}
    hk_count = _update_with_fallback(
        CUSTOM_DIR / "hong-kong-banks.txt",
        "Hong Kong Banks",
        (HKMA_API, "https://vpr.hkma.gov.hk/eng/regulatory-resources/registers/register-of-ais-and-lros/"),
        _fetch_hong_kong_domains,
        strict=strict,
    )
    us_count = _update_with_fallback(
        CUSTOM_DIR / "us-banks.txt",
        "United States Banks",
        (FDIC_API, "https://api.fdic.gov/banks/docs"),
        _fetch_us_domains,
        strict=strict,
    )
    finance_count = _update_with_fallback(
        CUSTOM_DIR / "us-financial-services.txt",
        "US Financial Services",
        (
            *V2FLY_FINANCE_SOURCES,
            "https://github.com/v2fly/domain-list-community",
            "https://www.schwab.com/",
            "https://www.fidelity.com/",
            "https://www.revolut.com/en-US/",
        ),
        _fetch_us_financial_service_domains,
        strict=strict,
    )
    print(
        "Updated bank rules: "
        f"hong-kong-banks={hk_count}, us-banks={us_count}, us-financial-services={finance_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
