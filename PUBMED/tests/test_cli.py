import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os

# Import the main function from your cli module
from pubmed_parser.cli import main

# Mock the core functions that cli.py calls
@patch('pubmed_parser.fetch_and_filter_pubmed_papers')
@patch('pubmed_parser.save_papers_to_csv')
def test_cli_output_to_console(mock_save_papers, mock_fetch_papers, capsys):
    """
    Test CLI when output is directed to console (no --file option).
    """
    # Mock the return value of fetch_and_filter_pubmed_papers
    mock_fetch_papers.return_value = [
        {
            "PubmedID": "123",
            "Title": "Test Paper 1",
            "Publication Date": "2023 Jan",
            "Non-academic Author(s)": "Author A",
            "Company Affiliation(s)": "Company X",
            "Corresponding Author Email": "a@example.com"
        }
    ]

    # Mock sys.argv to simulate command-line arguments
    test_args = ["get-papers-list", "test query"]
    with patch.object(sys, 'argv', test_args):
        main() # Call the main function of your CLI

    # Capture stdout
    captured = capsys.readouterr()

    # Assertions
    assert "--- Filtered Papers ---" in captured.out
    assert "PubmedID: 123" in captured.out
    assert "Title: Test Paper 1" in captured.out
    assert "Author A" in captured.out
    assert "Company X" in captured.out
    assert "a@example.com" in captured.out
    mock_fetch_papers.assert_called_once_with("test query", debug=False)
    mock_save_papers.assert_not_called() # save_papers_to_csv should not be called

@patch('pubmed_parser.fetch_and_filter_pubmed_papers')
@patch('pubmed_parser.save_papers_to_csv')
def test_cli_output_to_file(mock_save_papers, mock_fetch_papers, tmp_path):
    """
    Test CLI when output is directed to a file (--file option).
    """
    # Mock the return value of fetch_and_filter_pubmed_papers
    mock_fetch_papers.return_value = [
        {
            "PubmedID": "456",
            "Title": "Test Paper 2",
            "Publication Date": "2024 Feb",
            "Non-academic Author(s)": "Author B",
            "Company Affiliation(s)": "Company Y",
            "Corresponding Author Email": "b@example.com"
        }
    ]

    output_filename = tmp_path / "output.csv" # Use pytest's tmp_path for temporary files
    test_args = ["get-papers-list", "another query", "--file", str(output_filename)]
    with patch.object(sys, 'argv', test_args):
        main()

    mock_fetch_papers.assert_called_once_with("another query", debug=False)
    mock_save_papers.assert_called_once_with(mock_fetch_papers.return_value, str(output_filename))

@patch('pubmed_parser.fetch_and_filter_pubmed_papers')
@patch('pubmed_parser.save_papers_to_csv')
def test_cli_debug_mode(mock_save_papers, mock_fetch_papers, capsys):
    """
    Test CLI in debug mode.
    """
    mock_fetch_papers.return_value = [] # No papers for simplicity in debug test
    
    test_args = ["get-papers-list", "debug query", "-d"]
    with patch.object(sys, 'argv', test_args):
        main()
    
    captured = capsys.readouterr()
    assert "Debug mode enabled." in captured.out
    # fetch_and_filter_pubmed_papers should be called with debug=True
    mock_fetch_papers.assert_called_once_with("debug query", debug=True)
    mock_save_papers.assert_not_called()

@patch('pubmed_parser.fetch_and_filter_pubmed_papers')
def test_cli_no_papers_found(mock_fetch_papers, capsys):
    """
    Test CLI behavior when no papers are found.
    """
    mock_fetch_papers.return_value = [] # Simulate no papers found

    test_args = ["get-papers-list", "empty query"]
    with patch.object(sys, 'argv', test_args):
        # We expect a SystemExit because sys.exit(0) is called
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0 # Ensure it exits with code 0

    captured = capsys.readouterr()
    assert "No relevant papers found or an error occurred. Exiting." in captured.out
    mock_fetch_papers.assert_called_once_with("empty query", debug=False)

def test_cli_help_message(capsys):
    """
    Test the --help flag.
    """
    test_args = ["get-papers-list", "--help"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0 # Help message exits with code 0

    captured = capsys.readouterr()
    assert "usage: get-papers-list" in captured.out
    assert "Fetch research papers from PubMed" in captured.out
    assert "--file" in captured.out
    assert "--debug" in captured.out
    assert "--help" in captured.out

def test_cli_version_message(capsys):
    """
    Test the --version flag.
    """
    test_args = ["get-papers-list", "--version"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0 # Version message exits with code 0

    captured = capsys.readouterr()
    assert "get-papers-list 0.1.0" in captured.out # Matches version in pyproject.toml
