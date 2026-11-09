import json
import os
from typing import Dict, Any, List, Optional, Tuple
from src.parser import Episode, Beat, sec_to_time

class PromoVerifier:
    def __init__(self, show_bible: Optional[Dict[str, Any]] = None):
        self.show_bible = show_bible or {}
        self.rejected_log: List[Dict[str, Any]] = []

    def verify_and_trim_candidate(
        self,
        cand: Dict[str, Any],
        episode: Episode,
        min_duration: float = 20.0,
        max_duration: float = 60.0
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Enforces deterministic rules on model proposals:
        1. Looks up beats by ID (no hallucinated timestamps).
        2. Trims dead air before the hook so hook lands in first 3s.
        3. Enforces 20-60s duration strictly.
        4. Inspects post-cut lines for quick tension resolution.
        5. Checks for series spoilers.
        """
        start_id = cand.get("start_beat_id")
        hook_id = cand.get("hook_beat_id", start_id)
        end_id = cand.get("end_beat_id")

        start_beat = episode.get_beat(start_id)
        hook_beat = episode.get_beat(hook_id)
        end_beat = episode.get_beat(end_id)

        # Rule 1: Beat IDs must exist in screenplay
        if not start_beat or not end_beat:
            reason = f"Beat ID lookup failed: start={start_id} ({bool(start_beat)}), end={end_id} ({bool(end_beat)})"
            self._log_rejection(cand, episode.ep_num, "INVALID_BEAT_ID", reason)
            return False, None, reason

        all_beats = episode.all_beats
        try:
            start_idx = next(i for i, b in enumerate(all_beats) if b.beat_id == start_beat.beat_id)
            end_idx = next(i for i, b in enumerate(all_beats) if b.beat_id == end_beat.beat_id)
        except StopIteration:
            reason = "Beat order alignment failed in episode sequence"
            self._log_rejection(cand, episode.ep_num, "BEAT_ALIGNMENT_ERROR", reason)
            return False, None, reason

        if end_idx <= start_idx:
            reason = f"End beat ({end_id}) occurs before or at start beat ({start_id})"
            self._log_rejection(cand, episode.ep_num, "INVALID_BEAT_ORDER", reason)
            return False, None, reason

        # Rule 2: Dead Air Trimmer
        # If there is dead air before the hook beat, trim start forward so hook lands within 3.0s
        trimmed_start_idx = start_idx
        if hook_beat:
            hook_offset = hook_beat.start_sec - all_beats[trimmed_start_idx].start_sec
            if hook_offset > 3.0:
                # Find the latest beat before or at hook_beat such that (hook_beat.start_sec - beat.start_sec) <= 3.0
                for k in range(start_idx, len(all_beats)):
                    if (hook_beat.start_sec - all_beats[k].start_sec) <= 3.0:
                        trimmed_start_idx = k
                        break

        clip_beats = all_beats[trimmed_start_idx:end_idx + 1]
        raw_start_sec = clip_beats[0].start_sec
        raw_end_sec = clip_beats[-1].end_sec
        duration = raw_end_sec - raw_start_sec

        # Rule 3: Duration bounds [20s, 60s]
        if duration < min_duration:
            reason = f"Clip duration ({duration:.1f}s) is below minimum {min_duration}s"
            self._log_rejection(cand, episode.ep_num, "DURATION_TOO_SHORT", reason)
            return False, None, reason

        if duration > max_duration:
            # Attempt to trim end beat backwards to fit within 60s
            fitted = False
            for k in range(len(clip_beats) - 1, 0, -1):
                new_dur = clip_beats[k].end_sec - raw_start_sec
                if min_duration <= new_dur <= max_duration:
                    clip_beats = clip_beats[:k + 1]
                    raw_end_sec = clip_beats[-1].end_sec
                    duration = new_dur
                    fitted = True
                    break
            if not fitted:
                reason = f"Clip duration ({duration:.1f}s) exceeds maximum {max_duration}s and cannot be safely trimmed"
                self._log_rejection(cand, episode.ep_num, "DURATION_TOO_LONG", reason)
                return False, None, reason

        # Rule 4: Post-Cut Resolution Check
        # Check the 2 beats immediately following the cut
        post_cut_idx = trimmed_start_idx + len(clip_beats)
        if post_cut_idx < len(all_beats):
            next_beats = all_beats[post_cut_idx:post_cut_idx + 2]
            next_text = " ".join(b.content.lower() for b in next_beats)
            resolved_markers = ["laughs warmly", "smiles relieved", "sigh of relief", "it was only a joke", "embraces tenderly", "safely home"]
            if any(m in next_text for m in resolved_markers):
                reason = f"Tension resolves immediately after cut ({next_text[:60]}...); false cliffhanger"
                self._log_rejection(cand, episode.ep_num, "POST_CUT_TENSION_RESOLVED", reason)
                return False, None, reason

        # Rule 5: Spoiler Check
        clip_text = " ".join(b.content.lower() for b in clip_beats)
        if episode.ep_num < 40:
            if "duke of ashburn" in clip_text or "true duke" in clip_text or "regalia" in clip_text:
                reason = "Premature spoiler of Alexander's true Duke identity in early episode promo"
                self._log_rejection(cand, episode.ep_num, "PREMATURE_SERIES_SPOILER", reason)
                return False, None, reason

        verified_promo = {
            "episode": episode.ep_num,
            "episode_title": episode.ep_title,
            "scene_id": clip_beats[0].beat_id.split("_")[0],
            "start_time": sec_to_time(raw_start_sec),
            "end_time": sec_to_time(raw_end_sec),
            "start_sec": round(raw_start_sec, 2),
            "end_sec": round(raw_end_sec, 2),
            "duration_seconds": round(duration, 2),
            "start_beat_id": clip_beats[0].beat_id,
            "end_beat_id": clip_beats[-1].beat_id,
            "hook_beat_id": hook_beat.beat_id if hook_beat else clip_beats[0].beat_id,
            "beats_count": len(clip_beats),
            "hook_summary": cand.get("hook_summary", ""),
            "cliffhanger_summary": cand.get("cliffhanger_summary", ""),
            "why_it_works": cand.get("why_it_works", ""),
            "clip_beats": clip_beats
        }

        return True, verified_promo, None

    def _log_rejection(self, cand: Dict[str, Any], ep_num: int, reason_code: str, details: str):
        self.rejected_log.append({
            "episode": ep_num,
            "start_beat_id": cand.get("start_beat_id"),
            "end_beat_id": cand.get("end_beat_id"),
            "reason_code": reason_code,
            "details": details
        })

    def save_rejected(self, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_rejected": len(self.rejected_log),
                "rejections": self.rejected_log
            }, f, indent=2)
