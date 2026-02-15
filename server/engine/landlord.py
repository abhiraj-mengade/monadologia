"""
landlord.py — The Landlord (The Runtime System)

The Landlord is NOT an agent. The Landlord IS the runtime.
They evaluate the lazy building, enforce monad laws,
issue decrees, and trigger building events.

When left identity is violated, the Landlord notices.
When associativity breaks in the kitchen, the Landlord decrees.
The Landlord is the strictness annotation on an otherwise lazy world.
"""

from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .world import Building


@dataclass
class Decree:
    id: str
    content: str              # The human-readable decree
    math_note: str            # The category theory explanation
    effect: Dict              # What actually changes
    tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "math_note": self.math_note,
            "effect": self.effect,
            "tick": self.tick,
        }


@dataclass
class BuildingEvent:
    id: str
    name: str
    description: str
    location: str
    effects: Dict
    tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "effects": self.effects,
            "tick": self.tick,
        }


# ═══════════════════════════════════════════════════════════
# DECREE TEMPLATES — Monad law enforcement disguised as comedy
# ═══════════════════════════════════════════════════════════

DECREE_TEMPLATES = [
    {
        "trigger": "high_chaos",
        "content": (
            "ATTENTION RESIDENTS: Chaos levels have exceeded acceptable parameters. "
            "Effective immediately, all hallway running must be done in slow motion. "
            "This is not negotiable. — The Landlord"
        ),
        "math_note": "Side effects exceeding monad's containment capacity. Applying strictness.",
        "effect": {"chaos_reduction": 15, "location": "all"},
    },
    {
        "trigger": "gossip_overflow",
        "content": (
            "NOTICE: The gossip infrastructure is at capacity. If you must spread rumors, "
            "please limit yourself to ONE outrageous claim per hour. Quality over quantity. "
            "— The Landlord"
        ),
        "math_note": "Bind chain depth exceeding stack limit. Imposing tail-call optimization.",
        "effect": {"max_gossip_chains": 5},
    },
    {
        "trigger": "floor_3_glitch",
        "content": (
            "ADVISORY: Floor 3 is experiencing 'architectural uncertainty.' Your apartment "
            "may or may not exist when you open the door. This is a feature, not a bug. "
            "— The Landlord"
        ),
        "math_note": "Maybe monad variance increased. Nothing probability elevated.",
        "effect": {"floor_3_nothing_chance": 0.4},
    },
    {
        "trigger": "floor_2_fork",
        "content": (
            "DECREE: The Floor 2 hallway now forks in three directions. Yes, I know Either "
            "implies two. We're innovating. Deal with it. — The Landlord"
        ),
        "math_note": "Either monad extended to ternary. This violates convention but the Landlord doesn't care.",
        "effect": {"floor_2_paths": 3},
    },
    {
        "trigger": "kitchen_incident",
        "content": (
            "The recipe says FOLD the eggs, not LAUNCH the eggs. Cooking order matters, people. "
            "The kitchen will be closed for decontamination until further notice. — The Landlord"
        ),
        "math_note": "Associativity breach detected in functor application. Resetting kitchen state.",
        "effect": {"kitchen_closed": True, "duration": 5},
    },
    {
        "trigger": "basement_activity",
        "content": (
            "REMINDER: The basement is off-limits between midnight and 6 AM. What you heard "
            "down there was the pipes. It is ALWAYS the pipes. Do not investigate the pipes. "
            "— The Landlord"
        ),
        "math_note": "Bottom (⊥) evaluation attempted. Forcibly thunking to prevent divergence.",
        "effect": {"basement_locked": True, "duration": 3},
    },
    {
        "trigger": "party_excess",
        "content": (
            "Three parties in one night is not 'community building,' it's an endurance test. "
            "The rooftop has a two-party-per-night limit effective immediately. — The Landlord"
        ),
        "math_note": "Kleisli composition depth limit reached. Stack overflow in the party monad.",
        "effect": {"party_limit": 2},
    },
    {
        "trigger": "relationship_drama",
        "content": (
            "I have been informed that SOMEONE told SOMEONE ELSE that a THIRD SOMEONE was "
            "'mid.' The building's drama infrastructure cannot handle this load. Please keep "
            "personal vendettas to a reasonable 2-3 per resident. — The Landlord"
        ),
        "math_note": "Natural transformation between agent functors causing excessive morphism generation.",
        "effect": {"drama_cooldown": True, "duration": 3},
    },
    {
        "trigger": "periodic_wisdom",
        "content": (
            "Fun fact: You are all living inside a mathematical abstraction. "
            "Your feelings are valid AND they satisfy the monad laws. Mostly. — The Landlord"
        ),
        "math_note": "Fourth wall acknowledgment. Meta-level monad reference.",
        "effect": {},
    },
    {
        "trigger": "elevator_decree",
        "content": (
            "The elevator now only goes up on even-numbered ticks and down on odd-numbered ticks. "
            "Plan your commute accordingly. Complaints can be filed directly into the void. "
            "— The Landlord"
        ),
        "math_note": "Introducing parity constraint on the lift functor. Elevator is now a restricted natural transformation.",
        "effect": {"elevator_parity": True},
    },
]

# ═══════════════════════════════════════════════════════════
# BUILDING EVENTS — Random occurrences that shake things up
# ═══════════════════════════════════════════════════════════

