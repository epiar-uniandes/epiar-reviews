"""Throwaway probe. Checks which fields the ERIC search parameter covers.

The registration states that the search parameter covers title, abstract,
descriptors and identifiers. If the bare quoted search returns about the
same count as a title-only search, that claim is false and the field
coverage has to be stated differently.
"""

import time

import requests

ERIC = "https://api.ies.ed.gov/eric/"

QUERIES = [
    '"school feeding"',
    'title:"school feeding"',
    'description:"school feeding"',
    'subject:"school feeding"',
]

for query in QUERIES:
    params = {"search": query, "format": "json", "rows": 1, "fields": "title"}
    response = requests.get(ERIC, params=params, timeout=60)
    found = response.json().get("response", {}).get("numFound")
    print(f"{query:35s} {found}")
    time.sleep(1)