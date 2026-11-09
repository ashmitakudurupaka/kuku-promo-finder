import re
import os
from typing import List, Dict, Any, Optional

def time_to_sec(t_str: str) -> float:
    """Converts MM:SS.SS or HH:MM:SS.SS to float seconds."""
    t_str = t_str.strip().strip("()")
    parts = t_str.split(":")
    if len(parts) == 2:
        m, s = parts
        return float(m) * 60.0 + float(s)
    elif len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600.0 + float(m) * 60.0 + float(s)
    return float(t_str)

def sec_to_time(sec: float) -> str:
    """Converts float seconds to MM:SS.SS format."""
    m = int(sec // 60)
    s = sec % 60
    return f"{m:02d}:{s:05.2f}"

class Beat:
    def __init__(self, beat_id: str, beat_type: str, character: Optional[str], delivery: Optional[str],
                 start_sec: float, end_sec: float, content: str, line_num: int = 0):
        self.beat_id = beat_id  # e.g., ep01_b014
        self.beat_type = beat_type  # CAMERA, ACTION, DIALOGUE, SOUND FX
        self.character = character
        self.delivery = delivery
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.content = content.strip()
        self.line_num = line_num

    @property
    def start(self) -> str:
        return sec_to_time(self.start_sec)

    @property
    def end(self) -> str:
        return sec_to_time(self.end_sec)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_sec - self.start_sec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.beat_id,
            "type": self.beat_type,
            "character": self.character,
            "delivery": self.delivery,
            "start": self.start,
            "end": self.end,
            "start_sec": round(self.start_sec, 2),
            "end_sec": round(self.end_sec, 2),
            "duration": round(self.duration, 2),
            "content": self.content
        }

class Scene:
    def __init__(self, scene_id: str, heading: str, start_sec: float, end_sec: float):
        self.scene_id = scene_id
        self.heading = heading
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.beats: List[Beat] = []

    @property
    def start(self) -> str:
        return sec_to_time(self.start_sec)

    @property
    def end(self) -> str:
        return sec_to_time(self.end_sec)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_sec - self.start_sec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "heading": self.heading,
            "start": sec_to_time(self.start_sec),
            "end": sec_to_time(self.end_sec),
            "start_sec": round(self.start_sec, 2),
            "end_sec": round(self.end_sec, 2),
            "duration": round(self.duration, 2),
            "beats": [b.to_dict() for b in self.beats]
        }

class Episode:
    def __init__(self, ep_num: int, ep_title: str, logline: str, continuity: str, file_path: str):
        self.ep_num = ep_num
        self.ep_title = ep_title
        self.logline = logline
        self.continuity = continuity
        self.file_path = file_path
        self.scenes: List[Scene] = []
        self.beat_map: Dict[str, Beat] = {}

    @property
    def all_beats(self) -> List[Beat]:
        beats = []
        for s in self.scenes:
            beats.extend(s.beats)
        return beats

    @property
    def total_duration(self) -> float:
        if not self.scenes:
            return 0.0
        return max(s.end_sec for s in self.scenes)

    @property
    def duration(self) -> str:
        return sec_to_time(self.total_duration)

    def get_beat(self, beat_id: str) -> Optional[Beat]:
        return self.beat_map.get(beat_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_number": self.ep_num,
            "title": self.ep_title,
            "logline": self.logline,
            "continuity": self.continuity,
            "duration": self.duration,
            "total_duration_sec": round(self.total_duration, 2),
            "scenes": [s.to_dict() for s in self.scenes]
        }

def parse_screenplay(file_path: str) -> Episode:
    """
    Parses a microdrama episode script text file into structured objects.
    Tolerant of formatting variations (uppercase/lowercase headers, irregular line breaks).
    Every beat is assigned an immutable ID: ep{num}_b{idx}.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # Episode metadata
    ep_num_m = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
    ep_num = int(ep_num_m.group(1)) if ep_num_m else 0

    logline_m = re.search(r"EPISODE LOGLINE:\s*(.+?)(?=\n[A-Z\s]+:|\n---|\Z)", text, re.IGNORECASE | re.DOTALL)
    logline = logline_m.group(1).strip() if logline_m else ""

    cont_m = re.search(r"CONTINUITY NOTES:\s*(.+?)(?=\n[A-Z\s]+:|\n---|\Z)", text, re.IGNORECASE | re.DOTALL)
    continuity = cont_m.group(1).strip() if cont_m else ""

    base_name = os.path.basename(file_path)
    title = base_name.replace(".txt", "")

    episode = Episode(ep_num=ep_num, ep_title=title, logline=logline, continuity=continuity, file_path=file_path)

    script_body = text
    if "--- SCRIPT START ---" in text:
        script_body = text.split("--- SCRIPT START ---")[1]
    if "--- SCRIPT END ---" in script_body:
        script_body = script_body.split("--- SCRIPT END ---")[0]

    # Split by SCENE headers
    scene_blocks = re.split(r"\n(?=SCENE\s+\d+)", script_body.strip(), flags=re.IGNORECASE)

    global_beat_idx = 0

    for block in scene_blocks:
        block = block.strip()
        if not block:
            continue
        sc_header_m = re.match(r"SCENE\s+(\d+)", block, re.IGNORECASE)
        if not sc_header_m:
            continue
        scene_id = f"SCENE {sc_header_m.group(1)}"

        heading_m = re.search(r"Scene heading:\s*(.+?)\n", block, re.IGNORECASE)
        heading = heading_m.group(1).strip() if heading_m else "UNKNOWN HEADING"

        start_m = re.search(r"Scene start:\s*([0-9:.]+)", block, re.IGNORECASE)
        end_m = re.search(r"Scene end:\s*([0-9:.]+)", block, re.IGNORECASE)

        start_sec = time_to_sec(start_m.group(1)) if start_m else 0.0
        end_sec = time_to_sec(end_m.group(1)) if end_m else 0.0

        scene = Scene(scene_id=scene_id, heading=heading, start_sec=start_sec, end_sec=end_sec)

        beat_pattern = re.compile(
            r"\*\*([A-Z0-9_\s\.\-\'\/\&]+?)(?:\s*\((.*?)\))?:\*\*\s*\n"
            r"Start:\s*\(([0-9:.]+)\)\s*\|\s*End:\s*\(([0-9:.]+)\)\s*\n"
            r"(.*?)(?=\n\*\*[A-Z0-9_\s\.\-\'\/\&]+?(?:\s*\(.*?\))?:\*\*|\Z)",
            re.DOTALL | re.IGNORECASE
        )

        for bm in beat_pattern.finditer(block):
            tag = bm.group(1).strip().upper()
            parenthetical = bm.group(2).strip() if bm.group(2) else None
            b_start = time_to_sec(bm.group(3))
            b_end = time_to_sec(bm.group(4))
            content = bm.group(5).strip()

            global_beat_idx += 1
            beat_id = f"ep{ep_num:02d}_b{global_beat_idx:03d}"

            if tag in ["CAMERA", "ACTION", "SOUND FX", "SFX"]:
                beat_type = tag
                character = None
                delivery = None
            else:
                beat_type = "DIALOGUE"
                character = bm.group(1).strip()
                delivery = parenthetical

            beat = Beat(
                beat_id=beat_id,
                beat_type=beat_type,
                character=character,
                delivery=delivery,
                start_sec=b_start,
                end_sec=b_end,
                content=content
            )
            scene.beats.append(beat)
            episode.beat_map[beat_id] = beat

        if scene.end_sec <= scene.start_sec and scene.beats:
            scene.end_sec = max(b.end_sec for b in scene.beats)

        episode.scenes.append(scene)

    return episode
