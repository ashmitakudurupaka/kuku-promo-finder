import os
import json
import re
import urllib.request
from typing import Dict, Any, List, Optional
from src.parser import Episode, Beat

# Default configuration (OpenAI-compatible)
DEFAULT_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

def load_env_file(env_path: str = ".env"):
    """Loads environment variables from a .env file if present."""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v

# Auto-load .env
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_env_file(env_file)

def get_active_model_config() -> Dict[str, str]:
    return {
        "api_base": os.getenv("OPENAI_API_BASE", DEFAULT_API_BASE).rstrip("/"),
        "api_key": os.getenv("OPENAI_API_KEY", DEFAULT_API_KEY),
        "model": os.getenv("MODEL_NAME", DEFAULT_MODEL)
    }

def call_openai_compatible(messages: List[Dict[str, str]], response_json: bool = True, temperature: float = 0.2) -> Optional[Dict[str, Any]]:
    """Calls any OpenAI-compatible API endpoint (OpenAI, Groq, OpenRouter, Gemini, Ollama)."""
    cfg = get_active_model_config()
    api_key = cfg["api_key"]
    if not api_key:
        return None  # Triggers local fallback engine

    endpoint = f"{cfg['api_base']}/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            if response_json:
                return json.loads(content)
            return {"content": content}
    except Exception as e:
        print(f"⚠️ OpenAI-compatible API call failed ({e}). Falling back to local heuristic judge.")
        return None

