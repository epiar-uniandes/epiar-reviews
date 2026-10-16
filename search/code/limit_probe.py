"""Throwaway probe. Compares the two ways of searching titles and abstracts.

OpenAlex charges 10 credits for a search and 1 credit for a filtered list.
The same query can be written either way. This prints what the server says
it charged and how many records it reports for each, so that the cheaper
form is adopted only if it returns the same set.
"""

import requests

import config

QUERY = '"school feeding" OR "school meals" OR "take-home ration"'
DATES = (f"from_publication_date:{config.YEAR_MIN}-01-01,"
         f"to_publication_date:{config.SEARCH_CUTOFF}")

FORMS = {
    "search parameter": {
        "search.title_and_abstract": QUERY,
        "filter": DATES,
    },
    "filter form": {
        "filter": f"title_and_abstract.search:{QUERY},{DATES}",
    },
}
def remaining(response):
    """Prepaid balance the server reports after serving this request."""
    return response.headers.get("X-RateLimit-Prepaid-Remaining-USD")


for name, params in FORMS.items():
    full = dict(params, per_page=1, api_key=config.openalex_api_key())
    response = requests.get("https://api.openalex.org/works",
                            params=full, timeout=60)
    print(f"\n{name}")
    print("  status    ", response.status_code)
    print("  records   ", response.json()["meta"]["count"])
    print("  headers the server sent about the budget:")
    for header, value in response.headers.items():
        if header.lower().startswith("x-ratelimit"):
            print(f"    {header}: {value}")
