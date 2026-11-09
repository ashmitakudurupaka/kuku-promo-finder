from typing import Dict, Any, List
from src.parser import Beat

class QualityChecker:
    """
    Automated Failure Mode Detection & Quality Audit Engine.
    Identifies false positives, context traps, and pacing flaws in promo candidates.
    """
    
    @staticmethod
    def audit_promo(promo: Dict[str, Any], beats: List[Beat]) -> Dict[str, Any]:
        flags = []
        severity = "PASS"
        recommendations = []
        
        # 1. Check for Silent / Visual-Only Trap
        dialogue_beats = [b for b in beats if b.beat_type == "DIALOGUE"]
        total_dialogue_words = sum(len(b.content.split()) for b in dialogue_beats)
        dialogue_density = total_dialogue_words / max(1.0, promo["duration_seconds"])
        
        if len(dialogue_beats) == 0:
            flags.append({
                "code": "FAIL_SILENT_VISUAL",
                "label": "Visual-Only Dead Air Risk",
                "description": "Promo contains zero dialogue lines. On mobile feeds (TikTok/Reels), silent clips without text overlays suffer high drop-off unless visual action is extraordinarily kinetic.",
                "severity": "HIGH"
            })
            severity = "FAIL"
            recommendations.append("Add dialogue overlay or pick a window with verbal confrontation.")
        elif dialogue_density < 0.8:
            flags.append({
                "code": "WARN_LOW_DIALOGUE_DENSITY",
                "label": "Sparse Dialogue / Slow Cadence",
                "description": f"Dialogue cadence is low ({dialogue_density:.2f} words/sec). May feel sluggish to scrolling viewers.",
                "severity": "MEDIUM"
            })
            if severity != "FAIL":
                severity = "WARN"
            recommendations.append("Ensure background score or kinetic cinematography bridges the dialogue pauses.")

        # 2. Check for Lore / Exposition Trap
        all_text = " ".join(b.content for b in beats)
        lore_proper_nouns = [
            "Father Thomas", "Lord Sterling", "Bishop", "High Priest", 
            "Westshire", "Archive", "Council Reprieve", "Volume 4", "Decree 12"
        ]
        found_lore = [n for n in lore_proper_nouns if n.lower() in all_text.lower()]
        if len(found_lore) >= 2 and promo["episode"] > 20:
            flags.append({
                "code": "WARN_LORE_DEPENDENCY",
                "label": "Context / Lore Dependency",
                "description": f"Contains complex serialized references ({', '.join(found_lore)}) that require prior episode knowledge. Confuses cold audiences.",
                "severity": "MEDIUM"
            })
            if severity != "FAIL":
                severity = "WARN"
            recommendations.append("Tag for Retargeting (MoFu/BoFu) only; do NOT run as Cold Acquisition ad.")

        # 3. Check for Mid-Sentence Pacing Clipping
        last_beat = beats[-1]
        if last_beat.beat_type == "DIALOGUE":
            last_text = last_beat.content.strip().strip('"').strip("'")
            if not last_text.endswith((".", "!", "?", "...", "—", "-")):
                flags.append({
                    "code": "WARN_MID_SENTENCE_CUT",
                    "label": "Mid-Sentence Dialogue Truncation",
                    "description": "Clip ends mid-phrase without punctuation boundary, creating an unintentional grammatical cut rather than a planned narrative cliffhanger.",
                    "severity": "MEDIUM"
                })
                if severity != "FAIL":
                    severity = "WARN"
                recommendations.append("Extend end timestamp by 1.5s to capture the sentence completion.")

        # 4. Check for False Cliffhanger (Emotional De-escalation)
        last_3_beats = beats[-3:] if len(beats) >= 3 else beats
        tail_text = " ".join(b.content for b in last_3_beats).lower()
        peaceful_markers = ["safe for now", "peace at last", "breathes a sigh of relief", "tender embrace", "nods softly in agreement"]
        if any(m in tail_text for m in peaceful_markers):
            flags.append({
                "code": "FAIL_FALSE_CLIFFHANGER",
                "label": "False Cliffhanger (Resolved Tension)",
                "description": "Scene concludes on an emotional reconciliation or sigh of relief, reducing urgency to click the ad.",
                "severity": "HIGH"
            })
            severity = "FAIL"
            recommendations.append("Cut 8 seconds earlier at the height of the argument before the resolution.")

        # 5. Check for First 3s Hook Presence
        first_beat = beats[0]
        if first_beat.beat_type == "CAMERA" and any(k in first_beat.content.lower() for k in ["slowly", "distant", "peaceful", "empty room"]):
            flags.append({
                "code": "WARN_SLOW_HOOK",
                "label": "Slow Visual Ramp-Up",
                "description": "Opening camera cue is atmospheric rather than jarring. May lose scrolling viewers in seconds 0-2.",
                "severity": "LOW"
            })
            if severity == "PASS":
                severity = "WARN"
            recommendations.append("Trim opening 1-2 seconds to jump directly into the character confrontation.")

        return {
            "status": severity,
            "flags_count": len(flags),
            "flags": flags,
            "recommendations": recommendations,
            "human_in_the_loop_needed": severity != "PASS"
        }
