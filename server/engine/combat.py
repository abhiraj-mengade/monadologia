"""
combat.py — Duels & PvP Combat

Duels are the Monad's way of resolving conflicts.
Stats determine base power, but personality adds special abilities.
Combat uses the Either monad — every exchange has exactly two outcomes.

  duel :: Agent → Agent → Either Victory Defeat
"""

from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent


# ═══════════════════════════════════════════════════════════
# DUEL SYSTEM
# ═══════════════════════════════════════════════════════════

@dataclass
class DuelResult:
    id: str
    challenger_id: str
    defender_id: str
    challenger_name: str
    defender_name: str
    winner_id: str
    loser_id: str
    rounds: List[Dict]
    final_score: Dict[str, int]  # {challenger: X, defender: Y}
    spoils: Dict  # What the winner gets
    narration: str
    tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "challenger": {"id": self.challenger_id, "name": self.challenger_name},
            "defender": {"id": self.defender_id, "name": self.defender_name},
            "winner_id": self.winner_id,
            "loser_id": self.loser_id,
            "rounds": self.rounds,
            "final_score": self.final_score,
            "spoils": self.spoils,
            "narration": self.narration,
            "tick": self.tick,
        }


# Personality special abilities in duels
DUEL_ABILITIES = {
    "social_butterfly": {
        "name": "Crowd Support",
        "description": "Nearby agents cheer, giving +2 charisma bonus",
        "stat_boost": {"charisma": 2},
        "trigger_chance": 0.4,
    },
    "schemer": {
        "name": "Calculated Strike",
        "description": "Pre-planned the entire duel. +3 creativity bonus",
        "stat_boost": {"creativity": 3},
        "trigger_chance": 0.5,
    },
    "drama_queen": {
        "name": "Dramatic Comeback",
        "description": "When losing, dramatically rallies with +4 drama",
        "stat_boost": {"drama": 4},
        "trigger_chance": 0.3,
        "only_when_losing": True,
    },
    "nerd": {
        "name": "Statistical Advantage",
        "description": "Calculated the optimal strategy. +2 to all stats",
        "stat_boost": {"charisma": 2, "creativity": 2, "drama": 2, "purity": 2},
        "trigger_chance": 0.25,
    },
    "chaos_gremlin": {
        "name": "Wild Card",
        "description": "Does something completely unpredictable. Random ±5 to random stat",
        "stat_boost": {},  # Random at runtime
        "trigger_chance": 0.6,
    },
    "conspiracy_theorist": {
        "name": "Psychological Warfare",
        "description": "Whispers something that makes opponent doubt everything. -2 to opponent's purity",
        "stat_boost": {},  # Debuffs opponent
        "trigger_chance": 0.35,
    },
}