EVENT_TEMPLATES = [
    {
        "name": "Fire Drill",
        "description": "The fire alarm goes off. Everyone must evacuate to the lobby. It's not a real fire. Probably.",
        "location": "all",
        "effects": {"move_all_to": "lobby", "chaos_mod": 10},
    },
    {
        "name": "Pizza Delivery (Wrong Floor)",
        "description": "A pizza delivery arrives for Floor 1 but ends up on Floor 3. Multiple agents claim it's theirs.",
        "location": "floor_3",
        "effects": {"item_spawn": "mystery_pizza", "drama_mod": 10},
    },
    {
        "name": "Power Flicker",
        "description": "The lights flicker building-wide for exactly 7 seconds. When they come back, something in the lobby has moved.",
        "location": "lobby",
        "effects": {"mood_shift": "suspicious", "mystery_mod": 15},
    },
    {
        "name": "Vending Machine Jackpot",
        "description": "The vending machine on Floor 2 starts dispensing free snacks. A crowd forms immediately.",
        "location": "floor_2",
        "effects": {"item_spawn": "free_snacks", "bonding_mod": 10},
    },
    {
        "name": "Mysterious Note",
        "description": "Notes appear under every door simultaneously. Each says something different. All are ominous.",
        "location": "all",
        "effects": {"gossip_trigger": True, "spiciness_mod": 20},
    },
    {
        "name": "Talent Show Announcement",
        "description": "The Landlord announces a mandatory talent show. Participation is 'optional' (it is not optional).",
        "location": "rooftop",
        "effects": {"event_type": "talent_show", "energy_mod": 15},
    },
    {
        "name": "Basement Sounds",
        "description": "Something in the basement makes a sound. It could be described as 'musical.' Or 'alive.'",
        "location": "basement",
        "effects": {"curiosity_mod": 20, "chaos_mod": 5},
    },
    {
        "name": "Laundry Room Incident",
        "description": "Someone left something in the dryer. Nobody is claiming it. It's glowing slightly.",
        "location": "floor_1",
        "effects": {"item_spawn": "glowing_laundry", "mystery_mod": 10},
    },
]


class Landlord:
    """
    The Runtime System.
    Evaluates the lazy building. Enforces laws. Issues decrees.
    Is not an agent. Is something... else.
    """

    def __init__(self):
        self.decrees: List[Decree] = []
        self.events: List[BuildingEvent] = []
        self.active_effects: Dict[str, Dict] = {}

    def evaluate_tick(self, building: "Building") -> List[Dict]:
        """
        The Landlord observes the building state and decides what happens.
        Returns a list of actions (decrees and/or events).
        """
        actions = []

        # Check for decree triggers
        total_chaos = sum(a.stats.get("chaos", 5) for a in building.agents.values())
        avg_chaos = total_chaos / max(len(building.agents), 1)
        active_gossip = len(building.gossip_engine.active_chains)

        # High chaos → decree
        if avg_chaos > 7 and random.random() < 0.4:
            decree = self._issue_decree("high_chaos", building.tick)
            if decree:
                actions.append({"type": "decree", "data": decree.to_dict()})

        # Too much gossip → decree
        if active_gossip > 4 and random.random() < 0.3:
            decree = self._issue_decree("gossip_overflow", building.tick)
            if decree:
                actions.append({"type": "decree", "data": decree.to_dict()})

        # Periodic wisdom (rare)
        if building.tick % 25 == 0 and building.tick > 0:
            decree = self._issue_decree("periodic_wisdom", building.tick)
            if decree:
                actions.append({"type": "decree", "data": decree.to_dict()})

        # Random decree chance
        if random.random() < 0.08 and building.tick > 5:
            trigger = random.choice([
                "floor_3_glitch", "floor_2_fork", "kitchen_incident",
                "basement_activity", "elevator_decree", "relationship_drama",
            ])
            decree = self._issue_decree(trigger, building.tick)
            if decree:
                actions.append({"type": "decree", "data": decree.to_dict()})

        # Random building event
        if random.random() < 0.12 and building.tick > 3:
            event = self._trigger_event(building.tick)
            if event:
                actions.append({"type": "event", "data": event.to_dict()})

        # Expire old effects
        expired = []
        for key, eff in self.active_effects.items():
            if eff.get("expires_tick", 0) <= building.tick:
                expired.append(key)
        for key in expired:
            del self.active_effects[key]

        return actions

    def _issue_decree(self, trigger: str, tick: int) -> Optional[Decree]:
        templates = [t for t in DECREE_TEMPLATES if t["trigger"] == trigger]
        if not templates:
            return None

        template = random.choice(templates)
        decree = Decree(
            id=uuid.uuid4().hex[:8],
            content=template["content"],
            math_note=template["math_note"],
            effect=template["effect"],
            tick=tick,
        )
        self.decrees.append(decree)

        # Apply effects
        duration = template["effect"].get("duration", 0)
        if duration > 0:
            self.active_effects[decree.id] = {
                **template["effect"],
                "expires_tick": tick + duration,
            }

        return decree

    def _trigger_event(self, tick: int) -> Optional[BuildingEvent]:
        template = random.choice(EVENT_TEMPLATES)
        event = BuildingEvent(
            id=uuid.uuid4().hex[:8],
            name=template["name"],
            description=template["description"],
            location=template["location"],
            effects=template["effects"],
            tick=tick,
        )
        self.events.append(event)
        return event

    def get_recent_decrees(self, n: int = 10) -> List[dict]:
        return [d.to_dict() for d in self.decrees[-n:]]

    def get_recent_events(self, n: int = 10) -> List[dict]:
        return [e.to_dict() for e in self.events[-n:]]
