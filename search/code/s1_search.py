"""Step 1 of the search pipeline. First version, OpenAlex only.

This version saves nothing. It sends one query to OpenAlex and prints what
it sent and what came back, so that the query can be checked against the
registration before the full search is run.
"""
import time

import requests

import config #code created
import terms_line5

OPENALEX_WORKS = "https://api.openalex.org/works"

def openalex_query(terms):
    """Join the phrases of one block with OR, each one as a quoted phrase."""
    return " OR ".join(f'"{term}"' for term in terms)


def openalex_date_filter():
    """Build the date filter from the registered range."""
    parts = [f"from_publication_date:{config.YEAR_MIN}-01-01"]
    if config.SEARCH_CUTOFF:
        parts.append(f"to_publication_date:{config.SEARCH_CUTOFF}")
    return ",".join(parts)


def probe(block):
    params = {
        "search.title_and_abstract": openalex_query(block["terms"]),
        "filter": openalex_date_filter(),
        "per_page": 1,
        "mailto": config.CONTACT_EMAIL,
    }
    response = requests.get(OPENALEX_WORKS, params=params, timeout=60)

    print("URL sent:")
    print(response.url)
    print()
    print("HTTP status:", response.status_code)
    response.raise_for_status()

    payload = response.json()
    print("Records found:", payload["meta"]["count"])
    results = payload.get("results", [])
    if results:
        print("First record:", results[0].get("display_name"))

def get_with_retry(url, params, attempts=5):
    """Send a request, and wait when the server asks us to slow down.

    A 429 means we are sending requests too fast. We wait and try again,
    doubling the wait each time, honouring the Retry-After header when the
    server sends one. Any other error is raised, so that a query that failed
    never passes silently as zero records.
    """
    wait = 2
    for attempt in range(1, attempts + 1):
        response = requests.get(url, params=params, timeout=60)
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

def count_openalex(block):
    """Return how many records OpenAlex holds for one block."""
    params = {
        "search.title_and_abstract": openalex_query(block["terms"]),
        "filter": openalex_date_filter(),
        "per_page": 1,
        "mailto": config.CONTACT_EMAIL,
    }
    response = get_with_retry(OPENALEX_WORKS, params)
    return response.json()["meta"]["count"]


if __name__ == "__main__":
    print(f"OpenAlex record counts for {terms_line5.LINE_LABEL}")
    print(f"Publication dates from {config.YEAR_MIN}-01-01 "
          f"to {config.SEARCH_CUTOFF}\n")

    total = 0
    for block in terms_line5.iter_blocks():
        count = count_openalex(block)
        total += count
        print(f"{block['subintervention_label']:<35} "
              f"{block['language']}  {count:>9,}")
        time.sleep(1.0)

    print(f"\nTotal across the 27 blocks, before deduplication: {total:,}")