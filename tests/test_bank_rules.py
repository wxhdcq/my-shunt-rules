from __future__ import annotations

from update_bank_rules import _domains_from_url


def test_bank_domain_parser_handles_fdic_reported_variants() -> None:
    assert _domains_from_url("www,chambersbank.com") == {"chambersbank.com"}
    assert _domains_from_url("http://www.bankfidelity.com; www.bankfidelity.bank") == {
        "bankfidelity.bank",
        "bankfidelity.com",
    }


def test_bank_domain_parser_preserves_meaningful_subdomains() -> None:
    assert _domains_from_url("https://online.asia.ccb.com/login") == {"online.asia.ccb.com"}
