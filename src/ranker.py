from typing import List, Dict, Any

def compute_temporal_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    """Computes temporal Intersection over Union between two time intervals."""
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    if union <= 0.0:
        return 0.0
    return intersection / union

def apply_temporal_nms(promos: List[Dict[str, Any]], iou_threshold: float = 0.35, max_per_episode: int = 2) -> List[Dict[str, Any]]:
    """
    Applies Non-Maximum Suppression on candidate promos within an episode
    to filter out redundant, overlapping cut variants and preserve only the best distinct moments.
    """
    # Sort descending by total_virality_score
    sorted_promos = sorted(promos, key=lambda p: p["scores"]["total_virality_score"], reverse=True)
    selected: List[Dict[str, Any]] = []

    for cand in sorted_promos:
        c_start = cand["segments"][0]["start_sec"] if "start_sec" in cand["segments"][0] else 0.0
        c_end = cand["segments"][-1]["end_sec"] if "end_sec" in cand["segments"][-1] else 0.0

        overlap = False
        for chosen in selected:
            ch_start = chosen["segments"][0]["start_sec"] if "start_sec" in chosen["segments"][0] else 0.0
            ch_end = chosen["segments"][-1]["end_sec"] if "end_sec" in chosen["segments"][-1] else 0.0

            iou = compute_temporal_iou(c_start, c_end, ch_start, ch_end)
            if iou > iou_threshold:
                overlap = True
                break

        if not overlap:
            selected.append(cand)
            if len(selected) >= max_per_episode:
                break

    return selected

def rank_promo_campaign(all_episode_promos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ranks the entire collection of promos across all 50 episodes and creates
    the definitive Ad Posting Schedule with marketing funnels and strategic rationales.
    """
    # Sort by total virality score
    ranked_all = sorted(all_episode_promos, key=lambda p: p["scores"]["total_virality_score"], reverse=True)
    
    # Assign global rank
    for idx, p in enumerate(ranked_all, 1):
        p["global_rank"] = idx

    # Categorize into strategic campaign buckets
    tofu_promos = [p for p in ranked_all if ("Top-of-Funnel" in p["target_funnel"] or p["scores"]["hook_strength"] >= 26.0) and p["quality_audit"]["status"] != "FAIL"]
    mofu_promos = [p for p in ranked_all if ("High-Curiosity" in p["target_funnel"] or p["scores"]["cliffhanger_tension"] >= 21.0) and p["quality_audit"]["status"] != "FAIL"]
    bofu_promos = [p for p in ranked_all if ("Catharsis" in p["target_funnel"] or "Retargeting" in p["target_funnel"]) and p["quality_audit"]["status"] != "FAIL"]

    # Posting Calendar recommendations
    schedule = [
        {
            "priority": "PHASE 1: PRE-LAUNCH & HERO TEST (Day 1 - Day 3)",
            "goal": "Cold User Acquisition (Scale top-of-funnel reach on TikTok & Instagram Reels at lowest CAC)",
            "recommended_promos": tofu_promos[:3],
            "strategic_rationale": "Post Episode 1 altar rejection and Episode 3 altar rescue first. These require ZERO prior lore, leverage universal high-arousal emotions (betrayal, indignity, chivalric rescue), and achieve the highest 3-second thumb-stop rates."
        },
        {
            "priority": "PHASE 2: RETARGETING & CURIOSITY CLIFFHANGERS (Day 4 - Day 7)",
            "goal": "Drive App Installs & In-App Coin / Episode Unlocks",
            "recommended_promos": mofu_promos[:3],
            "strategic_rationale": "Target users who viewed 50%+ of Phase 1 ads. Use high-stakes ordeals (e.g. Episode 12/13 blackthorn briar ultimatum and Episode 41 chained bride assault) that end on unresolved life-or-death consequences, forcing users to download the app to see the resolution."
        },
        {
            "priority": "PHASE 3: HIGH-CATHARSIS PAYOFF & LTV CONVERSION (Day 8 - Day 14)",
            "goal": "Re-engagement, Retention & Show Bingeing",
            "recommended_promos": bofu_promos[:3] if bofu_promos else ranked_all[6:9],
            "strategic_rationale": "Showcase the ultimate power-reversals (e.g. Episode 42 Duke identity reveal and Episode 47 scullery maid retribution). Delivers intense emotional satisfaction and proves to prospective viewers that the emotional payoff is worth watching all 50 episodes."
        }
    ]

    return {
        "total_promos_evaluated": len(all_episode_promos),
        "top_10_hero_promos": ranked_all[:10],
        "campaign_schedule": schedule,
        "all_ranked_promos": ranked_all
    }
