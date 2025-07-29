# blanchot
Blanchot Bibliographic Masterlist
An open-source project to create a comprehensive, clean, and automatically updating bibliographic masterlist of scholarly works related to the philosopher and writer Maurice Blanchot.

# Description
This project synthesizes data from multiple major academic APIs (OpenAlex, Crossref, and HAL) to create a single, de-duplicated, and validated list of secondary literature. The data is processed using a Python script that includes intelligent chapter consolidation, relevance scoring, and historical enrichment via citation chasing to produce a high-quality dataset for researchers.

The final masterlist is automatically updated weekly using a GitHub Action to ensure it remains current with the latest publications.

# Features
Multi-Source Synthesis: Aggregates data from OpenAlex, Crossref, and HAL.

Data Validation: Uses Pydantic to ensure the integrity and structure of the collected data.

Intelligent Consolidation: Groups individual book chapters into single book entries using "parent DOI" relationships and title matching.

De-duplication: Uses DOIs and title/year matching to ensure the final list contains only unique works.

Automated Weekly Updates: A GitHub Action runs the synthesis script every week to find new publications and commits the updated list back to the repository.

Historical Enrichment: A "citation chasing" script uses recent works to find and add older, foundational literature that may be underrepresented in modern indexes.

# How to Use
To run this project locally, follow these steps:

Clone the repository:

git clone https://github.com/[your-username]/[your-repo-name].git
cd [your-repo-name]

Install dependencies:
It is recommended to use a virtual environment.

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Set up API Keys (if required):

The scripts are configured to pull API keys from environment variables or GitHub Secrets. For local runs, you may need to set these up. For example, for the weekly update script:

export YOUR_EMAIL="your_email@example.com"

Run the scripts:

To generate the initial master list from local JSON files, run the main synthesis script:

python [your_synthesis_script_name.py]

To enrich the list with historical data, run the citation chasing script:

python [your_citation_chasing_script_name.py]

# Output Data
The primary output of this project is the blanchot_master_list.json file. This file contains a list of unique, consolidated works. Each work is a JSON object with the following standardized structure:

doi: The Digital Object Identifier (string, optional).

title: The title of the work (string).

authors: A list of author objects, each containing a full_name (string).

year: The publication year (integer, optional).

publication_date: The full publication date (string, optional).

journal_name: The name of the journal or container publication (string, optional).

publisher: The publisher of the work (string, optional).

work_type: The type of work, e.g., "article", "book-chapter" (string, optional).

subjects: A list of subject keywords (list of strings).

source_url: A direct link to the record in its original database (string).

source_db: The database the record was sourced from (e.g., 'OpenAlex', 'Crossref').

citation_count: The number of known citations (integer, optional).

# License
This project is licensed under the MIT License. See the LICENSE file for details.
