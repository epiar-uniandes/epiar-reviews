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
SEARCH_CUTOFF = None

# Which intervention line to search. One module per line, terms_line5.py and so on.
ACTIVE_LINE = "line5"

# Where results and logs are written.
OUTPUT_DIR = ROOT.parent.parent / "data" / "raw"
LOG_DIR = ROOT.parent / "logs"