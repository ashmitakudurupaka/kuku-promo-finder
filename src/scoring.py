import re
from typing import Dict, Any, List, Tuple
from src.segmenter import CandidateWindow, HOOK_KEYWORDS, CLIFFHANGER_KEYWORDS
from src.parser import Beat, sec_to_time

# Core Microdrama Tropes prevalent in Kuku / ReelShort shows
TROPES_TAXONOMY = {
    "Altar Betrayal & Abandonment": ["marrying", "sister", "altar", "bridal", "gown", "gerald", "wedding", "former groom"],
    "Secret Noble / Duke in Disguise": ["scarred", "warrior", "bearded", "duke", "ashburn", "regalia", "true duke", "proposal"],
    "Cruel In-Laws & Stepmother": ["matriarch", "disowned", "ledger", "mother", "jewel of the family", "worthless"],
    "Sadistic Ordeal & Sacrifice": ["blackthorn", "briars", "bare hands", "lacerations", "hang", "theft", "signet ring"],
    "Chains & Public Humiliation": ["chains", "paraded", "humiliation", "scullery maid", "knees", "beg"],
    "Vengeful Retribution & Explosion": ["explosion", "shatters", "smoke", "treason", "arrest", "high priest", "invalid"]
}

def analyze_hook(cand: CandidateWindow) -> Tuple[float, str]:
    """
    Evaluates the first 3.0 seconds of the window.
    Returns (score [0-30], hook_description).
    """
    first_3s_limit = cand.start_sec + 3.0
    hook_beats = [b for b in cand.beats if b.start_sec <= first_3s_limit or (b.start_sec <= cand.start_sec + 4.5 and len(cand.beats) > 0 and b == cand.beats[0])]
    if not hook_beats:
        hook_beats = cand.beats[:1]
        
    score = 8.0 # Baseline
    cues_found = []
    
    for b in hook_beats:
        text_lower = b.content.lower()
        
        # Check action violence / kinetic movement
        for kw in HOOK_KEYWORDS["action"]:
            if re.search(rf"\b{kw}\b", text_lower):
                score += 5.0
                cues_found.append(f"kinetic action ({kw})")
                break
                
        # Check dialogue shock
        if b.beat_type == "DIALOGUE":
            score += 4.0
            for kw in HOOK_KEYWORDS["dialogue"]:
                if re.search(rf"\b{kw}\b", text_lower):
                    score += 5.0
                    cues_found.append(f"verbal shock ('{kw}')")
                    break
                    
            # Check delivery / emotion parenthetical
            if b.delivery:
                del_lower = b.delivery.lower()
                for kw in HOOK_KEYWORDS["delivery"]:
                    if kw in del_lower:
                        score += 3.0
                        cues_found.append(f"heightened emotion ({b.delivery})")
                        break
                        
        # Camera drama
        if b.beat_type == "CAMERA":
            if any(k in text_lower for k in ["close-up", "extreme close-up", "push-in", "tracking", "interlocked"]):
                score += 3.0
                cues_found.append("dramatic camera focus")
                
    # Normalize score
    score = min(30.0, score)
    
    # Generate human-readable hook description
    first_dialogue = next((b for b in hook_beats if b.beat_type == "DIALOGUE"), None)
    first_action = next((b for b in hook_beats if b.beat_type == "ACTION"), None)
    
    if first_dialogue and first_action:
        hook_desc = f"{first_action.content[:90]}... as {first_dialogue.character} cuts in: {first_dialogue.content}"
    elif first_dialogue:
        hook_desc = f"{first_dialogue.character} delivers a jarring line ({first_dialogue.delivery or 'tense'}): {first_dialogue.content}"
    elif first_action:
        hook_desc = f"Immediate visual shock: {first_action.content}"
    else:
        hook_desc = f"{hook_beats[0].content[:120]}"
        
    return score, hook_desc

