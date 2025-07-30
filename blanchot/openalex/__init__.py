import re
import time
import urllib.parse
from collections import defaultdict

#import pandas as pd
import requests
from pydantic import ValidationError
from tqdm import tqdm

from .models import OpenAlexWork

def get_oa_work():
    BASE = "https://api.openalex.org/works"
    filters = "title_and_abstract.search:Blanchot,publication_year:1998-2025"
    per_page = 200
    records = []
    cursor = "*"
    invalid_works = []
    with tqdm(desc='Downloading', unit='work') as pbar:
        while True:
            encoded_filters = urllib.parse.quote(filters)
            encoded_cursor = urllib.parse.quote(cursor)

            url = f"{BASE}?filter={encoded_filters}&per_page={per_page}&cursor={encoded_cursor}"
            
            resp = requests.get(url).json()
            if pbar.total == None: 
                pbar.total = resp['meta']['count']
            works = resp['results']

            for work in works:
                try:
                    valid_work = OpenAlexWork.model_validate(work).model_dump()
                    valid_work['short_id'] = re.search(r'[A-Z]\d+', str(valid_work['id'])).group()
                    records.append(valid_work)
                except ValidationError as e:
                    invalidation_info = {
                        "work_id": work.get("id"),
                        "error": str(e)
                    }
                    invalid_works.append(invalidation_info)
            
            
            pbar.update(len(works))

            next_cursor = resp['meta'].get('next_cursor')
            if not next_cursor:
                break
            cursor = next_cursor
            time.sleep(0.1)

    if invalid_works:
        print(f"\nInvalid: {len(invalid_works)}")

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