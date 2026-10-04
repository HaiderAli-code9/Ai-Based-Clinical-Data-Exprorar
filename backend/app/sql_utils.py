"""Utilities for parsing generated SQL queries."""

import re
from typing import List

from table_catalog import KNOWN_TABLES


def extract_source_tables(sql_query: str) -> List[str]:
    """Return sorted source table names referenced in a SQL query."""
    if not sql_query or sql_query.strip().startswith("--"):
        return []

    sql_lower = sql_query.lower()
    found: List[str] = []
    for table in KNOWN_TABLES:
        if re.search(rf"\b{re.escape(table)}\b", sql_lower):
            found.append(table)
    return sorted(found)
