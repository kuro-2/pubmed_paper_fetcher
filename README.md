# PubMed Paper Fetcher

A Python program to fetch research papers from PubMed, identify papers with at least one author affiliated with a pharmaceutical or biotech company, and return the results as a CSV file or print them to the console.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Code Organization](#code-organization)
- [Installation](#installation)
- [Usage](#usage)
- [Heuristics for Non-academic Authors](#heuristics-for-non-academic-authors)
- [Tools Used](#tools-used)
- [Evaluation Criteria Addressed](#evaluation-criteria-addressed)
- [Link to pubmed_parser package in test_pypi](#link-to-pubmed_parser-package-in-test_pypi)
- [License](#license)

---

## Project Overview

The core task is to interact with the PubMed API, filter papers based on specific author affiliations (pharmaceutical/biotech companies), and present the data in a structured CSV format.

---

## Features

- Fetches papers using the PubMed API with full query syntax support.
- Filters papers to include only those with at least one author affiliated with a pharmaceutical or biotech company.
- Outputs results to a CSV file with columns: PubmedID, Title, Publication Date, Non-academic Author(s), Company Affiliation(s), Corresponding Author Email.
- Command-line interface with options for:
  - Specifying the PubMed query.
  - Saving output to a file (`-f` or `--file`).
  - Enabling debug mode (`-d` or `--debug`).
  - Displaying usage instructions (`-h` or `--help`).
  - Showing program version (`-v` or `--version`).

---

## Code Organization

```
pubmed_paper_fetcher/
├── pyproject.toml
├── README.md
├── poetry.lock
└── src/
    └── pubmed_parser/
        ├── __init__.py  # Core logic for PubMed API interaction, parsing, and filtering
        └── cli.py       # Command-line interface (CLI) entry point
```

- **src/pubmed_parser/__init__.py**: Contains the main logic for interacting with the PubMed API, parsing results, filtering by affiliation, and saving to CSV.
- **src/pubmed_parser/cli.py**: Implements the command-line interface using `argparse`, calling functions from `__init__.py` based on user input.

---

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/kuro-2/pubmed_paper_fetcher.git
   cd pubmed_paper_fetcher
   ```

2. **Install Poetry (if not already installed):**
   ```sh
   pip install poetry
   ```

3. **Install dependencies:**
   ```sh
   poetry install
   ```

4. **Set your Entrez email:**
   - Open `src/pubmed_parser/__init__.py`
   - Replace `"your.email@example.example"` with your actual email address:
     ```python
     Entrez.email = "your.actual.email@example.com"
     ```

---

## Usage

After installation, use the CLI tool provided by Poetry.

**Basic Usage:**  
Search for papers and print results to the console:
```sh
poetry run get-papers-list "CRISPR gene editing"
```

**Save results to a CSV file:**  
```sh
poetry run get-papers-list "CRISPR gene editing" --file crispr_papers.csv
```

**Enable debug mode:**  
```sh
poetry run get-papers-list "COVID-19 vaccine" --debug
```

**Combined options:**  
```sh
poetry run get-papers-list "Alzheimer's disease therapeutics" -f alzheimers.csv -d
```

**Display help:**  
```sh
poetry run get-papers-list --help
```

**Display version:**  
```sh
poetry run get-papers-list --version
```

---

## Heuristics for Non-academic Authors

The program identifies non-academic author affiliations using a set of keywords. It checks for pharmaceutical/biotech company indicators (e.g., "pharmaceutical", "biotech", "inc.") and excludes strong academic indicators (e.g., "university", "school of").

- The keywords are defined in `src/pubmed_parser/__init__.py`:
  - `PHARMA_BIOTECH_KEYWORDS`
  - `ACADEMIC_KEYWORDS`

These heuristics can be refined for higher accuracy.

---

## Tools Used

- **Python 3.12+**: Programming language.
- **Poetry**: Dependency management and packaging.
- **Biopython (Bio.Entrez)**: PubMed API interaction.
- **lxml**: Efficient XML parsing.
- **argparse**: Command-line argument parsing.
- **Git/GitHub**: Version control and code hosting.
- **LLM:** ChatGPT

---

## Evaluation Criteria Addressed

- **Functional Requirements**
  - Fetches papers, filters by non-academic affiliations, outputs to CSV/console.
  - Uses Bio.Entrez and custom heuristics for filtering.
- **Non-functional Requirements**
  - Typed Python for readability and maintainability.
  - Efficient API calls and XML parsing.
  - Clear, maintainable code with comments and docstrings.
  - Logical separation into a module and CLI.
  - Basic error handling for API failures and missing data.
- **Bonus**
  - Modular design: `pubmed_parser` module and `cli.py` CLI.

---

## Link to pubmed_parser package in test_pypi
```sh
https://test.pypi.org/project/pubmed-parser/
```
---

## License

No license has been selected for this project. All rights reserved.

---
