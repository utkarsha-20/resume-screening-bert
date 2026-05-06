import re
from datetime import datetime

CURRENT_YEAR = datetime.now().year

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

# Matches patterns like:
# 2018–2020 | 2018-2020 | 2020–Present | June 2019–Aug 2023
DATE_RANGE_RE = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+)?"
    r"(\d{4})\s*[-–—]\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+)?(\d{4}|present|current|now)",
    re.IGNORECASE
)


def _parse_year(raw):
    raw = raw.strip().lower()
    if raw in ("present", "current", "now"):
        return CURRENT_YEAR
    return int(raw)


def extract_experience(text):
    """Return total years of experience as a float rounded to 1 decimal."""
    total_months = 0
    seen = set()

    for match in DATE_RANGE_RE.finditer(text):
        start_year = int(match.group(1))
        end_year = _parse_year(match.group(3))

        key = (start_year, end_year)
        if key in seen:
            continue
        seen.add(key)

        if end_year < start_year:
            continue

        total_months += (end_year - start_year) * 12

    years = round(total_months / 12, 1)
    return years
