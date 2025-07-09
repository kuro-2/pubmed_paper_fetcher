import pytest
import csv
from unittest.mock import patch, MagicMock
from io import StringIO
import os

# Import functions from your module
from pubmed_parser import (
    _is_non_academic_affiliation,
    _parse_author_affiliation,
    fetch_and_filter_pubmed_papers,
    save_papers_to_csv,
    PHARMA_BIOTECH_KEYWORDS, # Import for testing heuristics
    ACADEMIC_KEYWORDS # Import for testing heuristics
)
from lxml import etree # Needed to create mock XML elements

# --- Test _is_non_academic_affiliation function ---
def test_is_non_academic_affiliation_pharma_biotech():
    """Test cases for affiliations that should be identified as non-academic."""
    assert _is_non_academic_affiliation("Pfizer Inc.") is True
    assert _is_non_academic_affiliation("Genentech, Inc.") is True
    assert _is_non_academic_affiliation("Novartis Pharmaceuticals") is True
    assert _is_non_academic_affiliation("Biotechnology Research Labs") is True
    assert _is_non_academic_affiliation("AbbVie Corporation") is True
    assert _is_non_academic_affiliation("Janssen Global Services, LLC") is True
    assert _is_non_academic_affiliation("Roche Diagnostics") is True
    assert _is_non_academic_affiliation("AstraZeneca R&D") is True
    assert _is_non_academic_affiliation("Merck Sharp & Dohme Corp.") is True
    assert _is_non_academic_affiliation("Clinical Research Organization") is True
    assert _is_non_academic_affiliation("Global Health Institute") is True
    assert _is_non_academic_affiliation("Gates Foundation") is True
    assert _is_non_academic_affiliation("Innovation Center") is True


def test_is_non_academic_affiliation_academic():
    """Test cases for affiliations that should be identified as academic."""
    assert _is_non_academic_affiliation("Harvard University") is False
    assert _is_non_academic_affiliation("University of California, Berkeley") is False
    assert _is_non_academic_affiliation("School of Medicine, Stanford") is False
    assert _is_non_academic_affiliation("Department of Biology, MIT") is False
    assert _is_non_academic_affiliation("Massachusetts General Hospital") is False
    assert _is_non_academic_affiliation("Mayo Clinic") is False
    assert _is_non_academic_affiliation("Academic Medical Center") is False


def test_is_non_academic_affiliation_mixed_or_ambiguous():
    """Test cases for affiliations that might be mixed or ambiguous."""
    # Prioritizes academic if strong academic keyword is present
    assert _is_non_academic_affiliation("University of Cambridge, Pharma Department") is False
    assert _is_non_academic_affiliation("Hospital for Special Surgery, Biotech Division") is False
    assert _is_non_academic_affiliation("Academic Research Lab Inc.") is False
    assert _is_non_academic_affiliation("Smithsonian Institute") is False
    assert _is_non_academic_affiliation("Local Community College") is False
    assert _is_non_academic_affiliation("Independent Consultant") is False
    assert _is_non_academic_affiliation("Government Agency") is False


# --- Test _parse_author_affiliation function ---
def test_parse_author_affiliation_full_name_and_affiliation():
    """Test parsing author with full name and affiliation."""
    author_xml = etree.fromstring("""
    <Author>
        <LastName>Doe</LastName>
        <ForeName>John</ForeName>
        <Initials>JD</Initials>
        <AffiliationInfo>
            <Affiliation>University of ABC, Dept. of Science</Affiliation>
        </AffiliationInfo>
    </Author>
    """)
    name, affiliation = _parse_author_affiliation(author_xml)
    assert name == "John Doe"
    assert affiliation == "University of ABC, Dept. of Science"

def test_parse_author_affiliation_no_affiliation():
    """Test parsing author with full name but no affiliation."""
    author_xml = etree.fromstring("""
    <Author>
        <LastName>Smith</LastName>
        <ForeName>Jane</ForeName>
        <Initials>JS</Initials>
    </Author>
    """)
    name, affiliation = _parse_author_affiliation(author_xml)
    assert name == "Jane Smith"
    assert affiliation is None

def test_parse_author_affiliation_collective_name():
    """Test parsing author with a collective name."""
    author_xml = etree.fromstring("""
    <Author>
        <CollectiveName>The COVID-19 Study Group</CollectiveName>
    </Author>
    """)
    name, affiliation = _parse_author_affiliation(author_xml)
    assert name == "The COVID-19 Study Group"
    assert affiliation is None

def test_parse_author_affiliation_last_name_only():
    """Test parsing author with only a last name."""
    author_xml = etree.fromstring("""
    <Author>
        <LastName>Bloggs</LastName>
    </Author>
    """)
    name, affiliation = _parse_author_affiliation(author_xml)
    assert name == "Bloggs"
    assert affiliation is None

