import os
import time
import warnings
from typing import List, Optional, Dict, Any

import pandas as pd
from pydantic import BaseModel, HttpUrl, ValidationError

from hal import get_hal_work
from openalex import get_oa_work
from cr import get_cr_work

# Adopt the future behavior of pandas to avoid FutureWarnings
pd.set_option('future.no_silent_downcasting', True)
# Ignore all FutureWarnings to keep the console output clean
warnings.simplefilter(action='ignore', category=FutureWarning)

class Author(BaseModel):
    full_name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class BlanchotWork(BaseModel):
    doi: Optional[str] = None
    title: Optional[str] = None
    
    authors: List[Author] = []
    
    year: Optional[int] = None
    publication_date: Optional[str] = None
    journal_name: Optional[str] = None
    publisher: Optional[str] = None
    work_type: Optional[str] = None
    
    abstract: Optional[str] = None
    subjects: List[str] = []
    
    source_url: Optional[HttpUrl] = None
    citation_count: Optional[int] = None
    
    source_db: str
    relation: Optional[Dict[str, Any]] = None


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstructs a plain-text abstract from an OpenAlex inverted index."""
    if not inverted_index:
        return None
    
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    
    word_positions.sort()
    return ' '.join([word for pos, word in word_positions])


def from_openalex_to_blanchotwork(work_data: dict) -> dict:
    """Translates a raw OpenAlex dictionary into our standard format."""
    authors = []
    for authorship in work_data.get('authorships', []):
        if author_info := authorship.get('author'):
            authors.append(Author(full_name=author_info.get('display_name', '')))

    subjects = [concept.get('display_name') for concept in work_data.get('concepts', []) if concept]
    
    journal = None
    if primary_loc := work_data.get('primary_location'):
        if source := primary_loc.get('source'):
            journal = source.get('display_name')

    return {
        'doi': work_data.get('doi'),
        'title': work_data.get('title'),
        'authors': authors,
        'year': work_data.get('publication_year'),
        'publication_date': work_data.get('publication_date'),
        'journal_name': journal,
        'publisher': work_data.get('publisher'),
        'work_type': work_data.get('type'),
        'abstract': reconstruct_abstract(work_data.get('abstract_inverted_index')),
        'subjects': subjects,
        'citation_count': work_data.get('cited_by_count'),
        'source_url': work_data.get('id'),
        'source_db': 'OpenAlex',
        'relation': None
    }

def from_crossref_to_blanchotwork(work_data: dict) -> dict:
    """Translates a raw Crossref dictionary into our standard format."""
    authors = []
    author_list = work_data.get('author') or [] 
    for author_info in author_list:
        given = author_info.get('given', '')
        family = author_info.get('family', '')
        authors.append(Author(
            full_name=f"{given} {family}".strip(),
            given_name=given,
            family_name=family
        ))
        
    year = None
    if published := (work_data.get('published-print') or work_data.get('published-online')):
        if date_parts := published.get('date-parts', [[]]):
            if date_parts[0]: year = date_parts[0][0]

    journal_name = None
    container_title = work_data.get('container-title')
    if isinstance(container_title, list) and container_title:
        journal_name = container_title[0]

    doi = work_data.get('DOI')
    source_url = work_data.get('URL')
    if not source_url and doi:
        source_url = f"https://doi.org/{doi}"
    
    return {
        'doi': doi,
        'title': (work_data.get('title') or [None])[0],
        'authors': authors,
        'year': year,
        'publication_date': None,
        'journal_name': journal_name,
        'publisher': work_data.get('publisher'),
        'work_type': work_data.get('type'),
        'subjects': work_data.get('subject', []),
        'citation_count': work_data.get('is-referenced-by-count'),
        'source_url': source_url,
        'source_db': 'Crossref',
        'relation': work_data.get('relation')
    }

def from_hal_to_blanchotwork(work_data: dict) -> dict:
    """Translates a raw HAL dictionary into our standard format."""
    authors = [Author(full_name=name) for name in work_data.get('authFullName_s', [])]

    return {
        'doi': work_data.get('doiId_s'),
        'title': (work_data.get('title_s') or [None])[0],
        'authors': authors,
        'year': work_data.get('publicationDateY_i'),
        'publication_date': work_data.get('publicationDate_s'),
        'journal_name': work_data.get('journalTitle_s'),
        'publisher': None,
        'work_type': work_data.get('docType_s'),
        'abstract': None,
        'subjects': [],
        'citation_count': None,
        'source_url': work_data.get('uri_s'),
        'source_db': 'HAL',
        'relation': None
    }

def deduplicate_and_merge(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicates and merges records from the combined DataFrame.
    """
    print(f"\n--- Starting Deduplication & Merge ---")
    print(f"Initial record count: {len(df)}")
    
    df['doi'] = df['doi'].str.lower().str.strip().replace(r'https?://doi.org/', '', regex=True)
    df_with_doi = df[df['doi'].notna() & (df['doi'] != '')].copy()
    df_no_doi = df[df['doi'].isna() | (df['doi'] == '')].copy()
    
    print(f"Found {len(df_with_doi)} records with a DOI to merge.")
    print(f"Found {len(df_no_doi)} records without a DOI to carry over.")

    grouped = df_with_doi.groupby('doi')
    
    merged_records = []
    
    for doi, group in grouped:
        source_priority = {'OpenAlex': 0, 'Crossref': 1, 'HAL': 2}
        group['priority'] = group['source_db'].map(source_priority)
        group = group.sort_values('priority')
        
        #This may trigger a FutureWarning in older versions of pandas.
        merged_record = group.bfill().iloc[0].to_dict()

        all_subjects = set()
        for subjects_list in group['subjects'].dropna():
            if isinstance(subjects_list, list):
                all_subjects.update(subjects_list)
        merged_record['subjects'] = sorted(list(all_subjects))
        
        merged_record['source_db'] = ', '.join(sorted(group['source_db'].unique()))
        merged_record['citation_count'] = group['citation_count'].max()
        best_author_list = max(group['authors'], key=len, default=[])
        merged_record['authors'] = best_author_list

        merged_records.append(merged_record)

    df_merged = pd.DataFrame(merged_records)
    
    df_final = pd.concat([df_merged, df_no_doi], ignore_index=True)
    
    if 'priority' in df_final.columns:
        df_final = df_final.drop(columns=['priority'])
        
    print(f"Merge complete. Final unique record count: {len(df_final)}")
    return df_final

def main():
    """
    Main function to fetch data from all sources, translate it,
    combine it, and save it to a CSV file.
    """
    print("--- Starting Data Synthesis ---")
    
    print("Fetching data from OpenAlex...")
    oa_data = [from_openalex_to_blanchotwork(work) for work in get_oa_work()]
    
    print("\nFetching data from HAL...")
    hal_data = [from_hal_to_blanchotwork(work) for work in get_hal_work()]
    
    print("\nFetching data from Crossref...")
    cr_data = [from_crossref_to_blanchotwork(work) for work in get_cr_work()]
    
    print("\n--- Combining Data ---")
    df_initial = pd.DataFrame(oa_data + hal_data + cr_data)
    
    df_final = deduplicate_and_merge(df_initial)
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs', 'data.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_final.to_csv(output_path, index=False)
    
    print(f"\n--- Process Complete ---")
    print(f"Successfully saved {len(df_final)} unique records to {output_path}")

if __name__ == '__main__':
    main()