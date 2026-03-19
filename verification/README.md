# Verification Module

This directory contains scripts for verifying data consistency across the pipeline.

## Scripts

### `verify_bigquery_coverage.py`

Verifies that all queries in `search_results/search_log.csv` are present in the BigQuery dump (`bigQueryDump/bigquery.json`).

**Purpose:**
- Identifies queries that were searched but not uploaded to BigQuery
- Removes missing queries from search_log.csv to maintain data consistency
- Generates a detailed report of missing queries

**Usage:**
```bash
python3 verification/verify_bigquery_coverage.py
```

**Exit Codes:**
- `0`: All queries verified successfully
- `1`: Missing queries found (requires pipeline re-run)

**Output Files:**
- `verification/missing_queries_report.txt`: Detailed report of missing queries

**Integration:**
This script is automatically run during the Processing Phase (Phase 2) of the pipeline before BigQuery data processing.
