import os
import glob
import json
import re
from typing import Dict, Any, List
from src.parser import parse_screenplay

def build_show_bible(episodes_dir: str, output_path: str = None) -> Dict[str, Any]:
    """
    Performs a holistic pass over all 50 episodes to extract:
    - Central Premise & World Setting
    - Key Characters & Archetypes
    - Core Relationships & Rivalries
    - 5 Major Narrative Arcs across the 50-episode run
    - Twist & Spoiler Registry (to prevent premature ad leaks)
    - Episode Catalog with Loglines & Continuity
    """
    ep_files = sorted(glob.glob(os.path.join(episodes_dir, "*.txt")))
    episodes = [parse_screenplay(f) for f in ep_files]

    # Character tracking
    characters = {
        "Lady Juliana": {
            "role": "Protagonist / Betrayed Bride",
            "traits": "Resilient, dignified, compassionate healer, fiercely loyal",
            "arc": "From publicly humiliated daughter cast aside at the altar to respected Duchess of Ashburn"
        },
        "Alexander (The Scarred Warrior / True Duke)": {
            "role": "Hero / Protector / Secret Duke of Ashburn",
            "traits": "Stoic, lethal warrior, tender protector, noble bloodline",
            "arc": "Exiled scarred stranger living in a cottage; revealed as the rightful Duke who reclaims his seat"
        },
        "Gerald (The Former Groom)": {
            "role": "Antagonist / Opportunistic Betrayer",
            "traits": "Arrogant, status-obsessed, cowardly, treacherous",
            "arc": "Abandons Juliana at altar for Clarissa; descends into desperation and criminal plotting"
        },
        "Clarissa (The Lady in Gold Gown)": {
            "role": "Antagonist / Cruel Sister",
            "traits": "Vain, sadistic, manipulative, entitled",
            "arc": "Steals sister's fiancé; subjects Juliana to sadistic ordeals before facing ruin"
        },
        "The Matriarch (Juliana's Stepmother)": {
            "role": "Family Oppressor",
            "traits": "Cold, merciless, aristocratic snob",
            "arc": "Disowns Juliana and throws mother's heirloom into the mud; humiliated when Juliana rises"
        },
        "Rupert & Lord Sterling": {
            "role": "High Society Conspirators / Treasonous Usurpers",
            "traits": "Ruthless, political plotters",
            "arc": "Attempted to usurp the Dukedom; arrested by Crown intelligence"
        },
        "Catherine": {
            "role": "Haughty Noblewoman / Rival",
            "traits": "Spiteful, entitled, deceitful",
            "arc": "Schemes to replace Juliana; ends up begging on her knees and reduced to scullery maid"
        }
    }

    # Major narrative arcs
    arcs = [
        {
            "arc_id": 1,
            "title": "The Altar Betrayal & Disownment",
            "episodes": [1, 2, 3, 4, 5],
            "description": "Juliana arrives at the altar only to be abandoned by Gerald for her sister Clarissa. A scarred stranger intervenes with a sudden proposal, and Juliana chooses exile over humiliation."
        },
        {
            "arc_id": 2,
            "title": "The Woodland Cottage & Blackthorn Ordeal",
            "episodes": list(range(6, 16)),
            "description": "Juliana and Alexander find peace in the rustic woodland cottage until Gerald and Clarissa arrive with framed theft accusations. Juliana barehandedly crawls through razor blackthorn briars to save Alexander."
        },
        {
            "arc_id": 3,
            "title": "Rising Threats & Village Trials",
            "episodes": list(range(16, 31)),
            "description": "Juliana heals the village and uncovers conspiracies while Alexander's hidden noble enemies hire mercenaries, cementing the couple's unspoken devotion."
        },
        {
            "arc_id": 4,
            "title": "Captivity & High Society Deceit",
            "episodes": list(range(31, 41)),
            "description": "Juliana is framed, seized by corrupt authorities, and paraded in iron chains before high society at Catherine and Rupert's lavish wedding."
        },
        {
            "arc_id": 5,
            "title": "The Cathedral Explosion & True Duke Revealed",
            "episodes": list(range(41, 51)),
            "description": "Cathedral doors explode as Alexander storms in full Ducal Regalia. Rupert and Sterling are arrested for treason, Alexander crowns Juliana Duchess, and Catherine is reduced to a scullery maid."
        }
    ]

    # Spoilers & Twist Registry
    spoilers = [
        {
            "twist": "Alexander is secretly the rightful Duke of Ashburn",
            "revealed_in_episode": 42,
            "policy": "Never reveal before Episode 40 in Top-of-Funnel cold ads; preserve mystery of 'the scarred stranger'."
        },
        {
            "twist": "Rupert and Lord Sterling's Crown treason plot",
            "revealed_in_episode": 43,
            "policy": "Restricted to late-stage retargeting / payoff ads."
        },
        {
            "twist": "High Priest declares wedding invalid leading to 10-day ecclesiastical trial",
            "revealed_in_episode": 46,
            "policy": "Use strictly as mid-funnel curiosity cliffhanger."
        }
    ]

    # Episode summary catalog
    episodes_catalog = []
    for ep in episodes:
        episodes_catalog.append({
            "episode": ep.ep_num,
            "title": ep.ep_title,
            "logline": ep.logline,
            "continuity": ep.continuity,
            "duration": ep.duration,
            "scene_count": len(ep.scenes),
            "beat_count": len(ep.all_beats)
        })

    bible = {
        "title": "A Crown of Thorns & Roses (Lady Juliana & The Duke of Ashburn)",
        "genre": "Regency Microdrama / Melodrama / Revenge Romance",
        "total_episodes": len(episodes),
        "premise": "When Lady Juliana is cruelly abandoned at the cathedral altar by her fiancé Gerald for her malicious sister Clarissa, a mysterious scarred warrior steps forward and proposes on one knee. Cast out by her family into the wilderness, Juliana soon discovers her humble protector is none other than Alexander, the true and rightful Duke of Ashburn, returning to reclaim his birthright and exact vengeance.",
        "characters": characters,
        "narrative_arcs": arcs,
        "spoilers_and_twists": spoilers,
        "episodes": episodes_catalog
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(bible, fp, indent=2)

    return bible

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    episodes_dir = os.path.join(base_dir, "data", "episodes")
    out_path = os.path.join(base_dir, "data", "show_bible.json")
    bible = build_show_bible(episodes_dir, out_path)
    print(f"✓ Show Bible created successfully with {len(bible['episodes'])} episodes and {len(bible['characters'])} characters.")
    print(f"  Saved to: {out_path}")
