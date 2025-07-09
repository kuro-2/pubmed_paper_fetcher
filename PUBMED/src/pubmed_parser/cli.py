#cli.py
import argparse
import sys
from typing import List, Dict, Any

from pubmed_parser import fetch_and_filter_pubmed_papers, save_papers_to_csv

def main():
    """
    Main function for the command-line interface to fetch and filter PubMed papers.
    """
    parser = argparse.ArgumentParser(
        description="Fetch research papers from PubMed, filter by non-academic author "
                    "affiliations, and output results to CSV or console."
    )
    parser.add_argument(
        "query",
        type=str,
        help="The PubMed query string (e.g., 'cancer AND therapy[mesh]')"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Specify the filename to save the results as a CSV. "
             "If not provided, output will be printed to the console."
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Print debug information during execution."
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.1.0", # Replace with your actual version if needed
        help="Show program's version number and exit."
    )

    args = parser.parse_args()

    if args.debug:
        print("Debug mode enabled.")

    papers = fetch_and_filter_pubmed_papers(args.query, debug=args.debug)

    if not papers:
        print("No relevant papers found or an error occurred. Exiting.")
        sys.exit(0)

    if args.file:
        save_papers_to_csv(papers, args.file)
    else:
        # Print to console in a readable format
        print("\n--- Filtered Papers ---")
        for i, paper in enumerate(papers):
            print(f"\nPaper {i+1}:")
            for key, value in paper.items():
                print(f"  {key}: {value}")
        print("\n-----------------------")

if __name__ == "__main__":
    main()