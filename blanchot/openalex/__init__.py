import re
import time
import urllib.parse
from collections import defaultdict

import requests
from pydantic import ValidationError
from tqdm import tqdm

from .models import OpenAlexWork

def get_oa_work():
    BASE_URL = "https://api.openalex.org/works"
    records = []
    invalid_works = []
    
    current_year = time.localtime().tm_year
    filters = f"title_and_abstract.search:Blanchot,publication_year:1998-{current_year}"
    per_page = 200
    cursor = "*"

    with tqdm(desc='Downloading', unit='work') as pbar:
        while True:
            encoded_filters = urllib.parse.quote(filters)
            encoded_cursor = urllib.parse.quote(cursor)
            url = f"{BASE_URL}?filter={encoded_filters}&per_page={per_page}&cursor={encoded_cursor}"
            
            try:
                resp = requests.get(url).json()

                if 'error' in resp:
                    print(f"\n--- OpenAlex API Error ---")
                    print(f"Error: {resp.get('error')}")
                    print(f"Message: {resp.get('message', 'No message provided.')}")
                    break

                if pbar.total is None: 
                    pbar.total = resp.get('meta', {}).get('count', 0)
                
                works = resp.get('results', [])
                if not works:
                    break

                for work in works:
                    try:
                        valid_work = OpenAlexWork.model_validate(work).model_dump()
                        valid_work['short_id'] = re.search(r'[A-Z]\d+', str(valid_work['id'])).group()
                        records.append(valid_work)
                    except ValidationError as e:
                        invalid_works.append({
                            "work_id": work.get("id"),
                            "error": str(e)
                        })
                    except AttributeError:
                        invalid_works.append({
                            "work_id": work.get("id", "N/A"),
                            "error": "Could not parse short_id from work ID."
                        })
                
                pbar.update(len(works))
                
                next_cursor = resp.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"\nA network error occurred: {e}")
                break

    if invalid_works:
        print(f"\nSkipped {len(invalid_works)} invalid records.")

    original_count = len(records)
    print(f"\nDownloaded: {original_count}")

    grouped_records = defaultdict(list)
    for record in records:
        record_id = record['short_id']
        grouped_records[record_id].append(record)

    records = [works_list[0] for works_list in grouped_records.values()]
    final_count = len(records)

    print(f"Duplicates removed: {original_count - final_count}")

    return records