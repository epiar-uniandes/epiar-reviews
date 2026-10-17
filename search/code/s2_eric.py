"""Step 2 of the search pipeline. ERIC.

Downloads the records ERIC holds for the English block of each
sub-intervention of the active line, and writes them to one CSV file.

Three things differ from OpenAlex and are handled here:

1. Only the English terms are sent, because ERIC indexes non-English
   records with English titles and abstracts, as the registration states.
2. ERIC stores a publication year, not a full date. The registered cut-off
   is a day, so the year range is applied and the limitation is reported.
   Records of the cut-off year published after the cut-off day cannot be
   excluded, and that is a property of the source, not a choice.
3. ERIC is free and has no key, so there is no budget to spend and no
   resume file. If a run fails, it is simply run again.

Run with --test to work on a single sub-intervention and write to a file
marked _TEST.
"""

import csv
import sys
import time
from datetime import datetime, timezone

import requests

import config
import terms_line5

ERIC = "https://api.ies.ed.gov/eric/"

# Fields ERIC returns. The abstract is called description here.
ERIC_FIELDS = ("id,title,author,source,publicationdateyear,description,"
               "subject,peerreviewed")

# The first fifteen columns are the ones shared with the OpenAlex file, so
# that the four sources can be pooled later. The last two are ERIC only.
CSV_COLUMNS = [
    "line",
    "subintervention",
    "search_language",
    "source",
    "record_id",
    "doi",
    "title",
    "abstract",
    "publication_year",
    "publication_date",
    "record_language",
    "type",
    "first_author",
    "venue",
    "retrieved_at",
    "eric_subject",
    "eric_peer_reviewed",
]

TEST_SUBINTERVENTION = "school_transportation"

YEAR_MAX = int(config.SEARCH_CUTOFF[:4])


def eric_query(terms):
    """Join the phrases of one block with OR, each one as a quoted phrase."""
    return " OR ".join(f'"{term}"' for term in terms)


def request(query, rows, start):
    """Send one request to ERIC and return the response section."""
    params = {
        "search": query,
        "format": "json",
        "rows": rows,
        "start": start,
        "fields": ERIC_FIELDS,
    }
    response = requests.get(ERIC, params=params, timeout=120)
    response.raise_for_status()
    return response.json().get("response", {})


def sanity_check():
    """Refuse to run if ERIC does not appear to honour the query.

    A real phrase and a phrase that cannot occur anywhere are sent. If both
    report the same number of records, the server is ignoring what was
    asked and any download from it would be meaningless. The quoted and
    unquoted forms of the same phrase are also compared, because the
    registration states that terms are entered as quoted phrases, and that
    claim has to be true of what actually runs.
    """
    real = request('"school feeding"', 1, 0).get("numFound")
    nonsense = request('"zzqxwv nonsense phrase"', 1, 0).get("numFound")
    unquoted = request('school feeding', 1, 0).get("numFound")

    print("Sanity check")
    print(f'  "school feeding"          {real}')
    print(f'  school feeding            {unquoted}')
    print(f'  "zzqxwv nonsense phrase"  {nonsense}')

    if real == nonsense:
        sys.exit("\nERIC returned the same count for a real phrase and for a "
                 "phrase that cannot exist. The query is being ignored, so "
                 "nothing is downloaded. This has to be resolved before the "
                 "ERIC search can be run.")

    if real == unquoted:
        print("\n  Note: the quoted and unquoted forms return the same "
              "count. Either the phrase is matched the same way both times, "
              "or the quotes are being dropped. Worth confirming against a "
              "known record before the final run.")
    print()


def to_row(doc, block, retrieved_at):
    """Turn one ERIC record into one row of the CSV."""
    author = doc.get("author", "")
    if isinstance(author, list):
        author = author[0] if author else ""
    subject = doc.get("subject", "")
    if isinstance(subject, list):
        subject = "; ".join(subject)
    return {
        "line": block["line"],
        "subintervention": block["subintervention"],
        "search_language": block["language"],
        "source": "eric",
        "record_id": doc.get("id", ""),
        "doi": "",
        "title": one_line(doc.get("title", "") or ""),
        "abstract": one_line(doc.get("description", "") or ""),
        "publication_year": doc.get("publicationdateyear", ""),
        "publication_date": "",
        "record_language": "",
        "type": "",
        "first_author": author,
        "venue": doc.get("source", "") or "",
        "retrieved_at": retrieved_at,
        "eric_subject": one_line(subject),
        "eric_peer_reviewed": doc.get("peerreviewed", ""),
    }


def one_line(text):
    """Collapse line breaks and repeated spaces, so one record is one line."""
    return " ".join(str(text).split())


def download_block(block, writer, handle):
    """Download every ERIC record for one block, page by page.

    Paging is by offset, because ERIC has no cursor. Records outside the
    registered year range are dropped here rather than in the query, so
    that the count that was dropped is known and can be reported.
    """
    query = eric_query(block["terms"])
    total = request(query, 1, 0).get("numFound", 0)
    print(f"    server reports {total:,}")

    written = 0
    out_of_range = 0
    start = 0
    while start < total:
        docs = request(query, config.PAGE_SIZE, start).get("docs", [])
        if not docs:
            break
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for doc in docs:
            year = str(doc.get("publicationdateyear", ""))
            if year.isdigit() and not (config.YEAR_MIN <= int(year) <= YEAR_MAX):
                out_of_range += 1
                continue
            writer.writerow(to_row(doc, block, retrieved_at))
            written += 1
        handle.flush()
        start += config.PAGE_SIZE
        print(f"    {written:>8,} kept, {out_of_range:,} outside the years")
        time.sleep(config.REQUEST_PAUSE)

    return total, written, out_of_range


def main():
    if not config.SEARCH_CUTOFF:
        sys.exit("SEARCH_CUTOFF is not set in config.py. "
                 "The search cannot run without a fixed cut-off date.")

    testing = "--test" in sys.argv
       
    suffix = "_TEST" if testing else ""

    # Only the English block of each sub-intervention, as registered.
    blocks = [b for b in terms_line5.iter_blocks() if b["language"] == "en"]
    if testing:
        blocks = [b for b in blocks
                  if b["subintervention"] == TEST_SUBINTERVENTION]
        print("TEST RUN. One sub-intervention only.\n")

    sanity_check()

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    csv_path = config.OUTPUT_DIR / f"{terms_line5.LINE}_eric_{stamp}{suffix}.csv"

    print(f"Years {config.YEAR_MIN} to {YEAR_MAX}. ERIC stores a year and "
          f"not a day, so records of {YEAR_MAX} published after "
          f"{config.SEARCH_CUTOFF} cannot be excluded.\n")

    totals = []
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for block in blocks:
            print(f"{block['subintervention_label']}, {block['language']}")
            totals.append((block["subintervention"],)
                          + download_block(block, writer, handle))

    written = sum(t[2] for t in totals)
    dropped = sum(t[3] for t in totals)
    print(f"\n{written:,} rows written to {csv_path}")
    print(f"{dropped:,} records dropped for falling outside "
          f"{config.YEAR_MIN} to {YEAR_MAX}")


if __name__ == "__main__":
    main()