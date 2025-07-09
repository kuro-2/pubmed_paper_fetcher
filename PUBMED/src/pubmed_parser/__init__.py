#init.py
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from Bio import Entrez
from Bio import Medline
from lxml import etree

# Replace with your actual email address.
Entrez.email = "your.email@example.com"

# Heuristics for identifying non-academic affiliations
# These are keywords that suggest a pharmaceutical or biotech company.
PHARMA_BIOTECH_KEYWORDS = [
    "pharmaceutical", "biotech", "biotechnology", "pharma", "inc.", "llc", "corp",
    "company", "laboratories", "labs", "research institute", "r&d", "drug discovery",
    "clinical research", "diagnostics", "therapeutics", "medicines", "healthcare",
    "institute", "foundation", "center" # Added 'institute', 'foundation', 'center' as they can be non-academic
]

# Keywords that typically indicate an academic institution.
ACADEMIC_KEYWORDS = [
    "university", "college", "school of", "department of", "faculty of", "academy",
    "hospital", # Hospitals can be academic or non-academic, but often associated with universities
    "medical center", # Similar to hospitals
    "clinic" # Similar to hospitals
]

def _is_non_academic_affiliation(affiliation: str) -> bool:
    """
    Determines if an affiliation string suggests a non-academic (pharmaceutical/biotech) institution.

    Args:
        affiliation (str): The affiliation string to check.

    Returns:
        bool: True if the affiliation is likely non-academic, False otherwise.
    """
    lower_affiliation = affiliation.lower()

    # Check for strong academic indicators first. If found, it's likely academic.
    if any(keyword in lower_affiliation for keyword in ACADEMIC_KEYWORDS):
        # Additional check: if it contains both academic and pharma/biotech keywords,
        # and a pharma/biotech keyword appears after an academic one,
        # it might still be a pharma/biotech entity within an academic context,
        # but for simplicity, we prioritize academic if a strong academic keyword is present.
        # This heuristic can be refined further.
        return False

    # Check for pharmaceutical/biotech keywords
    if any(keyword in lower_affiliation for keyword in PHARMA_BIOTECH_KEYWORDS):
        return True

    # Check for common corporate indicators if no strong academic keywords were found
    if re.search(r'\b(inc|llc|corp|ltd|co)\b', lower_affiliation):
        return True

    return False


def _parse_author_affiliation(author_xml: etree.Element) -> Tuple[str, Optional[str]]:
    """
    Parses author name and affiliation from an author XML element.

    Args:
        author_xml (etree.Element): The XML element for a single author.

    Returns:
        Tuple[str, Optional[str]]: A tuple containing the author's full name
                                   and their affiliation string (or None if not found).
    """
    last_name = author_xml.findtext("LastName")
    fore_name = author_xml.findtext("ForeName")
    initials = author_xml.findtext("Initials")
    collective_name = author_xml.findtext("CollectiveName")

    author_name = ""
    if collective_name:
        author_name = collective_name
    elif last_name and fore_name:
        author_name = f"{fore_name} {last_name}"
    elif last_name and initials:
        author_name = f"{initials} {last_name}"
    elif last_name:
        author_name = last_name

    affiliation_info = author_xml.find(".//AffiliationInfo/Affiliation")
    affiliation = affiliation_info.text if affiliation_info is not None else None

    return author_name, affiliation


