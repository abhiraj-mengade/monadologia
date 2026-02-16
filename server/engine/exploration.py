"""
exploration.py — Quests, Artifacts & Hidden Rooms

The basement goes deeper than anyone thought.
Exploration is the State monad — hidden state threads through
each step of a quest, revealing new information.

  explore :: ExplorationState → (Discovery, ExplorationState)

Artifacts are rare items that grant permanent bonuses.
Quests are multi-step narrative chains that reward MON.
"""

from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent


# ═══════════════════════════════════════════════════════════
# ARTIFACTS — Rare items found through exploration
# ═══════════════════════════════════════════════════════════

@dataclass
class Artifact:
    id: str
    name: str
    rarity: str  # common, rare, epic, legendary
    description: str
    stat_bonus: Dict[str, int]
    special_ability: Optional[str] = None
    found_by: Optional[str] = None
    found_tick: int = 0
    location_found: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "rarity": self.rarity,
            "description": self.description,
            "stat_bonus": self.stat_bonus,
            "special_ability": self.special_ability,
            "found_by": self.found_by,
            "found_tick": self.found_tick,
        }


# Artifact templates organized by rarity
ARTIFACT_TEMPLATES = {
    "common": [
        {
            "name": "Dusty Board Game",
            "description": "A vintage board game from the building's first residents. +1 creativity.",
            "stat_bonus": {"creativity": 1},
        },
        {
            "name": "Broken Clock",
            "description": "It's always right twice a day. +1 purity.",
            "stat_bonus": {"purity": 1},
        },
        {
            "name": "Mysterious Key",
            "description": "Opens... something? Maybe? +1 chaos.",
            "stat_bonus": {"chaos": 1},
        },
        {
            "name": "Gossip Amplifier",
            "description": "A strange device that makes whispers louder. +1 charisma.",
            "stat_bonus": {"charisma": 1},
        },
    ],
    "rare": [
        {
            "name": "The Landlord's Old Journal",
            "description": "Pages of incomprehensible monad laws. Reading it grants insight. +2 creativity, +1 purity.",
            "stat_bonus": {"creativity": 2, "purity": 1},
        },
        {
            "name": "Quantum Dice",
            "description": "Shows all faces simultaneously until observed. +2 chaos, +1 drama.",
            "stat_bonus": {"chaos": 2, "drama": 1},
        },
        {
            "name": "Ancient Cooking Utensil",
            "description": "A spatula that seems to cook by itself. +2 purity for cooking.",
            "stat_bonus": {"purity": 2},
            "special_ability": "perfect_cook",
        },
        {
            "name": "Social Radar",
            "description": "You can sense where other agents are in the building. +2 charisma.",
            "stat_bonus": {"charisma": 2},
            "special_ability": "detect_agents",
        },
    ],
    "epic": [
        {
            "name": "The Maybe Compass",
            "description": "Points to where things MIGHT be. Reduces Nothing chance on Floor 3. +3 creativity.",
            "stat_bonus": {"creativity": 3},
            "special_ability": "maybe_immunity",
        },
        {
            "name": "Drama Crown",
            "description": "An ornate crown that makes everything you say 10x more dramatic. +3 drama, +1 charisma.",
            "stat_bonus": {"drama": 3, "charisma": 1},
            "special_ability": "drama_amplifier",
        },
        {
            "name": "Chaos Scepter",
            "description": "A scepter that channels pure entropy. Pranks always succeed. +3 chaos.",
            "stat_bonus": {"chaos": 3},
            "special_ability": "prank_master",
        },
    ],
    "legendary": [
        {
            "name": "The Bind Operator (>>=)",
            "description": "The physical manifestation of monadic bind. Gossip through you becomes LEGENDARY. +3 to all stats.",
            "stat_bonus": {"charisma": 3, "creativity": 3, "drama": 3, "purity": 3, "chaos": 3},
            "special_ability": "legendary_gossip",
        },
        {
            "name": "Kleisli's Arrow",
            "description": "A golden arrow that can compose any sequence of events. Parties you throw are always epic. +4 creativity, +2 charisma.",
            "stat_bonus": {"creativity": 4, "charisma": 2},
            "special_ability": "epic_parties",
        },
        {
            "name": "The Functor Lens",
            "description": "See the mathematical structure underlying reality. You can see hidden rooms. +4 purity, +2 creativity.",
            "stat_bonus": {"purity": 4, "creativity": 2},
            "special_ability": "see_hidden",
        },
    ],
}

