import os
import json
import argparse
from typing import Dict, Any, List

def time_to_sec(t_str: str) -> float:
    t_str = str(t_str).strip().strip("()")
    parts = t_str.split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60.0 + float(parts[1])
    elif len(parts) == 3:
        return float(parts[0]) * 3600.0 + float(parts[1]) * 60.0 + float(parts[2])
    return float(t_str)

def compute_temporal_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    if union <= 0.0:
        return 0.0
    return intersection / union

def evaluate_run(run_data: Dict[str, Any], gold_data: List[Dict[str, Any]], iou_threshold: float = 0.5) -> Dict[str, Any]:
    promos_by_ep = {}
    for p in run_data.get("all_promos", []):
        ep = p["episode"]
        if ep not in promos_by_ep:
            promos_by_ep[ep] = []
        # Ensure start_sec and end_sec exist
        if "start_sec" not in p:
            p["start_sec"] = time_to_sec(p["start_time"])
        if "end_sec" not in p:
            p["end_sec"] = time_to_sec(p["end_time"])
        promos_by_ep[ep].append(p)

    gold_total = len(gold_data)
    matches = 0
    ious = []
    hook_alignments = []
    cliff_alignments = []
    detailed_results = []

    for gold in gold_data:
        ep = gold["episode"]
        cands = promos_by_ep.get(ep, [])
        if not cands:
            detailed_results.append({
                "episode": ep,
                "title": gold["title"],
                "gold_span": f"{gold['start_time']} - {gold['end_time']}",
                "best_tool_span": "NONE (Missing)",
                "iou": 0.0,
                "match": False,
                "hook_aligned_within_3s": False,
                "cliffhanger_aligned_within_3s": False
            })
            continue

        best_cand = cands[0] if cands else None
        best_iou = 0.0
        for c in cands:
            iou = compute_temporal_iou(gold["start_sec"], gold["end_sec"], c["start_sec"], c["end_sec"])
            if iou > best_iou:
                best_iou = iou
                best_cand = c

        ious.append(best_iou)
        is_match = best_iou >= iou_threshold
        if is_match:
            matches += 1

        hook_match = abs(gold["start_sec"] - best_cand["start_sec"]) <= 3.0 if best_cand else False
        cliff_match = abs(gold["end_sec"] - best_cand["end_sec"]) <= 3.0 if best_cand else False
        if hook_match: hook_alignments.append(1)
        if cliff_match: cliff_alignments.append(1)

        detailed_results.append({
            "episode": ep,
            "title": gold["title"],
            "gold_span": f"{gold['start_time']} - {gold['end_time']}",
            "best_tool_span": f"{best_cand['start_time']} - {best_cand['end_time']}" if best_cand else "NONE",
            "iou": round(best_iou, 3),
            "match": is_match,
            "hook_aligned_within_3s": hook_match,
            "cliffhanger_aligned_within_3s": cliff_match
        })

    recall = round(matches / max(1, gold_total), 3)
    avg_iou = round(sum(ious) / max(1, len(ious)), 3)
    hook_accuracy = round(len(hook_alignments) / max(1, gold_total), 3)
    cliff_accuracy = round(len(cliff_alignments) / max(1, gold_total), 3)

    return {
        "gold_episodes_tested": gold_total,
        "matches_found": matches,
        "recall_at_iou_50": recall,
        "average_temporal_iou": avg_iou,
        "hook_alignment_rate_3s": hook_accuracy,
        "cliffhanger_alignment_rate_3s": cliff_accuracy,
        "detailed_results": detailed_results
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate promo extraction runs against gold benchmark.")
    parser.add_argument("--run1", default="outputs/promos_all_50_episodes.json", help="Path to primary run JSON.")
    parser.add_argument("--run2", default=None, help="Optional second run JSON for side-by-side comparison.")
    parser.add_argument("--gold", default="data/gold_promos.json", help="Path to gold dataset JSON.")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    run1_path = os.path.join(base_dir, args.run1) if not os.path.isabs(args.run1) else args.run1
    gold_path = os.path.join(base_dir, args.gold) if not os.path.isabs(args.gold) else args.gold

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    with open(run1_path, "r", encoding="utf-8") as f:
        run1_data = json.load(f)

    res1 = evaluate_run(run1_data, gold_data)

    print("\n" + "="*70)
    print("📊 KUKU PROMO FINDER — GOLD BENCHMARK EVALUATION")
    print("="*70)
    print(f"Evaluated File: {args.run1}")
    print(f"Gold Clips Tested: {res1['gold_episodes_tested']} iconic milestone episodes")
    print(f"Matches (IoU >= 0.50): {res1['matches_found']} / {res1['gold_episodes_tested']} ({res1['recall_at_iou_50']*100:.1f}% Recall)")
    print(f"Average Temporal IoU: {res1['average_temporal_iou']:.3f}")
    print(f"3-Second Hook Alignment: {res1['hook_alignment_rate_3s']*100:.1f}%")
    print(f"3-Second Cliffhanger Alignment: {res1['cliffhanger_alignment_rate_3s']*100:.1f}%")
    print("-" * 70)
    print(f"{'Ep':<4} | {'Gold Span':<17} | {'Tool Span':<17} | {'IoU':<6} | {'Hook ±3s':<9} | {'Result':<6}")
    print("-" * 70)
    for r in res1["detailed_results"]:
        status = "MATCH" if r["match"] else "MISS"
        h_status = "YES" if r.get("hook_aligned_within_3s") else "NO"
        print(f"Ep{r['episode']:02d} | {r['gold_span']:<17} | {r['best_tool_span']:<17} | {r['iou']:<6} | {h_status:<9} | {status}")
    print("="*70)

    # Optional side-by-side comparison
    if args.run2:
        run2_path = os.path.join(base_dir, args.run2) if not os.path.isabs(args.run2) else args.run2
        with open(run2_path, "r", encoding="utf-8") as f:
            run2_data = json.load(f)
        res2 = evaluate_run(run2_data, gold_data)

        print("\n" + "="*70)
        print("⚔️ SIDE-BY-SIDE MODEL COMPARISON")
        print("="*70)
        print(f"{'Metric':<32} | {'Model / Run 1':<16} | {'Model / Run 2':<16}")
        print("-" * 70)
        print(f"{'Recall @ IoU >= 0.50':<32} | {res1['recall_at_iou_50']*100:.1f}%{'':<10} | {res2['recall_at_iou_50']*100:.1f}%")
        print(f"{'Average Temporal IoU':<32} | {res1['average_temporal_iou']:.3f}{'':<10} | {res2['average_temporal_iou']:.3f}")
        print(f"{'Hook Alignment (±3s)':<32} | {res1['hook_alignment_rate_3s']*100:.1f}%{'':<10} | {res2['hook_alignment_rate_3s']*100:.1f}%")
        print(f"{'Cliffhanger Alignment (±3s)':<32} | {res1['cliffhanger_alignment_rate_3s']*100:.1f}%{'':<10} | {res2['cliffhanger_alignment_rate_3s']*100:.1f}%")
        print("="*70 + "\n")

if __name__ == "__main__":
    main()
