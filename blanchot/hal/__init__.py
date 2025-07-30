import requests, time
from collections import defaultdict

from tqdm import tqdm
from pydantic import ValidationError

from .models import HALWorkModel


BASE_URL = "https://api.archives-ouvertes.fr/search/"
SEARCH_TERM = "Blanchot"
START_YEAR = 1998
ROWS_PER_PAGE = 100
OUTPUT_JSON_FILE = "hal_blanchot_data.json"

def get_hal_work():
    validated_works = []
    failed_works_log = []
    start = 0
    num_found = 0

    print("Querying HAL API to get total number of results...")
    specific_query = f'(title_t:"{SEARCH_TERM}" OR abstract_t:"{SEARCH_TERM}")'
    initial_params = {'q': specific_query, 'fq': f'publicationDateY_i:[{START_YEAR} TO *]', 'rows': 0}
    try:
        initial_resp = requests.get(BASE_URL, params=initial_params).json()
        num_found = initial_resp.get('response', {}).get('numFound', 0)
        print(f"Found {num_found} total works to download.")
    except requests.exceptions.RequestException as e:
        print(f"Initial API request failed: {e}")
        num_found = 0

    if num_found > 0:
        with tqdm(total=num_found, desc="Downloading works from HAL") as pbar:
            while start < num_found:
                params = {
                    'q': f'(title_t:"{SEARCH_TERM}" OR abstract_t:"{SEARCH_TERM}")',
                    'fq': f'publicationDateY_i:[{START_YEAR} TO *]',
                    'fl': 'title_s, authFullName_s, publicationDateY_i, journalTitle_s, uri_s, docType_s, docid',
                    'wt': 'json',
                    'rows': ROWS_PER_PAGE,
                    'start': start,
                    'sort': 'docid asc'
                }
                try:
                    response = requests.get(BASE_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    docs = data.get('response', {}).get('docs', [])
                    if not docs: break
                    for doc_data in docs:
                        try:
                            validated_work = HALWorkModel.model_validate(doc_data)
                            validated_works.append(validated_work.model_dump())
                        except ValidationError as e:
                            failed_works_log.append({"uri": doc_data.get("uri_s"), "error_details": e.errors()})
                    pbar.update(len(docs))
                    start += ROWS_PER_PAGE
                    time.sleep(0.1)
                except requests.exceptions.RequestException as e:
                    print(f"\nAn error occurred during download: {e}"); break
    
    original_count = len(validated_works)
    print(f"\nPerforming deduplication on {original_count} records...")

    grouped_by_docid = defaultdict(list)
    for work in validated_works:
        grouped_by_docid[work['docid']].append(work)

    validated_works = [works_list[0] for works_list in grouped_by_docid.values()]
    final_count = len(validated_works)

    print(f"Removed {original_count - final_count} duplicate records.")

    return validated_works