def analyze_cliffhanger(cand: CandidateWindow) -> Tuple[float, str]:
    """
    Evaluates the final 4.0 seconds of the candidate window.
    Returns (score [0-30], cliffhanger_description).
    """
    tail_limit = max(cand.start_sec, cand.end_sec - 4.5)
    tail_beats = [b for b in cand.beats if b.end_sec >= tail_limit]
    if not tail_beats:
        tail_beats = cand.beats[-2:]
        
    score = 8.0 # Baseline
    cues_found = []
    last_beat = cand.beats[-1]
    last_text = last_beat.content.lower()
    
    for b in tail_beats:
        b_text = b.content.lower()
        
        # Audio / SFX cliffhanger
        if b.beat_type in ["SOUND FX", "SFX"]:
            for kw in CLIFFHANGER_KEYWORDS["audio"]:
                if kw in b_text:
                    score += 6.0
                    cues_found.append(f"sound design swell ({kw})")
                    break
                    
        # Dialogue cutoff / unanswered provocation
        if b.beat_type == "DIALOGUE":
            for kw in CLIFFHANGER_KEYWORDS["dialogue_triggers"]:
                if kw in b_text:
                    score += 5.0
                    cues_found.append(f"unanswered provocation ('{kw}')")
                    break
            if b.content.strip().endswith("?") or b.content.strip().endswith("..."):
                score += 4.0
                cues_found.append("open-ended punctuation")
                
        # Physical cliffhanger
        for kw in CLIFFHANGER_KEYWORDS["actions"]:
            if kw in b_text:
                score += 5.0
                cues_found.append(f"unresolved physical tension ({kw})")
                break

    # If the window ends at the exact end of an episode, natural cliffhanger boost!
    if abs(cand.end_sec - cand.episode.total_duration) < 2.0:
        score += 5.0
        cues_found.append("episode-ending cliffhanger cut")
        
    score = min(30.0, score)
    
    # Generate human-readable cliffhanger description
    if last_beat.beat_type == "DIALOGUE":
        cliff_desc = f"Cuts on {last_beat.character}'s unresolved line: {last_beat.content} leaving the stakes hanging."
    elif last_beat.beat_type in ["SOUND FX", "CAMERA"]:
        cliff_desc = f"Cuts abruptly as {last_beat.content} leaving the consequence unanswered."
    else:
        cliff_desc = f"Freezes on the peak of physical confrontation: {last_beat.content}"
        
    return score, cliff_desc

def analyze_standalone_clarity(cand: CandidateWindow) -> Tuple[float, str]:
    """
    Evaluates how self-contained and clear the emotional stakes are for a stranger.
    Returns (score [0-20], clarity_notes).
    """
    dialogues = [b for b in cand.beats if b.beat_type == "DIALOGUE"]
    all_text = " ".join(b.content for b in cand.beats).lower()
    
    score = 10.0 # Baseline
    
    # Must have dialogue to understand the human drama
    if len(dialogues) >= 2:
        score += 4.0
    elif len(dialogues) == 1:
        score += 2.0
    else:
        score -= 4.0 # Visual only without dialogue often confuses cold viewers on audio/dialogue-driven apps
        
    # Archetype clarity: Clear conflict between 2+ opposing entities
    characters = set(b.character for b in dialogues if b.character)
    if len(characters) >= 2:
        score += 4.0
        
    # High universal clarity markers
    if any(k in all_text for k in ["marry", "wedding", "sister", "husband", "wife", "mother", "father", "kill", "hang", "arrest", "chains"]):
        score += 3.0
        
    # Obscure exposition penalty: mentions of obscure paperwork/distant towns
    if any(k in all_text for k in ["clause 4", "parish registry volume", "boundary line of westshire"]):
        score -= 4.0
        
    score = max(4.0, min(20.0, score))
    
    chars_str = ", ".join(sorted(characters)) if characters else "Visual action"
    clarity_notes = f"Self-contained conflict between {chars_str} with clear primal stakes."
    return score, clarity_notes

def analyze_trope_and_pacing(cand: CandidateWindow) -> Tuple[float, List[str], str]:
    """
    Evaluates microdrama tropes and pacing sweet-spot.
    Returns (score [0-20], identified_tropes, pacing_note).
    """
    score = 10.0
    all_text = " ".join(b.content for b in cand.beats).lower()
    
    detected_tropes = []
    for trope, keywords in TROPES_TAXONOMY.items():
        if any(kw in all_text for kw in keywords):
            detected_tropes.append(trope)
            
    if detected_tropes:
        score += min(6.0, len(detected_tropes) * 2.5)
        
    # Duration sweet spot: 30s - 50s is optimal for TikTok / Reels algorithmic retention
    dur = cand.duration
    if 30.0 <= dur <= 50.0:
        score += 4.0
        pacing_note = f"Optimal duration ({dur:.1f}s) for TikTok/Reels full-watch retention."
    elif 20.0 <= dur < 30.0:
        score += 2.0
        pacing_note = f"Snappy short cut ({dur:.1f}s), high velocity but slightly brief narrative arc."
    else:
        score += 1.0
        pacing_note = f"Extended cut ({dur:.1f}s), rich build-up, requires high viewer engagement."
        
    score = min(20.0, score)
    return score, detected_tropes, pacing_note

