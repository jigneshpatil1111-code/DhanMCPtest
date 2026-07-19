from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Nifty500Member:
    symbol: str
    company_name: str
    industry: str
    isin: str


def universe_csv_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "nifty500.csv"


@lru_cache(maxsize=1)
def load_nifty500_members() -> tuple[Nifty500Member, ...]:
    with universe_csv_path().open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        members = tuple(
            Nifty500Member(
                symbol=row["Symbol"].strip().upper(),
                company_name=row["Company Name"].strip(),
                industry=row["Industry"].strip(),
                isin=row["ISIN Code"].strip(),
            )
            for row in rows
            if row.get("Series", "").strip().upper() == "EQ"
        )

    if len(members) != 500:
        raise RuntimeError(f"Expected 500 Nifty constituents, found {len(members)}.")
    return members


@lru_cache(maxsize=1)
def nifty500_symbols() -> frozenset[str]:
    return frozenset(member.symbol for member in load_nifty500_members())


def search_nifty500(query: str = "", limit: int = 25) -> list[Nifty500Member]:
    normalized = query.strip().casefold()
    matches = [
        member
        for member in load_nifty500_members()
        if not normalized
        or normalized in member.symbol.casefold()
        or normalized in member.company_name.casefold()
    ]
    return matches[: max(1, min(limit, 100))]
