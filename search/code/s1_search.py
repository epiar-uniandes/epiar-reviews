"""Step 1 of the search pipeline. OpenAlex.

Downloads the records OpenAlex holds for each block of the active line and
writes them to one CSV file, together with a run log recording every query
sent, its parameters, the date it was run and how many records it returned.

Run with --test to download a single small block and write it to a file
marked _TEST, for checking the output before the real run. The flag lives on
the command line and never in config.py, so that a test run cannot be left
switched on by accident.
"""

import csv
import json
import sys
import time
from datetime import datetime, timezone

import requests

import config
import terms_line5

OPENALEX_WORKS = "https://api.openalex.org/works"

# Only these fields are requested. Asking for the whole record would move far
# more data than the review needs.
OPENALEX_FIELDS = (
    "id,doi,display_name,publication_year,publication_date,language,type,"
    "authorships,primary_location,abstract_inverted_index"
)

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
]

# The block used by --test. Small enough to finish in seconds.
TEST_BLOCK = ("school_transportation", "pt")


def openalex_query(terms):
    """Join the phrases of one block with OR, each one as a quoted phrase."""
    return " OR ".join(f'"{term}"' for term in terms)


def openalex_date_filter():
    """Build the date filter from the registered range."""
    return (f"from_publication_date:{config.YEAR_MIN}-01-01,"
            f"to_publication_date:{config.SEARCH_CUTOFF}")


def get_with_retry(url, params, attempts=5):
    """Send a request, and wait when the server asks us to slow down.

    A 429 means we are sending requests too fast. We wait and try again,
    doubling the wait each time, honouring the Retry-After header when the
    server sends one. Any other error is raised, so that a query that failed
    never passes silently as zero records.
    """
    wait = 2
    for attempt in range(1, attempts + 1):
        response = requests.get(url, params=params, timeout=120)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        if attempt == attempts:
            response.raise_for_status()
        header = response.headers.get("Retry-After", "")
        pause = int(header) if header.isdigit() else wait
        print(f"    server asked to slow down, waiting {pause}s "
              f"(attempt {attempt} of {attempts})")
        time.sleep(pause)
        wait *= 2


def abstract_from_inverted_index(index):
    """Rebuild the abstract from the inverted index OpenAlex returns.

    OpenAlex does not store abstracts as text. For each word it stores the
    positions where that word occurs. This puts the words back in order.
    """
    if not index:
        return ""
    positions = []
    for word, places in index.items():
        for place in places:
            positions.append((place, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def first_author(work):
    authorships = work.get("authorships") or []
    if not authorships:
        return ""
    return (authorships[0].get("author") or {}).get("display_name", "")


def venue(work):
    location = work.get("primary_location") or {}
    return (location.get("source") or {}).get("display_name", "")


def to_row(work, block, retrieved_at):
    """Turn one OpenAlex record into one row of the CSV.

    The first three columns are the provenance the protocol promises: which
    sub-intervention and which language retrieved this record.
    """
    return {
        "line": block["line"],
        "subintervention": block["subintervention"],
        "search_language": block["language"],
        "source": "openalex",
        "record_id": work.get("id", ""),
        "doi": work.get("doi", "") or "",
        "title": work.get("display_name", "") or "",
        "abstract": abstract_from_inverted_index(
            work.get("abstract_inverted_index")),
        "publication_year": work.get("publication_year", ""),
        "publication_date": work.get("publication_date", "") or "",
        "record_language": work.get("language", "") or "",
        "type": work.get("type", "") or "",
        "first_author": first_author(work),
        "venue": venue(work),
        "retrieved_at": retrieved_at,
    }


def download_block(block, retrieved_at):
    """Download every record OpenAlex holds for one block.

    Paging uses a cursor rather than numbered pages, because OpenAlex does
    not serve numbered pages beyond 10,000 records and most blocks here are
    larger than that.
    """
    params = {
        "search.title_and_abstract": openalex_query(block["terms"]),
        "filter": openalex_date_filter(),
        "select": OPENALEX_FIELDS,
        "per_page": config.PAGE_SIZE,
        "mailto": config.CONTACT_EMAIL,
    }

    rows = []
    cursor = "*"
    expected = None
    first_url = None

    while cursor:
        page_params = dict(params, cursor=cursor)
        response = get_with_retry(OPENALEX_WORKS, page_params)
        payload = response.json()

        if first_url is None:
            first_url = response.url
            expected = payload["meta"]["count"]

        for work in payload["results"]:
            rows.append(to_row(work, block, retrieved_at))

        cursor = payload["meta"].get("next_cursor")
        print(f"    {len(rows):>8,} of {expected:,}")
        time.sleep(config.REQUEST_PAUSE)

    return rows, expected, first_url


def main():
    if not config.SEARCH_CUTOFF:
        sys.exit("SEARCH_CUTOFF is not set in config.py. "
                 "The search cannot run without a fixed cut-off date.")

    testing = "--test" in sys.argv
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamp = retrieved_at[:10]

    blocks = list(terms_line5.iter_blocks())
    if testing:
        blocks = [b for b in blocks
                  if (b["subintervention"], b["language"]) == TEST_BLOCK]
        suffix = "_TEST"
        print("TEST RUN. One block only.\n")
    else:
        suffix = ""

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = config.OUTPUT_DIR / f"{terms_line5.LINE}_openalex_{stamp}{suffix}.csv"
    log_path = config.LOG_DIR / f"{terms_line5.LINE}_openalex_{stamp}{suffix}.jsonl"

    written = 0
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as handle, \
            open(log_path, "w", encoding="utf-8") as log:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for block in blocks:
            print(f"{block['subintervention_label']}, {block['language']}")
            rows, expected, url = download_block(block, retrieved_at)
            writer.writerows(rows)
            written += len(rows)

            log.write(json.dumps({
                "line": block["line"],
                "subintervention": block["subintervention"],
                "language": block["language"],
                "source": "openalex",
                "terms": block["terms"],
                "query": openalex_query(block["terms"]),
                "filter": openalex_date_filter(),
                "first_request_url": url,
                "records_reported": expected,
                "records_written": len(rows),
                "retrieved_at": retrieved_at,
            }, ensure_ascii=False) + "\n")

            if expected is not None and len(rows) != expected:
                print(f"    WARNING: wrote {len(rows):,} but the server "
                      f"reported {expected:,}")

    print(f"\n{written:,} rows written to {csv_path}")
    print(f"Run log written to {log_path}")


if __name__ == "__main__":
    main()