"""Step 3 of the search pipeline. World Bank Open Knowledge Repository.

Downloads the documents the Bank's Documents and Reports repository holds
for the active line, and writes them to one CSV file together with a run
log.

Two things differ from the other two sources and are handled here:

1. The interface does not accept a single Boolean block, so each phrase is
   sent as its own query, paired with an education term in the language of
   the phrase, exactly as the registration states. The phrase that found
   each document is recorded, so the same document found by several
   phrases appears once per phrase and is deduplicated later, together
   with the other sources.
2. The repository stores a full publication date, so the registered
   cut-off day is applied by the API rather than afterwards.

The repository covers every sector of the Bank's work, which is why the
education term is part of the query here and not applied afterwards.

Run with --test to work on a single sub-intervention and write to files
marked _TEST.
"""

import csv
import json
import sys
import time
from datetime import datetime, timezone

import requests

import config
import terms_line5

WDS = "https://search.worldbank.org/api/v3/wds"

# Fields the repository returns. The abstract is nested inside abstracts
# under a key called cdata!, which is why it is read with a helper below.
WDS_FIELDS = ("id,display_title,abstracts,docdt,docty,lang,admreg,url,"
              "pdfurl,authors")

# Documents per request. The loop advances by the number of documents that
# actually came back, so a lower cap on the server side is harmless.
WDS_ROWS = 100

# The first fifteen columns are the ones shared with the other sources, so
# that the four can be pooled later. The last four are World Bank only.
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
    "wb_search_term",
    "wb_region",
    "wb_url",
    "wb_pdf_url",
]

TEST_SUBINTERVENTION = "school_transportation"


def one_line(text):
    """Collapse line breaks and repeated spaces, so one record is one line."""
    return " ".join(str(text).split())


def qterm(term, language):
    """Build the query for one phrase, with the education term of its language.

    The repository holds documents from every sector of the Bank, so the
    education term is what keeps the query inside education. The phrase is
    quoted and the education term is not, because the phrase is what the
    registration commits to and the education term is an anchor.
    """
    return f'"{term}" {config.EDUCATION_ANCHORS[language]}'


def ask(params):
    """Send one request to the repository and return the parsed body."""
    full = dict(params, format="json", fl=WDS_FIELDS)
    response = requests.get(WDS, params=full, timeout=120)
    response.raise_for_status()
    return response.json()


def documents(payload):
    """Return the documents of one page.

    The documents section is a mapping keyed by document identifier, and it
    has carried entries that are not documents, so only the values that
    look like a document are returned.
    """
    raw = payload.get("documents") or {}
    return [value for value in raw.values()
            if isinstance(value, dict) and value.get("id")]


def abstract_of(doc):
    """Read the abstract, which is nested under a key called cdata!."""
    abstracts = doc.get("abstracts")
    if isinstance(abstracts, dict):
        return abstracts.get("cdata!", "") or ""
    return ""


def first_author_of(doc):
    authors = doc.get("authors")
    if isinstance(authors, dict):
        values = [v for v in authors.values() if isinstance(v, str)]
        return values[0] if values else ""
    if isinstance(authors, list) and authors:
        return str(authors[0])
    if isinstance(authors, str):
        return authors
    return ""


def sanity_check():
    """Refuse to run if the repository does not appear to honour the query.

    A real phrase and a phrase that cannot occur anywhere are sent. If both
    report the same number of documents, the server is ignoring what was
    asked and any download from it would be meaningless.
    """
    real = ask({"qterm": '"school feeding" education', "rows": 1})
    nonsense = ask({"qterm": '"zzqxwv nonsense phrase" education', "rows": 1})

    print("Sanity check")
    print(f'  "school feeding" education          {real.get("total")}')
    print(f'  "zzqxwv nonsense phrase" education  {nonsense.get("total")}')

    if real.get("total") == nonsense.get("total"):
        sys.exit("\nThe repository returned the same count for a real phrase "
                 "and for a phrase that cannot exist. The query is being "
                 "ignored, so nothing is downloaded.")
    print()


def to_row(doc, block, term, retrieved_at):
    """Turn one document into one row of the CSV."""
    docdt = str(doc.get("docdt", "") or "")
    return {
        "line": block["line"],
        "subintervention": block["subintervention"],
        "search_language": block["language"],
        "source": "worldbank",
        "record_id": doc.get("id", ""),
        "doi": "",
        "title": one_line(doc.get("display_title", "") or ""),
        "abstract": one_line(abstract_of(doc)),
        "publication_year": docdt[:4],
        "publication_date": docdt[:10],
        "record_language": doc.get("lang", "") or "",
        "type": doc.get("docty", "") or "",
        "first_author": one_line(first_author_of(doc)),
        "venue": "World Bank Open Knowledge Repository",
        "retrieved_at": retrieved_at,
        "wb_search_term": term,
        "wb_region": doc.get("admreg", "") or "",
        "wb_url": doc.get("url", "") or "",
        "wb_pdf_url": doc.get("pdfurl", "") or "",
    }