# ==========================================================
# 1. Candidate Generation by Beat IDs
# ==========================================================
def propose_candidates_llm(episode: Episode, show_bible: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Prompts the model to select candidate promo spans strictly using beat IDs.
    Returns list of dicts:
    { "start_beat_id": "...", "hook_beat_id": "...", "end_beat_id": "...", "hook_summary": "...", "cliffhanger_summary": "...", "why_it_works": "..." }
    """
    beats_repr = []
    for b in episode.all_beats:
        if b.beat_type == "DIALOGUE":
            beats_repr.append(f"{b.beat_id}: [{b.character} ({b.delivery or 'neutral'})]: \"{b.content}\"")
        else:
            beats_repr.append(f"{b.beat_id}: [{b.beat_type}]: {b.content}")

    # If API key available, query the LLM
    cfg = get_active_model_config()
    if cfg["api_key"]:
        system_prompt = (
            "You are an expert short-form performance marketing editor for microdramas (ReelShort, DramaBox, Kuku). "
            "Your task is to identify 2-3 high-converting 20 to 60-second promo clips in the screenplay. "
            "CRITICAL RULE: Choose start_beat_id, hook_beat_id, and end_beat_id from the provided beat IDs ONLY. "
            "Do NOT invent timestamps. Code will look up timestamps. "
            "A promo must open on a thumb-stop hook (slap, confrontation, betrayal) in the first 3s, and cut on an unresolved cliffhanger before consequences resolve."
        )
        user_prompt = f"Episode {episode.ep_num} Screenplay Beats:\n" + "\n".join(beats_repr[:80]) + "\n\nReturn JSON: {\"candidates\": [{\"start_beat_id\": \"...\", \"hook_beat_id\": \"...\", \"end_beat_id\": \"...\", \"hook_summary\": \"...\", \"cliffhanger_summary\": \"...\", \"why_it_works\": \"...\"}]}"

        resp = call_openai_compatible([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        if resp and "candidates" in resp:
            return resp["candidates"]

    # Local Heuristic Proposer (No API Key Fallback)
    # Finds peak conflict windows across the whole episode (early, mid, climax)
    from src.segmenter import generate_candidate_windows
    from src.scoring import analyze_hook, analyze_cliffhanger

    windows = generate_candidate_windows(episode, min_duration=20.0, max_duration=60.0)
    
    # Score windows rapidly to propose diverse candidates across the episode
    scored_windows = []
    for w in windows:
        h_score, h_desc = analyze_hook(w)
        c_score, c_desc = analyze_cliffhanger(w)
        total_p = h_score + c_score
        # Bonus for climax windows ending near episode duration
        if abs(w.end_sec - episode.total_duration) < 3.0:
            total_p += 10.0
        scored_windows.append((total_p, w, h_desc, c_desc))

    # Sort descending by conflict potential
    scored_windows.sort(key=lambda x: x[0], reverse=True)

    proposals = []
    seen_spans = []

    for tot, w, h_desc, c_desc in scored_windows:
        # Avoid near-identical duplicate spans
        overlap = any(abs(w.start_sec - s) < 5.0 and abs(w.end_sec - e) < 5.0 for s, e in seen_spans)
        if overlap:
            continue

        hook_beat = next((b for b in w.beats if b.beat_type == "DIALOGUE" or any(k in b.content.lower() for k in ["slap", "shatter", "grab", "kneel", "marry"])), w.beats[0])
        proposals.append({
            "start_beat_id": w.beats[0].beat_id,
            "hook_beat_id": hook_beat.beat_id,
            "end_beat_id": w.beats[-1].beat_id,
            "hook_summary": h_desc,
            "cliffhanger_summary": c_desc,
            "why_it_works": "High-velocity emotional confrontation that cuts before resolution."
        })
        seen_spans.append((w.start_sec, w.end_sec))
        if len(proposals) >= 8:
            break

    return proposals

# ==========================================================
# 2. Cold-Viewer Judge
# ==========================================================
def cold_viewer_judge_llm(clip_text: str) -> Dict[str, Any]:
    """
    A second model call that sees ONLY the raw clip text (zero show bible, zero episode number).
    Simulates a scrolling stranger on TikTok/Instagram Reels.
    Returns:
    {
      "character_clarity_score": 1-5,
      "hook_stop_rate": 1-5,
      "cliffhanger_urgency": 1-5,
      "standalone_comprehension": 1-5,
      "verdict": "PASS" | "CONFUSING" | "WEAK_HOOK" | "RESOLVED_TOO_FAST",
      "critique": "..."
    }
    """
    cfg = get_active_model_config()
    if cfg["api_key"]:
        system_prompt = (
            "You are a cold social media user scrolling TikTok / Instagram Reels. "
            "You have NEVER seen this show before and know zero backstory. "
            "Read ONLY this clip transcript and evaluate: "
            "1. Can you understand who is who and what the immediate stakes are? (1-5)\n"
            "2. Would the first 3 seconds stop your thumb from scrolling? (1-5)\n"
            "3. Does the ending make you urgently want to unlock the next episode? (1-5)\n"
            "4. Does it make complete sense on its own without needing 10 episodes of lore? (1-5)\n"
            "Return JSON: {\"character_clarity_score\": int, \"hook_stop_rate\": int, \"cliffhanger_urgency\": int, \"standalone_comprehension\": int, \"verdict\": \"PASS\"|\"CONFUSING\"|\"WEAK_HOOK\"|\"RESOLVED_TOO_FAST\", \"critique\": \"one sentence critique\"}"
        )
        resp = call_openai_compatible([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Clip Transcript:\n\n{clip_text}"}
        ])
        if resp and "verdict" in resp:
            return resp

    # Deterministic Cold-Viewer Fallback
    text_lower = clip_text.lower()
    clarity = 4
    hook = 4
    cliff = 4
    standalone = 4
    critique = "Clear archetypal stakes with immediate emotional conflict."
    verdict = "PASS"

    # Confusing lore markers
    if any(k in text_lower for k in ["lord sterling", "father thomas", "archive volume", "decree"]):
        clarity -= 2
        standalone -= 2
        critique = "Mentions serialized political entities that confuse a cold viewer."
        verdict = "CONFUSING"

    # Weak hook (slow camera or passive dialogue)
    if text_lower.startswith("[camera]: symmetrical") or text_lower.startswith("[camera]: wide"):
        hook -= 2
        critique = "Opening camera beat is too slow to stop scrolling thumbs."
        verdict = "WEAK_HOOK"

    # Resolved tension
    if any(k in text_lower[-120:] for k in ["safe", "thank you", "smiles warmly", "nodded softly"]):
        cliff -= 2
        critique = "The scene resolved peacefully before cutting, killing the cliffhanger."
        verdict = "RESOLVED_TOO_FAST"

    return {
        "character_clarity_score": max(1, clarity),
        "hook_stop_rate": max(1, hook),
        "cliffhanger_urgency": max(1, cliff),
        "standalone_comprehension": max(1, standalone),
        "verdict": verdict,
        "critique": critique
    }
