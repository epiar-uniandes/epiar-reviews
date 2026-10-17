"""Step 1 of the search pipeline. OpenAlex.

Downloads the records OpenAlex holds for each block of the active line and
writes them to one CSV file, together with a run log recording every query
sent, its parameters, the date it was run and how many records it returned.

OpenAlex charges a daily budget. A full line does not fit in one day of the
free budget, so this script is built to be run again: it writes every page
to disk as it arrives, keeps a progress file, and picks up where it left
off. It also saves its progress when interrupted.

Run with --test to work on a single small block and write to files marked
_TEST. The flag lives on the command line and never in config.py, so that a
test run cannot be left switched on by accident.
"""

import csv
import json
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

import config
import terms_line5

OPENALEX_WORKS = "https://api.openalex.org/works"

# OpenAlex requires an API key for cursor paging. It is read from a file
# that git ignores, never written into the code.
API_KEY = config.openalex_api_key()

# Longest the script will sit waiting for the server. Anything above this
# means the daily budget is gone, and waiting hours inside a running process
# is a worse bet than saving progress and coming back.
MAX_WAIT = 300

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


class BudgetExhausted(Exception):
    """Raised when the server asks us to wait longer than MAX_WAIT."""

    def __init__(self, seconds):
        super().__init__(f"budget exhausted, resets in {seconds}s")
        self.seconds = seconds


def redact(text):
    """Remove the API key before anything is printed or written to a log."""
    return text.replace(API_KEY, "REDACTED")


def openalex_query(terms):
    """Join the phrases of one block with OR, each one as a quoted phrase."""
    return " OR ".join(f'"{term}"' for term in terms)


def openalex_date_filter():
    """Build the date filter from the registered range."""
    return (f"from_publication_date:{config.YEAR_MIN}-01-01,"
            f"to_publication_date:{config.SEARCH_CUTOFF}")


def get_with_retry(url, params, attempts=5):
    """Send a request, retrying what is worth retrying.

    A short 429 means we are sending requests too fast, and a connection
    that drops is usually the network, so both are retried with a growing
    wait. A long 429 means the daily budget is gone, and that is raised as
    BudgetExhausted so the caller can save its progress and stop. Anything
    else is raised, so a query that failed never passes silently as zero
    records. Every message is redacted first, because the URL carries the
    API key and an unhandled error would otherwise print it.
    """
    wait = 2
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=120)
        except requests.exceptions.RequestException as error:
            if attempt == attempts:
                raise RuntimeError(
                    f"the connection failed {attempts} times: "
                    f"{redact(str(error))}") from None
            print(f"    connection problem, retrying in {wait}s "
                  f"(attempt {attempt} of {attempts})")
            time.sleep(wait)
            wait *= 2
            continue

        if response.status_code == 429:
            header = response.headers.get("Retry-After", "")
            pause = int(header) if header.isdigit() else wait
            if pause > MAX_WAIT:
                raise BudgetExhausted(pause)
            if attempt < attempts:
                print(f"    server asked to slow down, waiting {pause}s "
                      f"(attempt {attempt} of {attempts})")
                time.sleep(pause)
                wait *= 2
                continue

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(redact(str(error))) from None

        return response

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


def one_line(text):
    """Collapse line breaks and repeated spaces, so one record is one line."""
    return " ".join(text.split())


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
        "title": one_line(work.get("display_name", "") or ""),
        "abstract": one_line(abstract_from_inverted_index(
            work.get("abstract_inverted_index"))),
        "publication_year": work.get("publication_year", ""),
        "publication_date": work.get("publication_date", "") or "",
        "record_language": work.get("language", "") or "",
        "type": work.get("type", "") or "",
        "first_author": first_author(work),
        "venue": venue(work),
        "retrieved_at": retrieved_at,
    }


