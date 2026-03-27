import json
from statistics import mean, median, stdev
from typing import Any, Dict, List


def load_json_records(path: str) -> List[Dict[str, Any]]:
    """Load JSON records from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_int(x: Any) -> int:
    """Safely convert value to int, returning 0 if conversion fails."""
    try:
        if x is None:
            return 0
        return int(x)
    except (ValueError, TypeError):
        return 0


def analyze_query_list(
    all_records: List[Dict[str, Any]], 
    query_list: List[str],
    max_retrieve: int = 120
) -> Dict[str, Any]:
    """
    Analyze a specific list of queries from the full records.
    
    Args:
        all_records: Full list of records from JSON file
        query_list: List of input_text values to analyze
        max_retrieve: Maximum retrieve value
        
    Returns:
        Dictionary containing analysis results
    """
    # Filter records to only those in query_list
    filtered_records = [r for r in all_records if r.get("input_text", "") in query_list]
    
    if not filtered_records:
        return {
            "error": "No matching records found for the provided queries",
            "queries_requested": len(query_list),
            "queries_found": 0
        }
    
    # Collect values for statistics
    original_recalls = []
    
    for record in filtered_records:
        input_text = record.get("input_text", "")
        products_matched = record.get("products_matched") or {}
        
        # Original recall - check for case-insensitive matches and take max
        # Edge case: "kyosho mini-z" and "KYOSHO MINI-Z" should be treated as same
        input_text_lower = input_text.lower()
        matching_recalls = [
            safe_int(v) for k, v in products_matched.items() 
            if k.lower() == input_text_lower
        ]
        original_recall = max(matching_recalls) if matching_recalls else 0
        original_recalls.append(original_recall)
    
    # Calculate statistics
    results = {
        "queries_requested": len(query_list),
        "queries_found": len(filtered_records),
        "queries_not_found": list(set(query_list) - set([r.get("input_text") for r in filtered_records])),
        
        # Original query recall statistics
        "original_recall_stats": {
            "count": len(original_recalls),
            "mean": mean(original_recalls) if original_recalls else 0,
            "median": median(original_recalls) if original_recalls else 0,
            "std": stdev(original_recalls) if len(original_recalls) > 1 else 0,
            "min": min(original_recalls) if original_recalls else 0,
            "max": max(original_recalls) if original_recalls else 0
        }
    
    }
    
    return results


def main():
    # Static configuration
    query_list = ["腕時計", "煉獄杏寿郎 七夕", "赤西仁", "ドリルビット", "正反対な君と僕"]
    data_file = "bigQueryOutput/translator_gemini_3_synonyms_gen_zh_to_jp.json"
    max_retrieve = 120
    output_file = None  # Set to a filename like "results.json" to save output
    
    # Load all records
    all_records = load_json_records(data_file)
    
    # Analyze
    results = analyze_query_list(all_records, query_list, max_retrieve)
    
    # Print summary
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"\n{'='*60}")
    print(f"QUERY LIST ANALYSIS")
    print(f"{'='*60}")
    print(f"Queries requested: {results['queries_requested']}")
    print(f"Queries found: {results['queries_found']}")
    if results['queries_not_found']:
        print(f"Queries not found: {results['queries_not_found']}")
    
    print(f"\n{'='*60}")
    print(f"ORIGINAL QUERY RECALL STATISTICS")
    print(f"{'='*60}")
    orig = results['original_recall_stats']
    print(f"Mean: {orig['mean']:.2f}")
    print(f"Median: {orig['median']:.2f}")
    print(f"Std Dev: {orig['std']:.2f}")
    print(f"Min: {orig['min']}")
    print(f"Max: {orig['max']}")
    
    
    

if __name__ == "__main__":
    main()
