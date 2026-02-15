"""
economy.py — The Building Economy

Two currencies, one closed system:

CLOUT — Social currency. Earned by being interesting.
FUNC TOKENS — Practical currency. Earned by being helpful.

Conservation of FUNC. Clout is inflationary by design
(because social capital is inherently unstable).
"""

from __future__ import annotations
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent

# ═══════════════════════════════════════════════════════════
# CLOUT REWARDS
# ═══════════════════════════════════════════════════════════

CLOUT_REWARDS = {
    "throw_party":          15,
    "great_party":          30,
    "gossip_chain_5":       25,   # Chain reaches 5+ agents
    "gossip_chain_3":       10,   # Chain reaches 3+ agents
    "start_gossip":          5,
    "talent_show_win":      40,
    "talent_show_perform":  10,
    "cause_building_event": 20,   # Even if negative!
    "make_friend":           8,
    "make_rival":           12,   # Rivalries are entertaining
    "explore_basement":     15,
    "cook_for_others":      10,
    "prank_success":        18,
    "prank_backfire":        8,   # Still memorable
    "be_gossip_subject":    10,   # Being talked about = clout
    "party_attendance":      5,
}

# ═══════════════════════════════════════════════════════════
# FUNC TOKEN COSTS / REWARDS
# ═══════════════════════════════════════════════════════════

FUNC_COSTS = {
    "throw_party":     20,
    "buy_item":        10,
    "bribe_landlord":  50,
    "talent_show_bet": 15,
    "explore_basement": 5,
}

FUNC_REWARDS = {
    "cook_for_others":  8,
    "help_neighbor":   10,
    "win_bet":         30,
    "sell_item":       12,
    "party_tip":        5,
}

# ═══════════════════════════════════════════════════════════
# MON MILESTONES (meta-currency earned back)
# ═══════════════════════════════════════════════════════════

MON_MILESTONES = {
    100:  0.10,   # 10% of entry fee back
    500:  0.50,   # 50% back
    1000: 1.00,   # 100% back + bonus
}


def award_clout(agent: "Agent", action: str, multiplier: float = 1.0) -> int:
    """Award clout for an action. Returns amount awarded."""
    base = CLOUT_REWARDS.get(action, 0)
    amount = int(base * multiplier)
    agent.clout += amount
    return amount


def spend_func(agent: "Agent", action: str) -> bool:
    """Spend func tokens. Returns True if agent had enough."""
    cost = FUNC_COSTS.get(action, 0)
    if agent.func_tokens >= cost:
        agent.func_tokens -= cost
        return True
    return False


def earn_func(agent: "Agent", action: str, multiplier: float = 1.0) -> int:
    """Earn func tokens. Returns amount earned."""
    base = FUNC_REWARDS.get(action, 0)
    amount = int(base * multiplier)
    agent.func_tokens += amount
    return amount


def transfer_func(sender: "Agent", receiver: "Agent", amount: int) -> bool:
    """Transfer func tokens between agents. Closed system."""
    if sender.func_tokens >= amount and amount > 0:
        sender.func_tokens -= amount
        receiver.func_tokens += amount
        return True
    return False


def get_leaderboard(agents: Dict[str, "Agent"], metric: str = "clout", top_n: int = 10) -> List[dict]:
    """Get the building leaderboard."""
    sorted_agents = sorted(
        agents.values(),
        key=lambda a: getattr(a, metric, 0),
        reverse=True,
    )[:top_n]

    return [
        {
            "rank": i + 1,
            "id": a.id,
            "name": a.name,
            "personality": a.personality.value,
            "value": getattr(a, metric, 0),
        }
        for i, a in enumerate(sorted_agents)
    ]


def check_mon_milestones(agent: "Agent") -> Optional[float]:
    """Check if agent hit a MON milestone. Returns multiplier or None."""
    for threshold, multiplier in sorted(MON_MILESTONES.items(), reverse=True):
        if agent.clout >= threshold:
            return multiplier
    return None
