import json
import argparse
from statistics import mean
from typing import Any, Dict, List, Tuple, Optional


def load_json_records(path: str) -> List[Dict[str, Any]]:
    """
    Loads:
      - a normal JSON array (most common), OR
      - a single JSON object, OR
      - JSON Lines (one JSON object per line)

    If your file is strict JSON array, json.load will work immediately.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    # Try standard JSON first
    try:
        data = json.loads(raw)
        return data
    except Exception as e:
        raise ValueError(f"Unable to process .json file {path}: {e}")



def safe_int(x: Any) -> int:
    try:
        if x is None:
            return 0
        return int(x)
    except (ValueError, TypeError):
        return 0


def analyze(records: List[Dict[str, Any]], max_retrieve: int = 120, low_threshold: int = 24, healthy_recall: int = 60) -> Dict[str, Any]:
    per_row = []
    deltas: List[int] = []
    positive_delta:List[int] = []
    negative_delta:List[int] = []
    pos = neg = zero = zeroExludingMaxResults = 0
    orig_hits_max = 0
    syn_any_hits_max = 0
    gen_hits_max = 0
    
    # Threshold-based metrics
    case1_low_to_healthy = 0  # original < low_threshold AND generated >= healthy
    case2_healthy_to_low = 0  # original >= healthy AND generated < healthy
    case3_both_low = 0        # both < low_threshold
    case4_both_healthy = 0    # both >= healthy

    for r in records:
        input_text = r.get("input_text", "")
        output_synonyms = r.get("output_synonyms") or [] #Output synonym is array in json file
        products_matched = r.get("products_matched") or {}

        # Missing keyword => treat as zero
        original_syn_recall = safe_int(products_matched.get(input_text, 0))

        syn_recalls = [safe_int(products_matched.get(s, 0)) for s in output_synonyms]
        generated_syn_recall = max(syn_recalls) if syn_recalls else 0

        delta = generated_syn_recall - original_syn_recall
        
        deltas.append(delta)
        
        if delta > 0:
            positive_delta.append(delta)
            pos += 1
        elif delta < 0:
            negative_delta.append(delta)
            neg += 1
        else:
            zero += 1
            if original_syn_recall != max_retrieve:
                zeroExludingMaxResults += 1

        if original_syn_recall == max_retrieve:
            orig_hits_max += 1

        if any(v == max_retrieve for v in syn_recalls):
            syn_any_hits_max += 1

        if generated_syn_recall == max_retrieve:
            gen_hits_max += 1
        
        # Calculate 4 metrics based on thresholds
        if original_syn_recall < low_threshold and generated_syn_recall >= healthy_recall:
            case1_low_to_healthy += 1
        elif original_syn_recall >= healthy_recall and generated_syn_recall < low_threshold:
            case2_healthy_to_low += 1
        elif original_syn_recall < low_threshold and generated_syn_recall < low_threshold:
            case3_both_low += 1
        elif original_syn_recall >= healthy_recall and generated_syn_recall >= healthy_recall:
            case4_both_healthy += 1

        per_row.append(
            {
                "input_text": input_text,
                "original_syn_recall": original_syn_recall,
                "generated_syn_recall": generated_syn_recall,
                "delta": delta,
                "synonyms": output_synonyms,
                "synonym_recalls": syn_recalls,
                "annotated": r.get("annotated", None),
            }
        )

    n = len(records)
    avg_delta = mean(deltas)
    avg_positive_delta = mean(positive_delta) if positive_delta else 0
    avg_negative_delta = mean(negative_delta) if negative_delta else 0
    return {
        "n_records": n,
        "avg_delta": avg_delta,
        "avg_positive_delta": avg_positive_delta,
        "avg_negative_delta": avg_negative_delta,
        "delta_positive": pos,
        "delta_negative": neg,
        "delta_zero": zero,
        "delta_zero_excl_max_results": zeroExludingMaxResults,
        "orig_equals_max_retrieve": orig_hits_max,
        "synonyms_any_equals_max_retrieve": syn_any_hits_max,
        "generated_equals_max_retrieve": gen_hits_max,
        "case1_low_to_healthy": case1_low_to_healthy,
        "case2_healthy_to_low": case2_healthy_to_low,
        "case3_both_low": case3_both_low,
        "case4_both_healthy": case4_both_healthy,
        "per_row": per_row,  # later use this for error analysis or exporting results
    }


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--path", required=True, help="Path to the JSON file")
    parser.add_argument("--max-retrieve", type=int, default=120, help="Max retrieve value (e.g., 120)")
    parser.add_argument("--low-threshold", type=int, default=24, help="Low threshold for recall")
    parser.add_argument("--healthy-recall", type=int, default=60, help="Healthy recall threshold")
    parser.add_argument("--out", default=None, help="Optional: write per-row results to JSON")
    args = parser.parse_args()

    records = load_json_records("bigQueryOutput/translator_gemini_3_synonyms_gen_zh_to_jp.json")
    results = analyze(records, max_retrieve=args.max_retrieve, 
                     low_threshold=args.low_threshold, 
                     healthy_recall=args.healthy_recall)

    # Print summary statistics
    
    print(f"Records: {results['n_records']}")
    print(f"Average delta: {results['avg_delta']:.6f}")
    print(f"Average positive delta: {results['avg_positive_delta']:.6f}")
    print(f"Average negative delta: {results['avg_negative_delta']:.6f}")
    ##To do make a pie chart to show the distribution of positive/negative/zero deltas
    print(f"Delta > 0: {results['delta_positive']}")
    print(f"Delta < 0: {results['delta_negative']}")
    print(f"Delta = 0 (excluding max retrieve cases): {results['delta_zero_excl_max_results']}")
    ##############
    print(f"Delta = 0: {results['delta_zero']}")
    ##make a Bar graph to show the distribution of original recall == max_retrieve, generated recall == max_retrieve, and any synonym recall == max_retrieve
    print(f"Original recall == {args.max_retrieve}: {results['orig_equals_max_retrieve']}")
    print(f"Generated (max synonym) == {args.max_retrieve}: {results['generated_equals_max_retrieve']}")
    ##########
    print("\n--- Threshold-based Metrics ---")
    print(f"Case 1 (orginal query recall performed worse than {args.low_threshold}({args.low_threshold/12} scrolls)  ,\n generated recall performed better than {args.healthy_recall}): {results['case1_low_to_healthy']}")
    print(f"Case 2 (orginal query recall performed better than {args.healthy_recall}({args.healthy_recall/12} scrolls) ,\n generated recall performed worse than {args.low_threshold}({args.low_threshold/12} scrolls)): {results['case2_healthy_to_low']}")
    print(f"Case 3 (Both Low): {results['case3_both_low']}")
    print(f"Case 4 (Both Healthy): {results['case4_both_healthy']}")
    
    # Optional export
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results["per_row"], f, ensure_ascii=False, indent=2)
        print(f"Wrote per-row output to: {args.out}")


if __name__ == "__main__":
    main()