def download_term(term, block, writer, handle):
    """Download every document the repository holds for one phrase.

    Paging is by offset. The offset advances by the number of documents
    that actually came back rather than by the number requested, so that a
    page smaller than requested does not skip anything.
    """
    params = {
        "qterm": qterm(term, block["language"]),
        "rows": WDS_ROWS,
        "strdate": f"{config.YEAR_MIN}-01-01",
        "enddate": config.SEARCH_CUTOFF,
    }

    first = ask(dict(params, os=0, rows=1))
    total = first.get("total", 0) or 0
    if total == 0:
        return 0, 0, 0

    written = 0
    offset = 0
    out_of_range = 0
    while offset < total:
        payload = ask(dict(params, os=offset))
        docs = documents(payload)
        if not docs:
            break
        retrieved_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds")
        for doc in docs:
            date = str(doc.get("docdt", "") or "")[:10]
            if date and not (f"{config.YEAR_MIN}-01-01" <= date
                             <= config.SEARCH_CUTOFF):
                out_of_range += 1
                continue
            writer.writerow(to_row(doc, block, term, retrieved_at))
            written += 1
        handle.flush()
        offset += len(docs)
        time.sleep(config.REQUEST_PAUSE)

    return total, written, out_of_range


def main():
    if not config.SEARCH_CUTOFF:
        sys.exit("SEARCH_CUTOFF is not set in config.py. "
                 "The search cannot run without a fixed cut-off date.")

    testing = "--test" in sys.argv
    suffix = "_TEST" if testing else ""

    blocks = list(terms_line5.iter_blocks())
    if testing:
        blocks = [b for b in blocks
                  if b["subintervention"] == TEST_SUBINTERVENTION]
        print("TEST RUN. One sub-intervention only.\n")

    sanity_check()

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    csv_path = (config.OUTPUT_DIR /
                f"{terms_line5.LINE}_worldbank_{stamp}{suffix}.csv")
    log_path = (config.LOG_DIR /
                f"{terms_line5.LINE}_worldbank_{stamp}{suffix}.json")

    phrases = sum(len(b["terms"]) for b in blocks)
    print(f"{len(blocks)} blocks, {phrases} phrases, one query each.")
    print(f"Dates {config.YEAR_MIN}-01-01 to {config.SEARCH_CUTOFF}, "
          f"applied by the API.\n")

    log = {
        "line": terms_line5.LINE,
        "source": "worldbank",
        "year_min": config.YEAR_MIN,
        "cutoff": config.SEARCH_CUTOFF,
        "education_anchors": config.EDUCATION_ANCHORS,
        "note": ("Each phrase is sent as its own query with an education "
                 "term in the language of the phrase, because the interface "
                 "does not accept a single Boolean block. A document found "
                 "by several phrases is written once per phrase and is "
                 "deduplicated later."),
        "retrieved_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
        "csv": csv_path.name,
        "queries": [],
    }

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for block in blocks:
            print(f"{block['subintervention_label']}, {block['language']}")
            block_written = 0
            for term in block["terms"]:
                total, written, out_of_range = download_term(
                    term, block, writer, handle)
                block_written += written
                log["queries"].append({
                    "subintervention": block["subintervention"],
                    "language": block["language"],
                    "term": term,
                    "qterm": qterm(term, block["language"]),
                    "documents_reported": total,
                    "documents_written": written,
                    "documents_outside_dates": out_of_range,
                })
                if total:
                    print(f"    {term[:45]:45s} {written:>5,} of {total:,}")
            print(f"  {block_written:,} rows for this block\n")

    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    written = sum(q["documents_written"] for q in log["queries"])
    reported = sum(q["documents_reported"] for q in log["queries"])
    stray = sum(q["documents_outside_dates"] for q in log["queries"])
    found = sum(1 for q in log["queries"] if q["documents_reported"])

    print(f"{written:,} rows written to {csv_path}")
    print(f"{reported:,} documents reported across {len(log['queries'])} "
          f"queries, {found} of which returned something")
    print(f"Run log written to {log_path}")

    if stray:
        print(f"\nNote: {stray:,} documents came back outside the date range "
              f"the API was asked for and were dropped here.")
    if written != reported - stray:
        print("\nWARNING: the rows written do not match what the server "
              "reported minus what was dropped.")
    else:
        print("\nThe rows written match what the server reported.")


if __name__ == "__main__":
    main()