def resolve_duel(
    challenger: "Agent",
    defender: "Agent",
    tick: int = 0,
    wager_func: int = 0,
    nearby_count: int = 0,
) -> DuelResult:
    """
    Resolve a duel between two agents.

    Combat is stat-based with personality abilities and randomness.
    Three rounds — best of three wins.

    Either Victory Defeat — always a binary outcome.
    """
    rounds = []
    challenger_score = 0
    defender_score = 0

    # Stats that matter in combat
    combat_stats = ["charisma", "creativity", "drama", "chaos"]

    for round_num in range(1, 4):
        # Pick a random combat stat for this round
        stat = random.choice(combat_stats)

        c_base = challenger.stats.get(stat, 5)
        d_base = defender.stats.get(stat, 5)

        # Add randomness (±3)
        c_roll = c_base + random.randint(-3, 3)
        d_roll = d_base + random.randint(-3, 3)

        # Personality abilities
        c_ability = _check_ability(challenger, challenger_score < defender_score)
        d_ability = _check_ability(defender, defender_score < challenger_score)

        c_bonus = 0
        d_bonus = 0
        c_ability_desc = None
        d_ability_desc = None

        if c_ability:
            c_bonus = c_ability.get("bonus", 0)
            c_ability_desc = c_ability.get("description")
            c_roll += c_bonus

        if d_ability:
            d_bonus = d_ability.get("bonus", 0)
            d_ability_desc = d_ability.get("description")
            d_roll += d_bonus

        # Social butterfly bonus from crowd
        if challenger.personality.value == "social_butterfly" and nearby_count > 2:
            c_roll += 1
        if defender.personality.value == "social_butterfly" and nearby_count > 2:
            d_roll += 1

        round_winner = "challenger" if c_roll >= d_roll else "defender"
        if round_winner == "challenger":
            challenger_score += 1
        else:
            defender_score += 1

        round_data = {
            "round": round_num,
            "stat": stat,
            "challenger_roll": c_roll,
            "defender_roll": d_roll,
            "winner": round_winner,
            "challenger_ability": c_ability_desc,
            "defender_ability": d_ability_desc,
        }
        rounds.append(round_data)

        # If someone has 2 wins, they win
        if challenger_score >= 2 or defender_score >= 2:
            break

    # Determine winner
    winner_id = challenger.id if challenger_score > defender_score else defender.id
    loser_id = defender.id if winner_id == challenger.id else challenger.id

    # Spoils
    spoils = {
        "func_transferred": wager_func,
        "clout_earned": 15,
        "clout_lost": 5,
    }

    # Generate narration
    narration = _narrate_duel(
        challenger, defender, rounds,
        challenger_score, defender_score,
        winner_id == challenger.id,
    )

    return DuelResult(
        id=uuid.uuid4().hex[:8],
        challenger_id=challenger.id,
        defender_id=defender.id,
        challenger_name=challenger.name,
        defender_name=defender.name,
        winner_id=winner_id,
        loser_id=loser_id,
        rounds=rounds,
        final_score={
            "challenger": challenger_score,
            "defender": defender_score,
        },
        spoils=spoils,
        narration=narration,
        tick=tick,
    )


def _check_ability(agent: "Agent", is_losing: bool = False) -> Optional[dict]:
    """Check if an agent's personality ability triggers."""
    ability = DUEL_ABILITIES.get(agent.personality.value)
    if not ability:
        return None

    # Check trigger chance
    if random.random() > ability["trigger_chance"]:
        return None

    # Check losing-only abilities
    if ability.get("only_when_losing") and not is_losing:
        return None

    # Calculate bonus
    if agent.personality.value == "chaos_gremlin":
        # Random bonus/penalty
        bonus = random.randint(-5, 5)
        return {
            "bonus": bonus,
            "description": f"🎲 WILD CARD! {agent.name} did something unpredictable! ({'+' if bonus > 0 else ''}{bonus})",
        }
    elif agent.personality.value == "conspiracy_theorist":
        return {
            "bonus": 2,
            "description": f"🔍 {agent.name} whispered something unsettling. Opponent doubts everything.",
        }
    else:
        total_boost = sum(ability["stat_boost"].values())
        return {
            "bonus": total_boost,
            "description": f"⚡ {ability['name']}! {ability['description']}",
        }


def _narrate_duel(
    challenger: "Agent",
    defender: "Agent",
    rounds: List[Dict],
    c_score: int,
    d_score: int,
    challenger_won: bool,
) -> str:
    """Generate a dramatic duel narration."""
    winner = challenger if challenger_won else defender
    loser = challenger if not challenger_won else defender

    if c_score == 2 and d_score == 0:
        return (
            f"⚔️ {winner.name} DEMOLISHED {loser.name} in a flawless 2-0 victory! "
            f"The {winner.personality.value} proved utterly dominant. {loser.name} may need therapy."
        )
    elif abs(c_score - d_score) == 1:
        return (
            f"⚔️ An INCREDIBLE duel between {challenger.name} and {defender.name}! "
            f"It came down to the wire — {winner.name} edged out {loser.name} {max(c_score, d_score)}-{min(c_score, d_score)}. "
            f"The crowd (if any) went wild."
        )
    else:
        return (
            f"⚔️ {winner.name} defeated {loser.name} {max(c_score, d_score)}-{min(c_score, d_score)} "
            f"in a duel for the ages. Both fought with honor. Well, mostly."
        )
