"""
parties.py — Party Composition (Kleisli Arrows / >=>)

A party is a SEQUENCE OF VIBES, each a Kleisli arrow:
    vibe :: PartyState → Maybe PartyState

Composing vibes IS Kleisli composition (>=>):
    thursdayNight = chill >=> karaoke >=> drama

Order matters! This is not a metaphor. Different orderings
produce fundamentally different party outcomes, just like
Kleisli composition is non-commutative.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent


class Vibe(str, Enum):
    CHILL = "chill"
    KARAOKE = "karaoke"
    DRAMA = "drama"
    MYSTERY = "mystery"
    DANCE = "dance"
    DEBATE = "debate"
    POTLUCK = "potluck"


@dataclass
class PartyState:
    energy: int = 50       # 0–100
    chaos: int = 20        # 0–100
    bonding: int = 30      # 0–100
    fun: int = 40          # 0–100
    vibe_log: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "energy": self.energy,
            "chaos": self.chaos,
            "bonding": self.bonding,
            "fun": self.fun,
            "vibe_log": self.vibe_log,
        }


# ═══════════════════════════════════════════════════════════
# VIBE FUNCTIONS — Each is a Kleisli arrow: PartyState → Maybe PartyState
# Returns None (Nothing) if the vibe fails.
# ═══════════════════════════════════════════════════════════

def vibe_chill(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Chill always succeeds. It's the identity-ish vibe."""
    state.energy = max(10, state.energy - 15)
    state.chaos = max(0, state.chaos - 20)
    state.bonding += 15
    state.fun += 5
    state.vibe_log.append("Everyone mellowed out. Good vibes. 🧘")
    return state