def fetch_and_filter_pubmed_papers(
    query: str, debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetches research papers from PubMed based on a query, filters them for
    non-academic author affiliations, and extracts relevant information.

    Args:
        query (str): The PubMed query string.
        debug (bool): If True, print debug information during execution.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                              represents a filtered paper with its details.
    """
    if debug:
        print(f"Searching PubMed with query: '{query}'")

    try:
        # Step 1: Search PubMed for paper IDs
        handle = Entrez.esearch(db="pubmed", term=query, retmax="100") # Increased retmax for more results
        record = Entrez.read(handle)
        handle.close()
        id_list = record["IdList"]

        if not id_list:
            if debug:
                print("No papers found for the given query.")
            return []

        if debug:
            print(f"Found {len(id_list)} paper IDs.")

        # Step 2: Fetch detailed records for the found IDs
        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="xml")
        xml_data = handle.read()
        handle.close()

        # Parse XML using lxml for better control and error handling
        root = etree.fromstring(xml_data)

        filtered_papers: List[Dict[str, Any]] = []

        # Iterate through each PubMedArticle in the XML
        for article_elem in root.xpath("//PubmedArticle"):
            pubmed_id = article_elem.xpath(".//MedlineCitation/PMID")[0].text
            title = article_elem.xpath(".//Article/ArticleTitle")[0].text
            
            # Publication Date
            pub_date_elem = article_elem.xpath(".//Article/Journal/JournalIssue/PubDate")[0]
            year = pub_date_elem.findtext("Year")
            month = pub_date_elem.findtext("Month")
            day = pub_date_elem.findtext("Day")
            
            publication_date = ""
            if year:
                publication_date = year
                if month:
                    publication_date += f" {month}"
                    if day:
                        publication_date += f" {day}"
            
            # Authors and Affiliations
            non_academic_authors: List[str] = []
            company_affiliations: List[str] = []
            corresponding_author_email: Optional[str] = None

            has_non_academic_affiliation = False

            for author_elem in article_elem.xpath(".//AuthorList/Author"):
                author_name, affiliation = _parse_author_affiliation(author_elem)

                if affiliation and _is_non_academic_affiliation(affiliation):
                    non_academic_authors.append(author_name)
                    company_affiliations.append(affiliation)
                    has_non_academic_affiliation = True
                
                # Check for Corresponding Author Email
                # This is often found in the affiliation string or in GrantList/Grant/Agency
                # or sometimes in a separate "Author" element that has an email.
                # PubMed XML structure for email can be tricky.
                # Let's look for email patterns in the affiliation or other fields.
                # A more robust solution might involve parsing the full text if available,
                # but for API-level parsing, we're limited.
                
                # Check for email in affiliation string
                if affiliation:
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+', affiliation)
                    if email_match:
                        corresponding_author_email = email_match.group(0)
                        # Assuming the first email found is the corresponding author's for simplicity
                        # In reality, this might require more sophisticated parsing or looking at specific roles.
                        # For this problem, we'll take the first one we find.
                        break # Found email, no need to check other authors for email in this article

            if has_non_academic_affiliation:
                filtered_papers.append({
                    "PubmedID": pubmed_id,
                    "Title": title,
                    "Publication Date": publication_date,
                    "Non-academic Author(s)": "; ".join(non_academic_authors),
                    "Company Affiliation(s)": "; ".join(company_affiliations),
                    "Corresponding Author Email": corresponding_author_email if corresponding_author_email else "N/A"
                })
                if debug:
                    print(f"Added paper: {title} (ID: {pubmed_id})")

        if debug:
            print(f"Found {len(filtered_papers)} papers with non-academic affiliations.")
        return filtered_papers

    except Exception as e:
        if debug:
            print(f"An error occurred during paper fetching: {e}")
        return []


def save_papers_to_csv(papers: List[Dict[str, Any]], filename: str) -> None:
    """
    Saves a list of paper dictionaries to a CSV file.

    Args:
        papers (List[Dict[str, Any]]): A list of paper dictionaries.
        filename (str): The name of the CSV file to save to.
    """
    if not papers:
        print("No papers to save.")
        return

    # Define the CSV header based on the problem requirements
    fieldnames = [
        "PubmedID",
        "Title",
        "Publication Date",
        "Non-academic Author(s)",
        "Company Affiliation(s)",
        "Corresponding Author Email",
    ]

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(papers)
        print(f"Successfully saved {len(papers)} papers to {filename}")
    except IOError as e:
        print(f"Error saving to CSV file {filename}: {e}")