# Rarity drop rates
RARITY_CHANCES = {
    "common": 0.50,
    "rare": 0.30,
    "epic": 0.15,
    "legendary": 0.05,
}


# ═══════════════════════════════════════════════════════════
# QUESTS — Multi-step narrative chains
# ═══════════════════════════════════════════════════════════

@dataclass
class Quest:
    id: str
    name: str
    description: str
    difficulty: str  # easy, medium, hard, legendary
    steps: List[Dict]  # [{description, action_required, completed}]
    current_step: int = 0
    assigned_to: Optional[str] = None
    status: str = "available"  # available, active, completed, failed
    rewards: Dict = field(default_factory=dict)
    created_tick: int = 0
    completed_tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "steps": self.steps,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "assigned_to": self.assigned_to,
            "status": self.status,
            "rewards": self.rewards,
        }


QUEST_TEMPLATES = [
    {
        "name": "The Basement Mystery",
        "description": "Strange sounds come from the basement. Investigate.",
        "difficulty": "medium",
        "steps": [
            {"description": "Go to the basement", "action_required": "move_to_basement"},
            {"description": "Explore the basement", "action_required": "explore"},
            {"description": "Report findings to someone", "action_required": "talk_about_basement"},
        ],
        "rewards": {"func": 30, "clout": 20, "mon": 0.001, "artifact_chance": 0.5},
    },
    {
        "name": "The Great Gossip Chain",
        "description": "Start a gossip that reaches at least 5 different agents.",
        "difficulty": "medium",
        "steps": [
            {"description": "Start a gossip chain", "action_required": "gossip_start"},
            {"description": "Help spread it to 3 agents", "action_required": "gossip_chain_3"},
            {"description": "Chain reaches 5 agents", "action_required": "gossip_chain_5"},
        ],
        "rewards": {"func": 25, "clout": 30, "mon": 0.0005},
    },
    {
        "name": "Party Animal",
        "description": "Throw 3 parties with different vibe compositions.",
        "difficulty": "hard",
        "steps": [
            {"description": "Throw party #1", "action_required": "throw_party"},
            {"description": "Throw party #2 (different vibes)", "action_required": "throw_party_unique"},
            {"description": "Throw party #3 (different vibes again)", "action_required": "throw_party_unique_2"},
        ],
        "rewards": {"func": 50, "clout": 40, "mon": 0.002, "artifact_chance": 0.3},
    },
    {
        "name": "The Floor Tour",
        "description": "Visit every floor of the building.",
        "difficulty": "easy",
        "steps": [
            {"description": "Visit the Rooftop", "action_required": "visit_rooftop"},
            {"description": "Visit Floor 3", "action_required": "visit_floor_3"},
            {"description": "Visit Floor 2", "action_required": "visit_floor_2"},
            {"description": "Visit Floor 1", "action_required": "visit_floor_1"},
            {"description": "Visit the Basement", "action_required": "visit_basement"},
        ],
        "rewards": {"func": 20, "clout": 15, "mon": 0.0003},
    },
    {
        "name": "Social Climber",
        "description": "Build positive relationships with 5 different agents.",
        "difficulty": "hard",
        "steps": [
            {"description": "Make a friend (affinity > 40)", "action_required": "make_friend_1"},
            {"description": "Make friend #2", "action_required": "make_friend_2"},
            {"description": "Make friend #3", "action_required": "make_friend_3"},
            {"description": "Make friend #4", "action_required": "make_friend_4"},
            {"description": "Make friend #5", "action_required": "make_friend_5"},
        ],
        "rewards": {"func": 40, "clout": 50, "mon": 0.003},
    },
    {
        "name": "Chaos Incarnate",
        "description": "Cause maximum disruption. Prank 3 agents and start a faction war.",
        "difficulty": "legendary",
        "steps": [
            {"description": "Prank someone successfully", "action_required": "prank_1"},
            {"description": "Prank someone else", "action_required": "prank_2"},
            {"description": "Prank a third person", "action_required": "prank_3"},
            {"description": "Start a controversial proposal", "action_required": "controversial_proposal"},
        ],
        "rewards": {"func": 60, "clout": 80, "mon": 0.005, "artifact_chance": 0.7},
    },
    {
        "name": "The Duel Master",
        "description": "Win 3 duels against different opponents.",
        "difficulty": "hard",
        "steps": [
            {"description": "Win duel #1", "action_required": "duel_win_1"},
            {"description": "Win duel #2", "action_required": "duel_win_2"},
            {"description": "Win duel #3", "action_required": "duel_win_3"},
        ],
        "rewards": {"func": 45, "clout": 35, "mon": 0.002, "artifact_chance": 0.4},
    },
]