def download_block(block, writer, handle, state):
    """Download one block, writing every page to disk as it arrives.

    Paging uses a cursor rather than numbered pages, because OpenAlex does
    not serve numbered pages beyond 10,000 records and most blocks here are
    larger than that. The cursor of the next page is stored in state after
    every page, so an interrupted block can be resumed from there.
    """
    params = {
        "search.title_and_abstract": openalex_query(block["terms"]),
        "filter": openalex_date_filter(),
        "select": OPENALEX_FIELDS,
        "per_page": config.PAGE_SIZE,
        "api_key": API_KEY,
    }

    while state["cursor"]:
        page_params = dict(params, cursor=state["cursor"])
        response = get_with_retry(OPENALEX_WORKS, page_params)
        payload = response.json()

        if state.get("first_request_url") is None:
            state["first_request_url"] = redact(response.url)
            state["expected"] = payload["meta"]["count"]

        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        rows = [to_row(work, block, retrieved_at)
                for work in payload["results"]]
        writer.writerows(rows)
        handle.flush()

        state["written"] += len(rows)
        state["cursor"] = payload["meta"].get("next_cursor")
        print(f"    {state['written']:>8,} of {state['expected']:,}")
        time.sleep(config.REQUEST_PAUSE)

    state["status"] = "done"


def load_progress(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_progress(path, progress):
    path.write_text(json.dumps(progress, indent=2, ensure_ascii=False),
                    encoding="utf-8")


def main():
    if not config.SEARCH_CUTOFF:
        sys.exit("SEARCH_CUTOFF is not set in config.py. "
                 "The search cannot run without a fixed cut-off date.")

    testing = "--test" in sys.argv
    suffix = "_TEST" if testing else ""

    blocks = list(terms_line5.iter_blocks())
    if testing:
        blocks = [b for b in blocks
                  if (b["subintervention"], b["language"]) == TEST_BLOCK]
        print("TEST RUN. One block only.\n")

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    progress_path = (config.LOG_DIR /
                     f"{terms_line5.LINE}_openalex_progress{suffix}.json")

    progress = load_progress(progress_path)
    if progress and progress.get("cutoff") != config.SEARCH_CUTOFF:
        sys.exit(f"{progress_path} was written with cut-off "
                 f"{progress['cutoff']} but config.py now says "
                 f"{config.SEARCH_CUTOFF}. Delete the progress file to start "
                 f"a new search, or restore the cut-off.")

    if progress is None:
        stamp = datetime.now(timezone.utc).date().isoformat()
        progress = {
            "line": terms_line5.LINE,
            "source": "openalex",
            "cutoff": config.SEARCH_CUTOFF,
            "year_min": config.YEAR_MIN,
            "first_run": stamp,
            "csv": f"{terms_line5.LINE}_openalex_{stamp}{suffix}.csv",
            "blocks": {},
        }
        new_file = True
    else:
        new_file = False
        print(f"Resuming the run started on {progress['first_run']}.\n")

    csv_path = config.OUTPUT_DIR / progress["csv"]
    mode = "w" if new_file else "a"

    stopped = None
    with open(csv_path, mode, newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        if new_file:
            writer.writeheader()

        try:
            for block in blocks:
                key = f"{block['subintervention']}|{block['language']}"
                state = progress["blocks"].setdefault(key, {
                    "status": "pending",
                    "cursor": "*",
                    "written": 0,
                    "expected": None,
                    "first_request_url": None,
                    "terms": block["terms"],
                    "query": openalex_query(block["terms"]),
                    "filter": openalex_date_filter(),
                })

                if state["status"] == "done":
                    print(f"{block['subintervention_label']}, "
                          f"{block['language']}  already done, "
                          f"{state['written']:,} rows")
                    continue

                print(f"{block['subintervention_label']}, {block['language']}")
                download_block(block, writer, handle, state)

                if state["expected"] and state["written"] != state["expected"]:
                    print(f"    WARNING: wrote {state['written']:,} but the "
                          f"server reported {state['expected']:,}")
        except BudgetExhausted as stop:
            stopped = stop
        finally:
            save_progress(progress_path, progress)

    done = sum(1 for b in progress["blocks"].values()
               if b["status"] == "done")
    written = sum(b["written"] for b in progress["blocks"].values())
    print(f"\n{written:,} rows in {csv_path}")
    print(f"{done} of {len(blocks)} blocks finished")
    print(f"Progress saved to {progress_path}")

    if stopped:
        back = (datetime.now().astimezone()
                + timedelta(seconds=stopped.seconds))
        print(f"\nThe daily OpenAlex budget is spent. Run this again after "
              f"{back.strftime('%H:%M on %d %B')} and it will carry on from "
              f"where it stopped.")
        sys.exit(1)



if __name__ == "__main__":
    main()