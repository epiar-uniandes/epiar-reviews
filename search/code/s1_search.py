"""Step 1 of the search pipeline. First version, OpenAlex only.

This version saves nothing. It sends one query to OpenAlex and prints what
it sent and what came back, so that the query can be checked against the
registration before the full search is run.
"""

import requests

import config
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


if __name__ == "__main__":
    blocks = list(terms_line5.iter_blocks())
    first = blocks[0]
    print(f"{first['subintervention_label']}, {first['language']}, "
          f"{len(first['terms'])} phrases\n")
    probe(first)