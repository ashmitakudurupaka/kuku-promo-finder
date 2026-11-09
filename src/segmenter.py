import re
from typing import List, Dict, Any, Tuple
from src.parser import Episode, Scene, Beat, sec_to_time

# High-impact hook cues
HOOK_KEYWORDS = {
    "action": [
        "slap", "shatter", "grab", "kneel", "chains", "explosion", "smoke", 
        "burst", "thrust", "dagger", "sword", "tear", "rip", "choke", "gasp", 
        "drop", "fall", "shove", "slam", "seize", "arrest", "drag", "whip"
    ],
    "dialogue": [
        "marrying", "sister", "betrayal", "worthless", "bastard", "divorce", 
        "not anymore", "turn around", "leave", "hang", "kill", "die", "beg", 
        "scullery", "duke", "traitor", "treason", "imposter", "who are you",
        "no value", "maid", "knees", "propose", "wife", "husband"
    ],
    "delivery": [
        "cold", "commanding", "vicious", "cruel", "furious", "trembling", 
        "heartbroken", "gloating", "smug", "desperate", "raw", "scornful", 
        "arrogant", "shocked", "mocking", "venomous", "menacing", "lethal"
    ]
}

# Cliffhanger cues
CLIFFHANGER_KEYWORDS = {
    "audio": [
        "drone swells", "cliffhanger", "cut to black", "abrupt cut", "silence", 
        "crescendo", "drone", "ominous", "shock"
    ],
    "dialogue_triggers": [
        "or what", "unless", "who are you", "what have you done", "never", 
        "look at me", "you will pay", "tell me", "sign it", "choose", "answer me",
        "guilty", "arrest them", "invalid", "too late"
    ],
    "actions": [
        "knuckles whitening", "tears harden", "defiance", "blade", "freeze", 
        "stare down", "gasps", "bursts into", "unveil", "proclaim", "chains"
    ]
}

class CandidateWindow:
    def __init__(self, episode: Episode, scene: Scene, start_beat_idx: int, end_beat_idx: int, 
                 segments: List[Tuple[float, float]] = None):
        self.episode = episode
        self.scene = scene
        self.start_beat_idx = start_beat_idx
        self.end_beat_idx = end_beat_idx
        self.beats: List[Beat] = scene.beats[start_beat_idx:end_beat_idx + 1]
        
        if segments:
            self.segments = segments
        else:
            self.segments = [(self.beats[0].start_sec, self.beats[-1].end_sec)]
            
    @property
    def start_sec(self) -> float:
        return self.segments[0][0]
        
    @property
    def end_sec(self) -> float:
        return self.segments[-1][1]
        
    @property
    def duration(self) -> float:
        return sum(seg_end - seg_start for seg_start, seg_end in self.segments)
        
    @property
    def start_time_str(self) -> str:
        return sec_to_time(self.start_sec)
        
    @property
    def end_time_str(self) -> str:
        return sec_to_time(self.end_sec)

def generate_candidate_windows(episode: Episode, min_duration: float = 20.0, max_duration: float = 60.0) -> List[CandidateWindow]:
    """
    Generates contiguous candidate promo windows within each scene of an episode
    that strictly fall between min_duration and max_duration seconds.
    """
    candidates = []
    
    for scene in episode.scenes:
        n_beats = len(scene.beats)
        if n_beats < 2:
            continue
            
        for i in range(n_beats):
            start_beat = scene.beats[i]
            
            # Optimization: Skip starting points that are purely atmospheric camera drift with no hook potential
            if start_beat.beat_type == "CAMERA" and any(k in start_beat.content.lower() for k in ["symmetrical", "empty", "slow tracking", "distant"]):
                # Allow only if next beat happens within 2s
                if i + 1 < n_beats and (scene.beats[i+1].start_sec - start_beat.start_sec) > 3.0:
                    continue
                    
            for j in range(i + 1, n_beats):
                end_beat = scene.beats[j]
                dur = end_beat.end_sec - start_beat.start_sec
                
                if dur < min_duration:
                    continue
                if dur > max_duration:
                    break  # Since beats are chronological, further beats will only exceed max_duration
                    
                cand = CandidateWindow(episode=episode, scene=scene, start_beat_idx=i, end_beat_idx=j)
                candidates.append(cand)
                
    return candidates