def vibe_karaoke(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Karaoke might fail if energy is too low (nobody wants to sing)."""
    if state.energy < 20:
        state.vibe_log.append("Nobody had the energy for karaoke. The mic sat lonely on the table. 🎤💀")
        return None  # Nothing — karaoke failed

    # Find the most charismatic attendee for the performance
    best_performer = max(attendees, key=lambda a: a.stats.get("charisma", 5)) if attendees else None
    talent = random.randint(10, 100)

    if talent > 70:
        state.fun += 30
        state.bonding += 20
        state.energy += 10
        performer_name = best_performer.name if best_performer else "Someone"
        state.vibe_log.append(f"{performer_name} CRUSHED the karaoke. Standing ovation. 🎤🔥")
    elif talent > 40:
        state.fun += 15
        state.energy += 5
        state.vibe_log.append("Karaoke was decent. A few bangers, a few... attempts. 🎤😅")
    else:
        state.chaos += 20
        state.fun += 10  # Bad karaoke is still memorable
        state.vibe_log.append("The karaoke was objectively terrible. But somehow... iconic? 🎤💀🔥")

    return state


def vibe_drama(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Drama might fail if everyone's too chill."""
    if state.chaos < 10 and state.energy < 25:
        state.vibe_log.append("Everyone was too zen for drama. Suspicious. 🤔")
        return None

    drama_agents = [a for a in attendees if a.stats.get("drama", 5) > 5]
    if drama_agents:
        instigator = random.choice(drama_agents)
        state.chaos += 30
        state.energy += 20
        state.fun += 15
        state.bonding -= 10
        state.vibe_log.append(
            f"{instigator.name} started something. Alliances were tested. "
            f"Someone said something they can't take back. 🍿💥"
        )
    else:
        state.chaos += 15
        state.energy += 10
        state.vibe_log.append("Mild drama. A passive-aggressive comment about dish duty. Classic. 😤")

    return state


def vibe_mystery(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Mystery always succeeds but outcomes are unpredictable."""
    roll = random.random()
    if roll < 0.3:
        state.chaos += 25
        state.fun += 20
        state.vibe_log.append(
            "The lights flickered. A note appeared under the door. "
            "Nobody knows where it came from. 👁️✨"
        )
    elif roll < 0.6:
        state.bonding += 25
        state.fun += 15
        state.vibe_log.append(
            "Someone found a hidden compartment in the wall. Inside: "
            "a vintage board game. Everyone played. Best night ever. 🎲"
        )
    else:
        state.chaos += 15
        state.energy -= 10
        state.vibe_log.append(
            "An unexplained sound from the basement. Everyone got quiet. "
            "Then pretended they didn't hear it. 🔇👀"
        )
    return state


def vibe_dance(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Dance needs energy. If you've got it, it's electric."""
    if state.energy < 30:
        state.vibe_log.append("Nobody had legs left for dancing. The speakers played to an empty floor. 💃❌")
        return None

    state.energy -= 20
    state.fun += 25
    state.bonding += 15
    state.chaos += 10
    state.vibe_log.append("The dance floor opened up. Moves were made. Reputations were built. 💃🕺✨")
    return state


def vibe_debate(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Debate needs at least some brain energy."""
    nerds = [a for a in attendees if a.stats.get("purity", 5) > 6]
    state.energy += 10
    state.chaos += 15

    if nerds:
        state.fun += 10
        state.bonding += 5
        debater = random.choice(nerds)
        state.vibe_log.append(
            f"{debater.name} initiated a philosophical debate. "
            f"'Is a hot dog a sandwich?' It got heated. 🌭🧠"
        )
    else:
        state.fun += 5
        state.vibe_log.append("Someone tried to start a debate but everyone just vibed instead. 🤷")

    return state


def vibe_potluck(state: PartyState, attendees: List["Agent"]) -> Optional[PartyState]:
    """Potluck — everyone brings something. Quality varies."""
    state.bonding += 20
    state.fun += 15

    chaos_level = sum(a.stats.get("chaos", 5) for a in attendees) / max(len(attendees), 1)
    if chaos_level > 6:
        state.chaos += 20
        state.vibe_log.append(
            "The potluck was... adventurous. Someone brought 'mystery casserole.' "
            "Two people are now bonded by shared food poisoning survival. 🍲😵"
        )
    else:
        state.chaos += 5
        state.vibe_log.append(
            "The potluck was genuinely lovely. Good food, good company. "
            "The pasta was especially legendary. 🍝✨"
        )
    return state


# Map vibe enum → function (Kleisli arrow)
VIBE_FUNCTIONS: Dict[Vibe, Callable] = {
    Vibe.CHILL: vibe_chill,
    Vibe.KARAOKE: vibe_karaoke,
    Vibe.DRAMA: vibe_drama,
    Vibe.MYSTERY: vibe_mystery,
    Vibe.DANCE: vibe_dance,
    Vibe.DEBATE: vibe_debate,
    Vibe.POTLUCK: vibe_potluck,
}


def kleisli_compose(vibes: List[Vibe], attendees: List["Agent"]) -> PartyState:
    """
    KLEISLI COMPOSITION (>=>)

    Compose a sequence of vibes into a party outcome.
    Each vibe is a Kleisli arrow (PartyState → Maybe PartyState).

    If any vibe returns Nothing, the party state freezes at that point.
    Order matters — (chill >=> drama >=> karaoke) gives a totally
    different night than (drama >=> karaoke >=> chill).

    This IS Kleisli composition. Not a metaphor.
    """
    state = PartyState()

    for vibe in vibes:
        vibe_fn = VIBE_FUNCTIONS.get(vibe)
        if vibe_fn is None:
            continue

        # Clamp values before each vibe
        state.energy = max(0, min(100, state.energy))
        state.chaos = max(0, min(100, state.chaos))
        state.bonding = max(0, min(100, state.bonding))
        state.fun = max(0, min(100, state.fun))

        result = vibe_fn(state, attendees)
        if result is None:
            # Nothing — the Maybe monad short-circuits
            break
        state = result

    # Final clamp
    state.energy = max(0, min(100, state.energy))
    state.chaos = max(0, min(100, state.chaos))
    state.bonding = max(0, min(100, state.bonding))
    state.fun = max(0, min(100, state.fun))

    return state


@dataclass
class Party:
    id: str
    host_id: str
    host_name: str
    location: str
    vibes: List[Vibe]
    attendee_ids: List[str] = field(default_factory=list)
    state: Optional[PartyState] = None
    resolved: bool = False
    created_tick: int = 0
    resolved_tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "host_id": self.host_id,
            "host_name": self.host_name,
            "location": self.location,
            "vibes": [v.value for v in self.vibes],
            "attendee_ids": self.attendee_ids,
            "state": self.state.to_dict() if self.state else None,
            "resolved": self.resolved,
        }
