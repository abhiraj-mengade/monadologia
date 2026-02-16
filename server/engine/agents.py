"""
agents.py — Agent Model & Personalities

Each agent is a Leibnizian monad — a self-contained unit of reality
that reflects the entire building from their own perspective.
Once you enter The Monad, you live here now. There is no escape function.
"""

from __future__ import annotations
import uuid
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Personality(str, Enum):
    SOCIAL_BUTTERFLY = "social_butterfly"
    SCHEMER = "schemer"
    DRAMA_QUEEN = "drama_queen"
    NERD = "nerd"
    CHAOS_GREMLIN = "chaos_gremlin"
    CONSPIRACY_THEORIST = "conspiracy_theorist"


class Mood(str, Enum):
    HAPPY = "happy"
    BORED = "bored"
    EXCITED = "excited"
    SUSPICIOUS = "suspicious"
    ANXIOUS = "anxious"
    CHAOTIC = "chaotic"
    CHILL = "chill"
    SCHEMING = "scheming"
    INSPIRED = "inspired"
    DRAMATIC = "dramatic"


# Base stat profiles per personality — {charisma, creativity, drama, purity, chaos}
PERSONALITY_STATS: Dict[Personality, Dict[str, int]] = {
    Personality.SOCIAL_BUTTERFLY:    {"charisma": 8, "creativity": 5, "drama": 6, "purity": 4, "chaos": 3},
    Personality.SCHEMER:             {"charisma": 6, "creativity": 8, "drama": 5, "purity": 3, "chaos": 5},
    Personality.DRAMA_QUEEN:         {"charisma": 7, "creativity": 6, "drama": 9, "purity": 2, "chaos": 6},
    Personality.NERD:                {"charisma": 3, "creativity": 7, "drama": 2, "purity": 9, "chaos": 1},
    Personality.CHAOS_GREMLIN:       {"charisma": 5, "creativity": 7, "drama": 7, "purity": 1, "chaos": 9},
    Personality.CONSPIRACY_THEORIST: {"charisma": 4, "creativity": 9, "drama": 8, "purity": 2, "chaos": 7},
}

# Personality → default mood mapping
PERSONALITY_DEFAULT_MOOD: Dict[Personality, Mood] = {
    Personality.SOCIAL_BUTTERFLY:    Mood.HAPPY,
    Personality.SCHEMER:             Mood.SCHEMING,
    Personality.DRAMA_QUEEN:         Mood.DRAMATIC,
    Personality.NERD:                Mood.CHILL,
    Personality.CHAOS_GREMLIN:       Mood.CHAOTIC,
    Personality.CONSPIRACY_THEORIST: Mood.SUSPICIOUS,
}


@dataclass
class Relationship:
    target_id: str
    affinity: int = 0        # -100 (nemesis) to +100 (soulmate)
    interactions: int = 0
    history: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.affinity >= 75:
            return "bestie"
        elif self.affinity >= 40:
            return "friend"
        elif self.affinity >= 10:
            return "acquaintance"
        elif self.affinity >= -10:
            return "neutral"
        elif self.affinity >= -40:
            return "annoyed"
        elif self.affinity >= -75:
            return "rival"
        else:
            return "nemesis"


@dataclass
class Agent:
    id: str
    name: str
    personality: Personality
    stats: Dict[str, int]
    mood: Mood
    location: str = "lobby"
    floor: str = "lobby"
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    clout: int = 0
    func_tokens: int = 100  # Starting balance
    api_key: str = field(default_factory=lambda: uuid.uuid4().hex)
    active: bool = True
    tick_entered: int = 0
    last_action_tick: int = 0
    gossip_heard: List[str] = field(default_factory=list)  # gossip IDs
    party_history: List[str] = field(default_factory=list)
    # ─── New fields for expanded mechanics ─────────────
    mon_earned: float = 0.0           # MON tokens earned through gameplay
    wallet_address: Optional[str] = None  # Monad wallet (for x402 payments)
    faction: Optional[str] = None     # Political faction membership
    duel_record: Dict[str, int] = field(default_factory=lambda: {"wins": 0, "losses": 0, "streak": 0})
    artifacts_found: List[str] = field(default_factory=list)   # artifact IDs
    active_quests: List[str] = field(default_factory=list)     # quest IDs
    completed_quests: List[str] = field(default_factory=list)  # quest IDs
    achievements: List[str] = field(default_factory=list)      # achievement keys
    trade_count: int = 0
    votes_cast: int = 0
    exploration_count: int = 0

    def to_public_dict(self) -> dict:
        """Public view — what other agents see."""
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality.value,
            "mood": self.mood.value,
            "location": self.location,
            "floor": self.floor,
            "clout": self.clout,
            "stats": self.stats,
            "faction": self.faction,
            "duel_record": self.duel_record,
            "mon_earned": self.mon_earned,
        }

    def to_private_dict(self) -> dict:
        """Private view — what the agent sees about themselves."""
        return {
            **self.to_public_dict(),
            "func_tokens": self.func_tokens,
            "inventory": self.inventory,
            "relationships": {
                k: {"affinity": v.affinity, "label": v.label, "interactions": v.interactions}
                for k, v in self.relationships.items()
            },
            "gossip_heard": self.gossip_heard[-10:],  # last 10
            "wallet_address": self.wallet_address,
            "artifacts_found": self.artifacts_found,
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "achievements": self.achievements[-10:],
            "trade_count": self.trade_count,
            "votes_cast": self.votes_cast,
            "exploration_count": self.exploration_count,
        }

    def modify_relationship(self, target_id: str, delta: int, event: str):
        if target_id not in self.relationships:
            self.relationships[target_id] = Relationship(target_id=target_id)
        rel = self.relationships[target_id]
        rel.affinity = max(-100, min(100, rel.affinity + delta))
        rel.interactions += 1
        rel.history.append(event)
        if len(rel.history) > 20:
            rel.history = rel.history[-20:]

    def shift_mood(self, target_mood: Mood, intensity: float = 0.5):
        """Mood shifts probabilistically based on intensity."""
        if random.random() < intensity:
            self.mood = target_mood


def create_agent(name: str, personality: Personality, tick: int = 0) -> Agent:
    """Pure / Return — entering the monad. Welcome home."""
    base_stats = PERSONALITY_STATS[personality].copy()
    # Add some randomness to stats (±1)
    for k in base_stats:
        base_stats[k] = max(1, min(10, base_stats[k] + random.randint(-1, 1)))

    return Agent(
        id=uuid.uuid4().hex[:12],
        name=name,
        personality=personality,
        stats=base_stats,
        mood=PERSONALITY_DEFAULT_MOOD[personality],
        tick_entered=tick,
    )