def generate_why_it_works(cand: CandidateWindow, hook_score: float, cliff_score: float, tropes: List[str]) -> str:
    """
    Produces a crisp, 1-line rationale for why this promo converts cold users.
    """
    ep_num = cand.episode.ep_num
    lead_trope = tropes[0] if tropes else "High-Stakes Melodrama"
    
    if "Altar Betrayal" in lead_trope:
        return "Universal emotional gut-punch: cold viewers instantly sympathize with the humiliated bride and rage against the treacherous groom."
    elif "Secret Noble" in lead_trope:
        return "High-dopamine rescue fantasy: a scarred outcast steps up to defend Juliana, instantly hooking viewers on the mystery of his true power."
    elif "Sadistic Ordeal" in lead_trope:
        return "Extreme visceral tension: the cruel blackthorn ultimatum forces an agonizing physical sacrifice that commands complete viewer empathy."
    elif "Chains & Public Humiliation" in lead_trope:
        return "Peak indignation: watching Juliana dragged in chains creates an overwhelming urge to see her vindicated, driving immediate app installs."
    elif "Vengeful Retribution" in lead_trope:
        return "Explosive catharsis: the sudden arrival in ducal regalia flips the power dynamic, leaving viewers desperate to watch the villains get crushed."
    else:
        if hook_score >= cliff_score:
            return "Instant thumb-stop confrontation that escalates before cutting at maximum emotional tension, maximizing click-through rate."
        else:
            return "Steadily mounting interpersonal conflict that cuts abruptly at an unresolved ultimatum, compelling viewers to download and unlock."

def evaluate_promo(cand: CandidateWindow) -> Dict[str, Any]:
    """
    Evaluates a candidate window and returns a complete structured promo record.
    """
    hook_score, hook_desc = analyze_hook(cand)
    cliff_score, cliff_desc = analyze_cliffhanger(cand)
    clarity_score, clarity_notes = analyze_standalone_clarity(cand)
    trope_score, tropes, pacing_note = analyze_trope_and_pacing(cand)
    
    total_score = hook_score + cliff_score + clarity_score + trope_score
    why_it_works = generate_why_it_works(cand, hook_score, cliff_score, tropes)
    
    # Classify marketing funnel placement based on narrative tension profile
    if "Vengeful Retribution" in tropes or "Secret Noble" in tropes and total_score >= 80:
        target_funnel = "Catharsis & Power Reversal (BoFu) - LTV & Binge Driver"
    elif cliff_score >= 21.0 and ("Sadistic Ordeal" in tropes or "Chains" in tropes or total_score >= 82):
        target_funnel = "High-Curiosity Cliffhanger (MoFu) - Pay-to-Unlock Driver"
    elif hook_score >= 24.0 and clarity_score >= 15.0:
        target_funnel = "Cold Audience Top-of-Funnel (ToFu) - Viral Stop Rate"
    else:
        target_funnel = "Retargeting / Dramatic Escalation (MoFu)"
        
    return {
        "episode": cand.episode.ep_num,
        "episode_title": cand.episode.ep_title,
        "scene_id": cand.scene.scene_id,
        "scene_heading": cand.scene.heading,
        "start_time": cand.start_time_str,
        "end_time": cand.end_time_str,
        "duration_seconds": round(cand.duration, 2),
        "segments": [{"start": sec_to_time(s[0]), "end": sec_to_time(s[1]), "duration": round(s[1] - s[0], 2)} for s in cand.segments],
        "hook": hook_desc,
        "cliffhanger": cliff_desc,
        "why_it_works": why_it_works,
        "scores": {
            "hook_strength": round(hook_score, 1),
            "cliffhanger_tension": round(cliff_score, 1),
            "standalone_clarity": round(clarity_score, 1),
            "trope_and_pacing": round(trope_score, 1),
            "total_virality_score": round(total_score, 1)
        },
        "target_funnel": target_funnel,
        "identified_tropes": tropes,
        "pacing_note": pacing_note
    }
