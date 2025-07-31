from crossref.restful import Works
import pandas as pd
from pydantic import ValidationError
from tqdm import tqdm

from .models import CrossrefWorkModel

works_api = Works()

works_query = works_api.query(bibliographic='Blanchot').filter(
    from_pub_date='1998'
).sort('published').order('asc')

def get_cr_work():
    validated_records = []
    failed_records = []

    try:
        for work_data in tqdm(works_query, total=works_query.count(), desc="Downloading"):
            try:
                validated_work = CrossrefWorkModel.model_validate(work_data)
                validated_records.append(validated_work)
            except ValidationError as e:
                failed_records.append({'doi': work_data.get('DOI'), 'error': str(e)})
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")


    print(f"\nDownload complete.")
    print(f"Total validated records: {len(validated_records)}")
    if failed_records:
        print(f"Total records that failed validation: {len(failed_records)}")


    original_count = len(validated_records)
    unique_records_builder = []
    seen_dois = set()
    duplicate_log = []

    for work in validated_records:
        doi = work.DOI

        if doi not in seen_dois:
            unique_records_builder.append(work)
            seen_dois.add(doi)
        else:
            duplicate_log.append({
                "DOI": doi,
                "title": work.title[0] if work.title else "No Title"
            })

    validated_records = unique_records_builder
    final_count = len(validated_records)

    print(f"Unique records: {final_count}")
    print(f"Duplicates removed: {original_count - final_count}")


    df = pd.DataFrame([work.model_dump(by_alias=True) for work in validated_records])
    print(f"\nCreated DataFrame with {len(df)} records for filtering.")

    if 'publisher' in df.columns:
        # TODO:EXPAND LIST -- EXPANDED BELOW
        academic_keywords = [
            # --- Core Disciplines & Theories ---
            'Philosophy', 'Philosophie', 'Filosofia', 'Filosofía',
            'Literature', 'Literary', 'Linguistics', 'Poetics',
            'Humanities', 'Theory', 'Critical', 'Deconstruction',
            'Phenomenology', 'Psychoanalysis', 'Aesthetics', 'Cultural Studies',
            
            # --- Institutional & Publisher Types ---
            'University Press', 'University', 'Press', 'Academic',
            'College', 'Institute', 'Institut', 'Centro', 'Centre',
            'Society', 'Société', 'Sociedad',
            
            # --- Publication Types (English) ---
            'Journal', 'Review', 'Studies', 'Quarterly', 'Annual', 'Annals',
            'Proceedings', 'Transactions', 'Bulletin', 'Archive', 'Yearbook',
            
            # --- Publication Types (Foreign Languages) ---
            # French
            'Revue', 'Cahiers', 'Études', 'Annales', 'Presses',
            # German
            'Zeitschrift', 'Kritik', 'Jahrbuch', 'Archiv', 'Verlag',
            # Italian
            'Rivista', 'Studi', 'Annali',
            # Spanish / Portuguese
            'Revista', 'Estudios', 'Anales',
            # Latin
            'Acta'
        ]
        
        search_pattern = '|'.join(academic_keywords)
        
        df_filtered = df[df['publisher'].str.contains(search_pattern, case=False, na=False)]
        return df_filtered.to_dict('records')
        
    else:
        print("\nWarning: 'publisher' column not found in the downloaded data. Cannot perform filtering.")
        return None