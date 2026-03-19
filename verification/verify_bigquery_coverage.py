#!/usr/bin/env python3
"""
BigQuery Coverage Verification Script

This script verifies that all queries in search_log.csv are present in the
BigQuery dump (bigquery.json). It identifies missing queries, removes them
from the search log, and prompts the user to rerun the pipeline.

Usage:
    python verification/verify_bigquery_coverage.py
"""
import os
import sys
import csv
import json
from typing import Set, List


# File paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH_LOG_PATH = os.path.join(PROJECT_ROOT, "search_results", "search_log.csv")
BIGQUERY_JSON_PATH = os.path.join(PROJECT_ROOT, "bigQueryDump", "bigquery.json")
MISSING_QUERIES_REPORT = os.path.join(PROJECT_ROOT, "verification", "missing_queries_report.txt")


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def load_search_log_queries() -> Set[str]:
    """
    Load all queries from search_log.csv
    
    Returns:
        Set of query strings from the search log
    """
    if not os.path.exists(SEARCH_LOG_PATH):
        print(f"{Colors.FAIL}Error: search_log.csv not found at {SEARCH_LOG_PATH}{Colors.ENDC}")
        sys.exit(1)
    
    queries = set()
    try:
        with open(SEARCH_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                query = row.get('original_query', '').strip()
                if query:
                    queries.add(query)
        
        print(f"{Colors.OKGREEN}✓ Loaded {len(queries)} unique queries from search_log.csv{Colors.ENDC}")
        return queries
    
    except Exception as e:
        print(f"{Colors.FAIL}Error reading search_log.csv: {e}{Colors.ENDC}")
        sys.exit(1)


def load_bigquery_queries() -> Set[str]:
    """
    Load all original_query values from bigquery.json (NDJSON format)
    
    Returns:
        Set of query strings from BigQuery dump
    """
    if not os.path.exists(BIGQUERY_JSON_PATH):
        print(f"{Colors.FAIL}Error: bigquery.json not found at {BIGQUERY_JSON_PATH}{Colors.ENDC}")
        sys.exit(1)
    
    queries = set()
    line_num = 0
    
    try:
        with open(BIGQUERY_JSON_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    query = entry.get('original_query', '').strip()
                    if query:
                        queries.add(query)
                except json.JSONDecodeError as e:
                    print(f"{Colors.WARNING}Warning: Failed to parse line {line_num}: {e}{Colors.ENDC}")
                    continue
        
        print(f"{Colors.OKGREEN}✓ Loaded {len(queries)} unique queries from bigquery.json{Colors.ENDC}")
        return queries
    
    except Exception as e:
        print(f"{Colors.FAIL}Error reading bigquery.json: {e}{Colors.ENDC}")
        sys.exit(1)


def find_missing_queries(search_queries: Set[str], bigquery_queries: Set[str]) -> List[str]:
    """
    Find queries that are in search_log but not in bigquery dump
    
    Args:
        search_queries: Set of queries from search_log.csv
        bigquery_queries: Set of queries from bigquery.json
    
    Returns:
        Sorted list of missing queries
    """
    missing = search_queries - bigquery_queries
    return sorted(list(missing))


def remove_missing_queries_from_search_log(missing_queries: Set[str]) -> int:
    """
    Remove missing queries from search_log.csv
    
    Args:
        missing_queries: Set of queries to remove
    
    Returns:
        Number of rows removed
    """
    if not missing_queries:
        return 0
    
    # Read all rows
    rows_to_keep = []
    removed_count = 0
    
    try:
        with open(SEARCH_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                query = row.get('original_query', '').strip()
                if query not in missing_queries:
                    rows_to_keep.append(row)
                else:
                    removed_count += 1
        
        # Write back the filtered rows
        with open(SEARCH_LOG_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_keep)
        
        print(f"{Colors.OKGREEN}✓ Removed {removed_count} missing queries from search_log.csv{Colors.ENDC}")
        return removed_count
    
    except Exception as e:
        print(f"{Colors.FAIL}Error updating search_log.csv: {e}{Colors.ENDC}")
        sys.exit(1)


def save_missing_queries_report(missing_queries: List[str]):
    """
    Save missing queries to a report file
    
    Args:
        missing_queries: List of missing queries
    """
    # Ensure verification directory exists
    os.makedirs(os.path.dirname(MISSING_QUERIES_REPORT), exist_ok=True)
    
    try:
        with open(MISSING_QUERIES_REPORT, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MISSING QUERIES REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total missing queries: {len(missing_queries)}\n")
            f.write(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("These queries were found in search_log.csv but not in bigquery.json:\n")
            f.write("-" * 80 + "\n\n")
            
            for i, query in enumerate(missing_queries, 1):
                f.write(f"{i}. {query}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("ACTION TAKEN: These queries have been removed from search_log.csv\n")
            f.write("NEXT STEP: Please re-run the pipeline from the setup phase\n")
            f.write("=" * 80 + "\n")
        
        print(f"{Colors.OKGREEN}✓ Report saved to: {MISSING_QUERIES_REPORT}{Colors.ENDC}")
    
    except Exception as e:
        print(f"{Colors.WARNING}Warning: Could not save report: {e}{Colors.ENDC}")


def main():
    """Main verification function"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("BigQuery Coverage Verification")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    # Load queries from both sources
    print(f"{Colors.OKCYAN}▶ Loading search_log.csv...{Colors.ENDC}")
    search_queries = load_search_log_queries()
    
    print(f"\n{Colors.OKCYAN}▶ Loading bigquery.json...{Colors.ENDC}")
    bigquery_queries = load_bigquery_queries()
    
    # Find missing queries
    print(f"\n{Colors.OKCYAN}▶ Comparing queries...{Colors.ENDC}")
    missing_queries = find_missing_queries(search_queries, bigquery_queries)
    extra_queries = sorted(list(bigquery_queries - search_queries))
    common_queries = search_queries & bigquery_queries
    
    # Report results
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("VERIFICATION RESULTS")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    print(f"Queries in search_log.csv:                    {len(search_queries)}")
    print(f"Queries in bigquery.json:                     {len(bigquery_queries)}")
    print(f"Common queries (in both):                     {len(common_queries)}")
    print(f"Missing (in search_log, NOT in bigquery):    {len(missing_queries)}")
    print(f"Extra (in bigquery, NOT in search_log):      {len(extra_queries)}")
    
    if not missing_queries:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ SUCCESS: All queries in search_log.csv are present in bigquery.json{Colors.ENDC}")
        
        if extra_queries:
            print(f"\n{Colors.OKCYAN}ℹ INFO: BigQuery has {len(extra_queries)} additional queries not in search_log{Colors.ENDC}")
            print(f"{Colors.OKCYAN}(This is normal if BigQuery contains other searches){Colors.ENDC}")
        
        print(f"\n{Colors.OKGREEN}You can proceed with the pipeline.{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ WARNING: {len(missing_queries)} queries are missing from bigquery.json{Colors.ENDC}\n")
        
        # Display missing queries (limit to first 20 for console output)
        print(f"{Colors.WARNING}Missing queries (in search_log but NOT in bigquery):{Colors.ENDC}")
        for i, query in enumerate(missing_queries[:20], 1):
            print(f"  {i}. {query}")
        
        if len(missing_queries) > 20:
            print(f"  ... and {len(missing_queries) - 20} more")
        
        # Display extra queries info
        if extra_queries:
            print(f"\n{Colors.OKCYAN}Extra queries (in bigquery but NOT in search_log): {len(extra_queries)}{Colors.ENDC}")
            for i, query in enumerate(extra_queries[:10], 1):
                print(f"  {i}. {query}")
            if len(extra_queries) > 10:
                print(f"  ... and {len(extra_queries) - 10} more")
        
        # Save report
        print(f"\n{Colors.OKCYAN}▶ Saving detailed report...{Colors.ENDC}")
        save_missing_queries_report(missing_queries)
        
        # Remove missing queries from search log
        print(f"\n{Colors.OKCYAN}▶ Cleaning search_log.csv...{Colors.ENDC}")
        removed = remove_missing_queries_from_search_log(set(missing_queries))
        
        # Final instructions
        print(f"\n{Colors.WARNING}{Colors.BOLD}{'='*80}")
        print("ACTION REQUIRED")
        print(f"{'='*80}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}The missing queries have been removed from search_log.csv.")
        print(f"Please re-run the pipeline from the setup phase to ensure")
        print(f"all queries are properly processed and uploaded to BigQuery.{Colors.ENDC}\n")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
