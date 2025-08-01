# Blanchot Digital Bibliography
This project provides an automated pipeline for building a comprehensive, deduplicated, and merged bibliographic dataset on the works of and about Maurice Blanchot. It collects data from three major academic sources: OpenAlex, Crossref, and HAL. The final output is a clean CSV file, suitable for research and analysis.

## Features
**Multi-Source Aggregation:** Fetches data from OpenAlex, Crossref, and HAL APIs.

**Data Standardization:** Translates disparate data formats into a single, consistent schema.

**Intelligent Deduplication:** Identifies and merges duplicate records across all sources using DOIs as the primary key.

**Automated Updates:** A GitHub Actions workflow runs the synthesis script weekly to keep the dataset current.

**Clean Output:** Produces a single data.csv file with the final, cohesive bibliography.

## Data Sources
The script pulls data from the following APIs:

- OpenAlex

- Crossref

- HAL (Hyper-Articles en Ligne)

## Project Structure
```
blanchot/
├── .github/workflows/    # GitHub Actions automation.
├── blanchot/             # Main package.
│   ├── cr/                 # Scripts/models for CR.
│   ├── hal/                # Scripts/models for HAL.
│   ├── openalex/           # Scripts/models for OA.
│   └── run_synth.py        # Main synthesis script.
├── outputs/              # data.csv save location.
├── .gitignore              
└── requirements.txt        
```

## Setup and Installation

### Clone the repository:
```bash
git clone [https://github.com/Kaiyu27/blanchot.git](https://github.com/Kaiyu27/blanchot.git)
cd blanchot
```
### Set up a Python environment (Conda):
```Bash
conda create -n blanchot python=3.13
conda activate blanchot
```

### Install dependencies:
```Bash
pip install -r requirements.txt
```

## Usage
To run the full data synthesis pipeline, execute the main script from the project's root directory:
```Bash
python blanchot/run_synth.py
```
The script will fetch data from all sources, process it, and save the final merged file to outputs/data.csv.

## Automation
This repository is configured with a GitHub Actions workflow (.github/workflows/run_synthesis.yml) that automatically runs the synthesis script once a week. It commits the updated data.csv file back to the repository, ensuring the dataset remains current.

## License
This project is licensed under the MIT License. See the LICENSE file for details.