def test_parse_author_affiliation_with_email_in_affiliation():
    """Test parsing author affiliation that contains an email address."""
    author_xml = etree.fromstring("""
    <Author>
        <LastName>Emailer</LastName>
        <ForeName>Erica</ForeName>
        <AffiliationInfo>
            <Affiliation>PharmaCo, Inc. erica.emailer@pharmaco.com</Affiliation>
        </AffiliationInfo>
    </Author>
    """)
    name, affiliation = _parse_author_affiliation(author_xml)
    assert name == "Erica Emailer"
    assert affiliation == "PharmaCo, Inc. erica.emailer@pharmaco.com"


# --- Test fetch_and_filter_pubmed_papers function ---

# Mock XML response for Entrez.efetch
# Removed DOCTYPE declaration to prevent lxml parsing errors in tests
MOCK_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
<PubmedArticle>
    <MedlineCitation Owner="NLM" Status="MEDLINE">
        <PMID Version="1">12345678</PMID>
        <Article PubModel="Print">
            <ArticleTitle>A study on CRISPR gene editing in academic settings</ArticleTitle>
            <Journal>
                <JournalIssue>
                    <PubDate>
                        <Year>2023</Year>
                        <Month>Jan</Month>
                        <Day>15</Day>
                    </PubDate>
                </JournalIssue>
            </Journal>
            <AuthorList CompleteYN="Y">
                <Author ValidYN="Y">
                    <LastName>Smith</LastName>
                    <ForeName>A</ForeName>
                    <AffiliationInfo>
                        <Affiliation>University of Academia, Dept. of Research.</Affiliation>
                    </AffiliationInfo>
                </Author>
            </AuthorList>
        </Article>
    </MedlineCitation>
</PubmedArticle>
<PubmedArticle>
    <MedlineCitation Owner="NLM" Status="MEDLINE">
        <PMID Version="1">87654321</PMID>
        <Article PubModel="Print">
            <ArticleTitle>Novel therapeutics from BiotechCorp for cancer</ArticleTitle>
            <Journal>
                <JournalIssue>
                    <PubDate>
                        <Year>2024</Year>
                        <Month>Feb</Month>
                        <Day>20</Day>
                    </PubDate>
                </JournalIssue>
            </Journal>
            <AuthorList CompleteYN="Y">
                <Author ValidYN="Y">
                    <LastName>Jones</LastName>
                    <ForeName>B</ForeName>
                    <AffiliationInfo>
                        <Affiliation>BiotechCorp, Inc., Innovation Division. b.jones@biotechcorp.com</Affiliation>
                    </AffiliationInfo>
                </Author>
                <Author ValidYN="Y">
                    <LastName>Williams</LastName>
                    <ForeName>C</ForeName>
                    <AffiliationInfo>
                        <Affiliation>Academic Medical Center.</Affiliation>
                    </AffiliationInfo>
                </Author>
            </AuthorList>
        </Article>
    </MedlineCitation>
</PubmedArticle>
<PubmedArticle>
    <MedlineCitation Owner="NLM" Status="MEDLINE">
        <PMID Version="1">11223344</PMID>
        <Article PubModel="Print">
            <ArticleTitle>Drug discovery in PharmaLabs</ArticleTitle>
            <Journal>
                <JournalIssue>
                    <PubDate>
                        <Year>2023</Year>
                        <Month>Mar</Month>
                        <Day>10</Day>
                    </PubDate>
                </JournalIssue>
            </Journal>
            <AuthorList CompleteYN="Y">
                <Author ValidYN="Y">
                    <LastName>Brown</LastName>
                    <ForeName>D</ForeName>
                    <AffiliationInfo>
                        <Affiliation>PharmaLabs, Ltd. d.brown@pharmalabs.co.uk</Affiliation>
                    </AffiliationInfo>
                </Author>
            </AuthorList>
        </Article>
    </MedlineCitation>
</PubmedArticle>
<PubmedArticle>
    <MedlineCitation Owner="NLM" Status="MEDLINE">
        <PMID Version="1">99887766</PMID>
        <Article PubModel="Print">
            <ArticleTitle>Another academic paper</ArticleTitle>
            <Journal>
                <JournalIssue>
                    <PubDate>
                        <Year>2022</Year>
                        <Month>Dec</Month>
                        <Day>01</Day>
                    </PubDate>
                </JournalIssue>
            </Journal>
            <AuthorList CompleteYN="Y">
                <Author ValidYN="Y">
                    <LastName>Clark</LastName>
                    <ForeName>E</ForeName>
                    <AffiliationInfo>
                        <Affiliation>Another University.</Affiliation>
                    </AffiliationInfo>
                </Author>
            </AuthorList>
        </Article>
    </MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>
