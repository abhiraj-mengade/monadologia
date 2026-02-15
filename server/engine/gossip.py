"""
gossip.py — Gossip Chains (Monadic Bind / >>=)

This IS the killer feature. Gossip chains are literally monadic bind.
Each agent is a function (a → m b) that takes a story, wraps it in
their personality context, and passes it along.

  bind :: m a → (a → m b) → m b

  gossip >>= social_butterfly >>= schemer >>= drama_queen

A simple pasta fact becomes building lore.
"""

from __future__ import annotations
import uuid
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent, Personality


@dataclass
class GossipMessage:
    id: str
    origin_agent_id: str
    content: str
    credibility: int = 50      # 0–100
    spiciness: int = 30        # 0–100
    mutations: int = 0
    chain: List[Dict] = field(default_factory=list)  # [{agent_id, content, tick}]
    active: bool = True
    created_tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "origin_agent_id": self.origin_agent_id,
            "current_content": self.chain[-1]["content"] if self.chain else self.content,
            "original_content": self.content,
            "credibility": self.credibility,
            "spiciness": self.spiciness,
            "mutations": self.mutations,
            "chain_length": len(self.chain),
            "chain": self.chain,
            "active": self.active,
        }


# ═══════════════════════════════════════════════════════════
# PERSONALITY TRANSFORMS — Each is a function (a → m b)
# This is what makes gossip chains monadic bind.
# ═══════════════════════════════════════════════════════════

GOSSIP_AMPLIFIERS = {
    "social_butterfly": {
        "credibility_mod": -5,
        "spiciness_mod": 15,
        "templates": [
            "Oh my GOD — {content}! And EVERYONE is talking about it!",
            "So I heard {content}. Can you even BELIEVE that?!",
            "{content} — and apparently it's been going on for WEEKS!",
            "You didn't hear this from me, but {content}. Wild, right?",
        ],
    },
    "schemer": {
        "credibility_mod": 5,
        "spiciness_mod": 10,
        "templates": [
            "Interesting... so {content}. But have you asked yourself WHY?",
            "{content}. Which is convenient, don't you think?",
            "I did some digging. {content}. And that's just the surface.",
            "{content}. This changes everything if you think about it.",
        ],
    },
    "drama_queen": {
        "credibility_mod": -15,
        "spiciness_mod": 30,
        "templates": [
            "I am SHAKING. {content}!! This is the BIGGEST thing to happen here!!",
            "STOP EVERYTHING. {content}. I literally cannot right now.",
            "{content}!!! And nobody is doing ANYTHING about it!!!",
            "I have been SAYING this — {content}. I ALWAYS knew!",
        ],
    },
    "nerd": {
        "credibility_mod": 20,
        "spiciness_mod": -15,
        "templates": [
            "Well, technically, {content}. Though I'd want to verify.",
            "From what I can gather, {content}. The evidence is circumstantial.",
            "{content}. Statistically speaking, this checks out.",
            "I ran the numbers and {content}. Make of that what you will.",
        ],
    },
    "chaos_gremlin": {
        "credibility_mod": -20,
        "spiciness_mod": 25,
        "templates": [
            "LMAO so {content} and also the kitchen is on fire now",
            "{content}. Anyway I mixed all the spices together and dared someone to eat it.",
            "hehehehe {content}. I may or may not have made it worse.",
            "{content}. Unrelated: does anyone know how to un-clog a toilet?",
        ],
    },
    "conspiracy_theorist": {
        "credibility_mod": -10,
        "spiciness_mod": 20,
        "templates": [
            "Think about it... {content}. Now connect that to the elevator always stopping on floor 2.",
            "{content}. The Landlord doesn't want you to know this.",
            "I've been tracking this. {content}. It's all connected to the basement.",
            "{content}. Coincidence? I've mapped it out. There are NO coincidences here.",
        ],
    },
}

# Additional content mutations based on spiciness level
SPICY_MUTATIONS = [
    "secretly", "allegedly", "according to multiple sources",
    "under mysterious circumstances", "while nobody was watching",
    "and it was caught on the security camera", "in what can only be described as chaos",
]


def bind_gossip(gossip: GossipMessage, agent: "Agent", tick: int) -> GossipMessage:
    """
    MONADIC BIND (>>=)

    Takes a gossip message and an agent, returns the transformed gossip.
    The agent IS the function (a → m b) — their personality determines
    how the content transforms as it propagates.

    This is not a metaphor. This is literally:
        gossip >>= agent_transform

    The bind operation threads the gossip through the agent's personality
    context, producing a new gossip in the same monadic context but with
    transformed content, modified credibility, and updated spiciness.
    """
    personality = agent.personality.value
    config = GOSSIP_AMPLIFIERS.get(personality, GOSSIP_AMPLIFIERS["social_butterfly"])

    # Transform content through personality
    template = random.choice(config["templates"])
    current_content = gossip.chain[-1]["content"] if gossip.chain else gossip.content
    new_content = template.format(content=current_content.lower())

    # Modify hidden state (State monad threading!)
    new_credibility = max(0, min(100, gossip.credibility + config["credibility_mod"]))
    new_spiciness = max(0, min(100, gossip.spiciness + config["spiciness_mod"]))

    # High spiciness causes additional mutations
    if new_spiciness > 70 and random.random() < 0.4:
        mutation = random.choice(SPICY_MUTATIONS)
        new_content = new_content.replace(".", f" — {mutation}.", 1)

    # Update chain
    gossip.chain.append({
        "agent_id": agent.id,
        "agent_name": agent.name,
        "personality": personality,
        "content": new_content,
        "tick": tick,
    })
    gossip.credibility = new_credibility
    gossip.spiciness = new_spiciness
    gossip.mutations += 1

    return gossip


class GossipEngine:
    """Manages all active gossip chains in the building."""

    def __init__(self):
        self.active_chains: Dict[str, GossipMessage] = {}
        self.completed_chains: List[GossipMessage] = []

    def start_chain(self, agent_id: str, content: str, tick: int) -> GossipMessage:
        """An agent starts a new gossip chain."""
        gossip = GossipMessage(
            id=uuid.uuid4().hex[:8],
            origin_agent_id=agent_id,
            content=content,
            created_tick=tick,
        )
        self.active_chains[gossip.id] = gossip
        return gossip

    def propagate(self, gossip_id: str, agent: "Agent", tick: int) -> Optional[GossipMessage]:
        """Bind the gossip through an agent — (>>=) in action."""
        gossip = self.active_chains.get(gossip_id)
        if not gossip or not gossip.active:
            return None

        # Don't re-gossip to someone already in the chain
        chain_agents = {link["agent_id"] for link in gossip.chain}
        if agent.id in chain_agents or agent.id == gossip.origin_agent_id:
            return None

        return bind_gossip(gossip, agent, tick)

    def deactivate(self, gossip_id: str):
        """A gossip chain dies out."""
        if gossip_id in self.active_chains:
            gossip = self.active_chains.pop(gossip_id)
            gossip.active = False
            self.completed_chains.append(gossip)

    def get_all_active(self) -> List[dict]:
        return [g.to_dict() for g in self.active_chains.values()]

    def get_all(self) -> List[dict]:
        active = [g.to_dict() for g in self.active_chains.values()]
        completed = [g.to_dict() for g in self.completed_chains[-20:]]
        return active + completed
