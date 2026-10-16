"""Shared configuration for the EPIAR search pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Contact address sent to the APIs. OpenAlex uses it for its polite pool,
# which gives faster and more reliable responses.
CONTACT_EMAIL = "ja.sanchezd1@uniandes.edu.co"

# Earliest publication year included in the search, as registered.
YEAR_MIN = 1990

# Last publication date included in the search. The protocol promises the
# search runs once against a predefined date, so that two people running
# this code on different days retrieve the same records. Set it before the
# first real run and do not change it afterwards. Format YYYY-MM-DD.
SEARCH_CUTOFF = "2026-08-17"

# Which intervention line to search. One module per line, terms_line5.py and so on.
ACTIVE_LINE = "line5"

# Where results and logs are written.
OUTPUT_DIR = ROOT.parent.parent / "data" / "raw"
LOG_DIR = ROOT.parent / "logs"

# How many records OpenAlex returns per request, and how long to wait
# between requests. The pause is courtesy, not speed.
PAGE_SIZE = 200
REQUEST_PAUSE = 1.0

# OpenAlex requires an API key. A key is a credential, so it is kept in a
# file that git ignores and is never written into this file, which is
# public. The file holds the key on a single line.
KEY_FILE = ROOT.parent.parent / "openalex_key.txt"


def openalex_api_key():
    """Read the OpenAlex API key from the ignored key file."""
    if not KEY_FILE.exists():
        raise SystemExit(
            f"No OpenAlex API key found. Create {KEY_FILE} with the key on "
            f"a single line. That file is ignored by git on purpose."
        )
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit(f"{KEY_FILE} is empty.")
    return key