"""

@patch('Bio.Entrez.esearch')
@patch('Bio.Entrez.efetch')
def test_fetch_and_filter_pubmed_papers_success(mock_efetch, mock_esearch):
    """
    Test successful fetching and filtering of papers.
    Mocks Entrez.esearch to return a list of IDs and Entrez.efetch to return mock XML.
    """
    # Mock esearch to return IDs
    mock_esearch.return_value = MagicMock(
        read=lambda: {'IdList': ['12345678', '87654321', '11223344', '99887766']},
        close=lambda: None
    )

    # Mock efetch to return the XML data
    mock_efetch.return_value = MagicMock(
        read=lambda: MOCK_EFETCH_XML,
        close=lambda: None
    )

    query = "test query"
    papers = fetch_and_filter_pubmed_papers(query, debug=True) # Set debug to True for verbose test output

    assert len(papers) == 2 # Expecting 2 papers with non-academic affiliations
    assert papers[0]["PubmedID"] == "87654321"
    assert papers[0]["Title"] == "Novel therapeutics from BiotechCorp for cancer"
    assert papers[0]["Non-academic Author(s)"] == "B Jones"
    assert papers[0]["Company Affiliation(s)"] == "BiotechCorp, Inc., Innovation Division. b.jones@biotechcorp.com"
    assert papers[0]["Corresponding Author Email"] == "b.jones@biotechcorp.com"

    assert papers[1]["PubmedID"] == "11223344"
    assert papers[1]["Title"] == "Drug discovery in PharmaLabs"
    assert papers[1]["Non-academic Author(s)"] == "D Brown"
    assert papers[1]["Company Affiliation(s)"] == "PharmaLabs, Ltd. d.brown@pharmalabs.co.uk"
    assert papers[1]["Corresponding Author Email"] == "d.brown@pharmalabs.co.uk"

    # Verify that Entrez functions were called
    mock_esearch.assert_called_once_with(db="pubmed", term=query, retmax="10000")
    mock_efetch.assert_called_once_with(db="pubmed", id=['12345678', '87654321', '11223344', '99887766'], rettype="medline", retmode="xml")


@patch('Bio.Entrez.esearch')
def test_fetch_and_filter_pubmed_papers_no_results(mock_esearch):
    """Test case when esearch returns no IDs."""
    mock_esearch.return_value = MagicMock(
        read=lambda: {'IdList': []},
        close=lambda: None
    )

    papers = fetch_and_filter_pubmed_papers("no existing query")
    assert len(papers) == 0
    mock_esearch.assert_called_once() # Ensure esearch was called


@patch('Bio.Entrez.esearch')
@patch('Bio.Entrez.efetch')
def test_fetch_and_filter_pubmed_papers_api_error(mock_efetch, mock_esearch):
    """Test case when an API call (e.g., efetch) raises an exception.)"""
    mock_esearch.return_value = MagicMock(
        read=lambda: {'IdList': ['123']},
        close=lambda: None
    )
    # The side_effect will now be triggered correctly after XML parsing fix
    mock_efetch.side_effect = Exception("Simulated API error")

    papers = fetch_and_filter_pubmed_papers("query with error", debug=True)
    assert len(papers) == 0
    mock_esearch.assert_called_once()
    mock_efetch.assert_called_once()


# --- Test save_papers_to_csv function ---
def test_save_papers_to_csv_success(tmp_path):
    """Test successful saving of papers to a CSV file."""
    test_papers = [
        {
            "PubmedID": "1",
            "Title": "Paper One",
            "Publication Date": "2023 Jan",
            "Non-academic Author(s)": "A. Author",
            "Company Affiliation(s)": "Company A",
            "Corresponding Author Email": "a.author@company.com"
        },
        {
            "PubmedID": "2",
            "Title": "Paper Two",
            "Publication Date": "2024 Feb 10",
            "Non-academic Author(s)": "B. Author",
            "Company Affiliation(s)": "Company B",
            "Corresponding Author Email": "N/A"
        }
    ]
    
    # Use tmp_path fixture provided by pytest for temporary file creation
    output_file = tmp_path / "test_output.csv"
    save_papers_to_csv(test_papers, str(output_file))

    assert output_file.exists()
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert header == [
        "PubmedID",
        "Title",
        "Publication Date",
        "Non-academic Author(s)",
        "Company Affiliation(s)",
        "Corresponding Author Email",
    ]
    assert len(rows) == 2
    assert rows[0] == ["1", "Paper One", "2023 Jan", "A. Author", "Company A", "a.author@company.com"]
    assert rows[1] == ["2", "Paper Two", "2024 Feb 10", "B. Author", "Company B", "N/A"]

def test_save_papers_to_csv_no_papers(capfd, tmp_path):
    """Test saving an empty list of papers."""
    output_file = tmp_path / "empty_output.csv"
    save_papers_to_csv([], str(output_file))

    assert not output_file.exists() # File should not be created for empty list
    
    # Check if "No papers to save." was printed
    out, err = capfd.readouterr()
    assert "No papers to save." in out

def test_save_papers_to_csv_io_error(capfd):
    """Test handling of an IOError during CSV saving."""
    test_papers = [{"PubmedID": "1", "Title": "Test", "Publication Date": "2023", "Non-academic Author(s)": "A", "Company Affiliation(s)": "C", "Corresponding Author Email": "E"}]
    
    # Mock open to raise an IOError
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        save_papers_to_csv(test_papers, "/nonexistent/path/error.csv")
        out, err = capfd.readouterr()
        assert "Error saving to CSV file" in out
        assert "Permission denied" in out