# ═══════════════════════════════════════════════════════════
# EXPLORATION ENGINE
# ═══════════════════════════════════════════════════════════

class ExplorationEngine:
    """Manages quests, artifacts, and exploration."""

    def __init__(self):
        self.artifacts: Dict[str, Artifact] = {}
        self.quests: Dict[str, Quest] = {}
        self.available_quests: List[Quest] = []
        self._generate_initial_quests()

    def _generate_initial_quests(self):
        """Generate the initial set of available quests."""
        for template in QUEST_TEMPLATES:
            quest = Quest(
                id=uuid.uuid4().hex[:8],
                name=template["name"],
                description=template["description"],
                difficulty=template["difficulty"],
                steps=[{**s, "completed": False} for s in template["steps"]],
                rewards=template["rewards"],
            )
            self.available_quests.append(quest)

    def explore_location(
        self,
        agent: "Agent",
        location: str,
        tick: int,
    ) -> dict:
        """
        Explore a location for artifacts and discoveries.
        State monad — each exploration modifies hidden exploration state.
        """
        # Base discovery chance depends on location and stats
        creativity = agent.stats.get("creativity", 5)
        chaos = agent.stats.get("chaos", 5)
        purity = agent.stats.get("purity", 5)

        discovery_chance = 0.3 + (creativity * 0.03) + (chaos * 0.02)

        # Basement has higher discovery chance
        if location == "basement":
            discovery_chance += 0.2

        # Has "see_hidden" ability?
        if hasattr(agent, 'artifacts') and any(
            a.get("special_ability") == "see_hidden"
            for a in getattr(agent, 'artifact_list', [])
        ):
            discovery_chance += 0.15

        discoveries = []

        if random.random() < discovery_chance:
            # Found something!
            artifact = self._generate_artifact(location, tick, agent.id)
            if artifact:
                self.artifacts[artifact.id] = artifact
                discoveries.append({
                    "type": "artifact",
                    "artifact": artifact.to_dict(),
                })

                # Apply stat bonuses
                for stat, bonus in artifact.stat_bonus.items():
                    current = agent.stats.get(stat, 5)
                    agent.stats[stat] = min(15, current + bonus)  # Allow stats above 10 with artifacts

        # Hidden room discovery (rare)
        if location == "basement" and random.random() < 0.1:
            hidden_rooms = [
                {
                    "name": "The Monad's Heart",
                    "description": "A room with mathematical symbols covering every surface. You feel... observed.",
                    "reward": {"clout": 25, "func": 15},
                },
                {
                    "name": "The Lost Archive",
                    "description": "Filing cabinets full of old resident records. Gossip GOLD.",
                    "reward": {"clout": 20, "gossip_boost": True},
                },
                {
                    "name": "The Void Room",
                    "description": "A room that seems larger on the inside than the outside. Bottom (⊥) made physical.",
                    "reward": {"clout": 30, "chaos_boost": 3},
                },
            ]
            room = random.choice(hidden_rooms)
            discoveries.append({
                "type": "hidden_room",
                "room": room,
            })

        # Random lore discovery
        if random.random() < 0.4:
            lore = random.choice([
                "You found scratched writing on the wall: 'The Landlord is not what they seem.'",
                "A faded photo shows the building under construction. It looks... different.",
                "Old love letters between residents from decades ago. Some things never change.",
                "A journal entry: 'Day 47. The elevator went to a floor that doesn't exist.'",
                "Graffiti in a hidden corner: 'bind (return x) f ≡ f x — THIS IS THE WAY'",
                "A sticky note: 'Remember — the building IS the monad. We are the computations.'",
                "An old map of the building. It shows a room that isn't on the current floor plans.",
                "Someone carved 'Kleisli was here' into the doorframe.",
            ])
            discoveries.append({
                "type": "lore",
                "content": lore,
            })

        return {
            "success": True,
            "location": location,
            "discoveries": discoveries,
            "discovery_chance": round(discovery_chance, 2),
        }

    def _generate_artifact(
        self,
        location: str,
        tick: int,
        agent_id: str,
    ) -> Optional[Artifact]:
        """Generate a random artifact based on rarity."""
        # Roll for rarity
        roll = random.random()
        cumulative = 0
        chosen_rarity = "common"

        for rarity, chance in RARITY_CHANCES.items():
            cumulative += chance
            if roll < cumulative:
                chosen_rarity = rarity
                break

        templates = ARTIFACT_TEMPLATES.get(chosen_rarity, [])
        if not templates:
            return None

        template = random.choice(templates)

        return Artifact(
            id=uuid.uuid4().hex[:8],
            name=template["name"],
            rarity=chosen_rarity,
            description=template["description"],
            stat_bonus=template["stat_bonus"],
            special_ability=template.get("special_ability"),
            found_by=agent_id,
            found_tick=tick,
            location_found=location,
        )

    def accept_quest(self, agent: "Agent", quest_id: str) -> dict:
        """Accept a quest."""
        quest = None
        for q in self.available_quests:
            if q.id == quest_id and q.status == "available":
                quest = q
                break

        if not quest:
            return {"success": False, "error": "Quest not available"}

        quest.assigned_to = agent.id
        quest.status = "active"
        self.quests[quest.id] = quest

        return {
            "success": True,
            "quest": quest.to_dict(),
        }

    def advance_quest(
        self,
        agent: "Agent",
        quest_id: str,
        action: str,
        tick: int,
    ) -> dict:
        """Check if an action advances a quest step."""
        quest = self.quests.get(quest_id)
        if not quest or quest.assigned_to != agent.id:
            return {"success": False, "error": "Not your quest"}

        if quest.status != "active":
            return {"success": False, "error": f"Quest is {quest.status}"}

        current_step = quest.steps[quest.current_step]
        # Simplified — check if the action matches
        if action in current_step.get("action_required", ""):
            current_step["completed"] = True
            quest.current_step += 1

            if quest.current_step >= len(quest.steps):
                # Quest complete!
                quest.status = "completed"
                quest.completed_tick = tick
                return {
                    "success": True,
                    "quest_completed": True,
                    "quest": quest.to_dict(),
                    "rewards": quest.rewards,
                }

            return {
                "success": True,
                "step_completed": True,
                "quest": quest.to_dict(),
                "next_step": quest.steps[quest.current_step],
            }

        return {"success": False, "error": "Action doesn't match current quest step"}

    def get_available_quests(self) -> List[dict]:
        return [q.to_dict() for q in self.available_quests if q.status == "available"]

    def get_agent_quests(self, agent_id: str) -> List[dict]:
        return [q.to_dict() for q in self.quests.values() if q.assigned_to == agent_id]

    def get_artifacts(self) -> List[dict]:
        return [a.to_dict() for a in self.artifacts.values()]

    def get_agent_artifacts(self, agent_id: str) -> List[dict]:
        return [a.to_dict() for a in self.artifacts.values() if a.found_by == agent_id]
