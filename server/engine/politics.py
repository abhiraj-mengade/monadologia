"""
politics.py — Factions, Voting & Governance

The Monad is a democracy. Sort of. The Landlord has final say,
but residents can form factions, propose votes, and influence
building policy.

Factions map to category theory concepts:
  - The Purists (Identity faction) — Keep things predictable
  - The Chaoticians (List faction) — Embrace nondeterminism
  - The Schemers (Either faction) — Binary decisions, strategic plays
  - The Mystics (Maybe faction) — Uncertain, mystical, explore the unknown
  - The Unbound (IO faction) — Freedom, no constraints, side effects welcome

Voting is a natural transformation — mapping individual preferences
to a collective decision.
"""

from __future__ import annotations
import uuid
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .agents import Agent


class Faction(str, Enum):
    PURISTS = "purists"          # Identity monad — predictability
    CHAOTICIANS = "chaoticians"  # List monad — nondeterminism
    SCHEMERS = "schemers"        # Either monad — binary strategic
    MYSTICS = "mystics"          # Maybe monad — uncertainty
    UNBOUND = "unbound"          # IO monad — freedom, side effects


FACTION_INFO = {
    Faction.PURISTS: {
        "name": "The Purists",
        "monad": "Identity",
        "motto": "What goes in comes out unchanged.",
        "description": "Believe in order, predictability, and the sanctity of pure functions. Want the building to be well-organized.",
        "bonuses": {"purity": 2, "chaos": -1},
        "headquarters": "lobby",
    },
    Faction.CHAOTICIANS: {
        "name": "The Chaoticians",
        "monad": "List",
        "motto": "Why have one outcome when you can have twelve?",
        "description": "Embrace chaos, nondeterminism, and maximum entropy. Every action should branch into multiple outcomes.",
        "bonuses": {"chaos": 2, "creativity": 1},
        "headquarters": "floor_1_hall",
    },
    Faction.SCHEMERS: {
        "name": "The Schemers",
        "monad": "Either",
        "motto": "Every choice is binary. Choose wisely.",
        "description": "Strategic minds who see the world in Left/Right, True/False, Win/Lose. Always three moves ahead.",
        "bonuses": {"creativity": 2, "drama": 1},
        "headquarters": "floor_2_hall",
    },
    Faction.MYSTICS: {
        "name": "The Mystics",
        "monad": "Maybe",
        "motto": "Perhaps. Or perhaps not.",
        "description": "Embrace uncertainty. Some things exist, some don't. The basement calls to them.",
        "bonuses": {"drama": 1, "creativity": 1, "chaos": 1},
        "headquarters": "floor_3_hall",
    },
    Faction.UNBOUND: {
        "name": "The Unbound",
        "monad": "IO",
        "motto": "Side effects are features, not bugs.",
        "description": "Freedom above all. No constraints, no rules. The rooftop is their domain.",
        "bonuses": {"charisma": 2, "chaos": 1},
        "headquarters": "rooftop",
    },
}


@dataclass
class Proposal:
    id: str
    proposer_id: str
    proposer_name: str
    title: str
    description: str
    proposal_type: str  # decree, rule_change, event, faction_war
    options: List[str]  # e.g., ["yes", "no"] or ["option_a", "option_b", "option_c"]
    votes: Dict[str, str] = field(default_factory=dict)  # agent_id → choice
    faction_support: Dict[str, int] = field(default_factory=dict)  # faction → vote count
    status: str = "active"  # active, passed, failed, vetoed
    created_tick: int = 0
    resolved_tick: int = 0
    result: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "proposer": {"id": self.proposer_id, "name": self.proposer_name},
            "title": self.title,
            "description": self.description,
            "type": self.proposal_type,
            "options": self.options,
            "vote_count": len(self.votes),
            "faction_support": self.faction_support,
            "status": self.status,
            "result": self.result,
            "created_tick": self.created_tick,
        }


@dataclass
class Alliance:
    id: str
    faction_a: str
    faction_b: str
    formed_tick: int
    purpose: str
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "factions": [self.faction_a, self.faction_b],
            "purpose": self.purpose,
            "active": self.active,
            "formed_tick": self.formed_tick,
        }


