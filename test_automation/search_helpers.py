"""
Search Results Configuration and Helper Module

This module provides configuration and helper functions for managing
search results and logging.
"""
import os
import csv
from datetime import datetime
from typing import Dict, List


class SearchLogger:
    """
    Helper class to manage search result logging.
    """
    
    def __init__(self, output_path: str):
        """
        Initialize the SearchLogger.
        
        Args:
            output_path: Path to the output CSV file
        """
        self.output_path = output_path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the output directory exists."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
    
    def log_search(self, original_query: str, searched: bool = True) -> None:
        """
        Log a search entry to CSV.
        
        Args:
            original_query: The query that was searched
            searched: Boolean indicating if search was performed
        """
        file_exists = os.path.isfile(self.output_path)
        
        with open(self.output_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["original_query", "searched", "date"]
            )
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                "original_query": original_query,
                "searched": str(searched),
                "date": datetime.now().strftime("%d/%m/%Y")
            })
    
    def get_searched_queries(self) -> List[str]:
        """
        Get list of queries that have already been searched.
        
        Returns:
            List of query strings that have been searched
        """
        if not os.path.exists(self.output_path):
            return []
        
        searched = []
        with open(self.output_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("searched", "").lower() == "true":
                    searched.append(row.get("original_query", ""))
        
        return searched
    
    def clear_log(self) -> None:
        """Clear the search log file."""
        if os.path.exists(self.output_path):
            os.remove(self.output_path)


def parse_synonyms(output_text: str) -> List[str]:
    """
    Parse synonym string separated by pipe character.
    
    Args:
        output_text: String containing synonyms separated by |
        
    Returns:
        List of synonym strings
        
    Example:
        >>> parse_synonyms("僕のヒーローアカデミア|ヒロアカ")
        ['僕のヒーローアカデミア', 'ヒロアカ']
    """
    return [s.strip() for s in output_text.split('|') if s.strip()]


def format_search_summary(total_rows: int, total_searches: int) -> str:
    """
    Format a summary of the search operation.
    
    Args:
        total_rows: Number of rows processed
        total_searches: Total number of searches performed
        
    Returns:
        Formatted summary string
    """
    return f"""
{'='*60}
Search Operation Summary
{'='*60}
Rows Processed:    {total_rows}
Total Searches:    {total_searches}
Average Searches:  {total_searches / total_rows if total_rows > 0 else 0:.2f} per row
{'='*60}
"""


if __name__ == "__main__":
    # Example usage
    logger = SearchLogger("search_results/search_log.csv")
    
    # Test parse synonyms
    test_output = "僕のヒーローアカデミア|ヒロアカ"
    synonyms = parse_synonyms(test_output)
    print(f"Parsed synonyms: {synonyms}")
    
    # Test logging
    logger.log_search("我的英雄學院")
    for synonym in synonyms:
        logger.log_search(synonym)
    
    print("\nLogged searches successfully!")