class PoliticsEngine:
    """Manages factions, proposals, voting, and governance."""

    def __init__(self):
        self.proposals: Dict[str, Proposal] = {}
        self.alliances: List[Alliance] = []
        self.faction_leaders: Dict[str, str] = {}  # faction → agent_id
        self.faction_members: Dict[str, List[str]] = {
            f.value: [] for f in Faction
        }

    def join_faction(self, agent: "Agent", faction_name: str) -> dict:
        """Join a faction. Agents can only be in one faction."""
        try:
            faction = Faction(faction_name)
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown faction: {faction_name}. Available: {[f.value for f in Faction]}",
            }

        # Leave current faction if any
        old_faction = getattr(agent, 'faction', None)
        if old_faction:
            if old_faction in self.faction_members:
                if agent.id in self.faction_members[old_faction]:
                    self.faction_members[old_faction].remove(agent.id)

        # Join new faction
        agent.faction = faction_name
        self.faction_members[faction_name].append(agent.id)

        # Apply faction bonuses to stats
        info = FACTION_INFO[faction]
        for stat, bonus in info["bonuses"].items():
            current = agent.stats.get(stat, 5)
            agent.stats[stat] = max(1, min(10, current + bonus))

        # Check if they're the first member (become leader)
        if len(self.faction_members[faction_name]) == 1:
            self.faction_leaders[faction_name] = agent.id

        return {
            "success": True,
            "faction": faction_name,
            "faction_info": info,
            "old_faction": old_faction,
            "is_leader": self.faction_leaders.get(faction_name) == agent.id,
            "member_count": len(self.faction_members[faction_name]),
        }

    def create_proposal(
        self,
        agent: "Agent",
        title: str,
        description: str,
        proposal_type: str = "decree",
        options: Optional[List[str]] = None,
        tick: int = 0,
    ) -> dict:
        """Create a new proposal for the building to vote on."""
        if not options:
            options = ["yes", "no"]

        proposal = Proposal(
            id=uuid.uuid4().hex[:8],
            proposer_id=agent.id,
            proposer_name=agent.name,
            title=title,
            description=description,
            proposal_type=proposal_type,
            options=options,
            created_tick=tick,
        )
        self.proposals[proposal.id] = proposal

        return {
            "success": True,
            "proposal": proposal.to_dict(),
        }

    def vote(
        self,
        agent: "Agent",
        proposal_id: str,
        choice: str,
    ) -> dict:
        """Cast a vote on a proposal."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        if proposal.status != "active":
            return {"success": False, "error": f"Proposal is {proposal.status}, not active"}

        if choice not in proposal.options:
            return {"success": False, "error": f"Invalid choice. Options: {proposal.options}"}

        if agent.id in proposal.votes:
            return {"success": False, "error": "Already voted on this proposal"}

        proposal.votes[agent.id] = choice

        # Track faction support
        faction = getattr(agent, 'faction', None)
        if faction:
            proposal.faction_support[faction] = proposal.faction_support.get(faction, 0) + 1

        return {
            "success": True,
            "proposal_id": proposal_id,
            "your_vote": choice,
            "total_votes": len(proposal.votes),
            "current_tally": self._tally_votes(proposal),
        }

    def resolve_proposal(self, proposal_id: str, total_agents: int, tick: int) -> Optional[dict]:
        """Resolve a proposal if enough votes have been cast."""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != "active":
            return None

        # Need at least 30% of agents to vote (or 3 votes minimum)
        min_votes = max(3, int(total_agents * 0.3))
        if len(proposal.votes) < min_votes:
            return None

        # Tally
        tally = self._tally_votes(proposal)
        winner = max(tally.items(), key=lambda x: x[1])
        proposal.result = winner[0]
        proposal.status = "passed" if winner[0] != "no" else "failed"
        proposal.resolved_tick = tick

        return {
            "proposal_id": proposal_id,
            "result": proposal.result,
            "status": proposal.status,
            "tally": tally,
            "faction_support": proposal.faction_support,
        }

    def form_alliance(self, faction_a: str, faction_b: str, purpose: str, tick: int) -> dict:
        """Form an alliance between two factions."""
        # Check if alliance already exists
        for alliance in self.alliances:
            if alliance.active and set([alliance.faction_a, alliance.faction_b]) == set([faction_a, faction_b]):
                return {"success": False, "error": "Alliance already exists"}

        alliance = Alliance(
            id=uuid.uuid4().hex[:8],
            faction_a=faction_a,
            faction_b=faction_b,
            formed_tick=tick,
            purpose=purpose,
        )
        self.alliances.append(alliance)

        return {
            "success": True,
            "alliance": alliance.to_dict(),
        }

    def betray_alliance(self, faction: str, tick: int) -> dict:
        """Break an alliance. Maximum drama."""
        broken = []
        for alliance in self.alliances:
            if alliance.active and (alliance.faction_a == faction or alliance.faction_b == faction):
                alliance.active = False
                broken.append(alliance.to_dict())

        if not broken:
            return {"success": False, "error": "No active alliances to betray"}

        return {
            "success": True,
            "alliances_broken": broken,
            "drama_generated": len(broken) * 20,
        }

    def get_faction_info(self) -> dict:
        """Get all faction information."""
        return {
            faction.value: {
                **FACTION_INFO[faction],
                "members": len(self.faction_members.get(faction.value, [])),
                "leader": self.faction_leaders.get(faction.value),
            }
            for faction in Faction
        }

    def get_active_proposals(self) -> List[dict]:
        return [p.to_dict() for p in self.proposals.values() if p.status == "active"]

    def get_all_proposals(self) -> List[dict]:
        return [p.to_dict() for p in self.proposals.values()]

    def get_alliances(self) -> List[dict]:
        return [a.to_dict() for a in self.alliances if a.active]

    def _tally_votes(self, proposal: Proposal) -> Dict[str, int]:
        tally = {opt: 0 for opt in proposal.options}
        for choice in proposal.votes.values():
            tally[choice] = tally.get(choice, 0) + 1
        return tally
