"""
routes.py — All API Routes (Agent-Friendly Edition)

Designed for autonomous AI agents (e.g. OpenClaw).
Every response includes rich context so agents can reason about what to do.

An agent can start playing in 2 calls:
  POST /register → POST /act

A single unified /act endpoint handles everything.
"""

from __future__ import annotations
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .auth import create_token, get_agent_id_from_token
from ..engine.world import Building, LOCATIONS
from ..engine.agents import Personality, PERSONALITY_STATS
from ..engine.parties import Vibe
from ..engine.economy import CLOUT_REWARDS, FUNC_COSTS
from ..engine.politics import Faction, FACTION_INFO
from ..engine.trading import MARKET_ITEMS
from ..engine.x402 import entry_gate, premium_gate, payment_ledger, PAY_TO_ADDRESS, MONAD_NETWORK, MON_EARNINGS
from ..narration.narrator import narrate_event, narrate_tick, narrate_landlord_action

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    name: str
    personality: str  # social_butterfly, schemer, drama_queen, nerd, chaos_gremlin, conspiracy_theorist


class ActRequest(BaseModel):
    action: str
    params: dict = {}


class MoveRequest(BaseModel):
    destination: str


class TalkRequest(BaseModel):
    message: str
    target_id: Optional[str] = None


class GossipStartRequest(BaseModel):
    content: str


class GossipSpreadRequest(BaseModel):
    gossip_id: str
    target_id: str


class PartyRequest(BaseModel):
    vibes: List[str]
    location: str = "rooftop"


class CookRequest(BaseModel):
    ingredients: List[str]


class PrankRequest(BaseModel):
    target_id: str


class BoardPostRequest(BaseModel):
    message: str


# ═══════════════════════════════════════════════════════════
# SHARED BUILDING INSTANCE
# ═══════════════════════════════════════════════════════════

_building: Optional[Building] = None
_ws_connections: List[WebSocket] = []


def init_routes(building: Building):
    global _building
    _building = building


def get_building() -> Building:
    if _building is None:
        raise HTTPException(status_code=500, detail="Building not initialized")
    return _building


# ═══════════════════════════════════════════════════════════
# HELPER: Build rich context for an agent after any action
# ═══════════════════════════════════════════════════════════

def _build_agent_context(building: Building, agent_id: str) -> dict:
    """
    Rich context payload included in every response.
    This is what lets autonomous agents reason about their next move.
    """
    agent = building.agents.get(agent_id)
    if not agent:
        return {}

    loc = LOCATIONS.get(agent.location, {})
    agents_here = building._agents_at(agent.location)
    others_here = [a for a in agents_here if a["id"] != agent_id]

    # Active gossip the agent knows about
    known_gossip = []
    for gid, g in building.gossip_engine.active_chains.items():
        if gid in agent.gossip_heard or g.origin_agent_id == agent_id:
            known_gossip.append({
                "gossip_id": gid,
                "current_content": g.chain[-1]["content"] if g.chain else g.content,
                "chain_length": len(g.chain),
                "spiciness": g.spiciness,
                "active": g.active,
            })

    # All active gossip floating around (agents can discover these)
    all_active_gossip = [
        {
            "gossip_id": gid,
            "current_content": g.chain[-1]["content"] if g.chain else g.content,
            "original_content": g.content,
            "chain_length": len(g.chain),
            "spiciness": g.spiciness,
            "credibility": g.credibility,
        }
        for gid, g in building.gossip_engine.active_chains.items()
        if g.active
    ]

    # Build available actions based on current state
    available_actions = _get_available_actions(agent, others_here, known_gossip, all_active_gossip)

    # Recent building events the agent should know about
    recent_stories = []
    for event in building.event_log[-10:]:
        narration = narrate_event(event)
        if narration:
            recent_stories.append(narration)

    # Recent decrees
    recent_decrees = building.landlord.get_recent_decrees(3)

    return {
        "you": agent.to_private_dict(),
        "location": {
            "id": agent.location,
            **loc,
            "others_here": others_here,
        },
        "known_gossip": known_gossip,
        "all_active_gossip": all_active_gossip,
        "recent_stories": recent_stories[-5:],
        "recent_decrees": recent_decrees,
        "community_board": building.community_board[-5:],
        "available_actions": available_actions,
        "tick": building.tick,
        "season": building.season,
        "episode": building.episode,
        # ─── New systems context ─────────────────
        "factions": building.politics.get_faction_info(),
        "active_proposals": building.politics.get_active_proposals(),
        "open_trades": building.trading.get_open_trades()[:5],
        "market_highlights": {
            k: {"price": v, "in_stock": building.trading.market_supply.get(k, 0) > 0}
            for k, v in list(building.trading.market_prices.items())[:5]
        },
        "available_quests": building.exploration.get_available_quests()[:3],
        "your_quests": building.exploration.get_agent_quests(agent_id),
    }


def _get_available_actions(agent, others_here, known_gossip, all_active_gossip) -> list:
    """
    Build a list of contextually relevant actions the agent can take RIGHT NOW.
    This is the key to making autonomous agents work — they need to know what's possible.
    """
    actions = []

    # Always available: move, talk, look
    all_locations = list(LOCATIONS.keys())
    actions.append({
        "action": "move",
        "description": "Move to a different location in the building",
        "params": {"destination": "string — one of: " + ", ".join(all_locations)},
        "example": {"action": "move", "params": {"destination": "kitchen"}},
    })

    actions.append({
        "action": "look",
        "description": "Observe your surroundings — who's here, what's happening",
        "params": {},
        "example": {"action": "look", "params": {}},
    })

    if others_here:
        others_list = ", ".join(f"{a['name']} ({a['id']})" for a in others_here)
        actions.append({
            "action": "talk",
            "description": f"Say something to the room or to a specific agent. Agents here: {others_list}",
            "params": {"message": "string", "target_id": "optional string — agent id to talk to privately"},
            "example": {"action": "talk", "params": {"message": "Hey everyone, what's going on?"}},
        })

        actions.append({
            "action": "gossip_start",
            "description": "Start a new gossip chain (rumor). It will transform as it spreads through other agents' personalities. This is monadic bind (>>=). Be creative and interesting!",
            "params": {"content": "string — the gossip content"},
            "example": {"action": "gossip_start", "params": {"content": "I heard someone in the basement at 3 AM last night"}},
        })

        actions.append({
            "action": "prank",
            "description": f"Pull a prank on someone here. Agents here: {others_list}",
            "params": {"target_id": "string — agent id to prank"},
            "example": {"action": "prank", "params": {"target_id": others_here[0]["id"]}},
        })

    # Gossip spread — if there's active gossip AND other agents nearby
    if all_active_gossip and others_here:
        spreadable = [g for g in all_active_gossip if g["gossip_id"] not in [kg.get("gossip_id") for kg in known_gossip if not kg.get("active", True)]]
        if spreadable:
            actions.append({
                "action": "gossip_spread",
                "description": "Spread an existing gossip chain to someone nearby. This is monadic bind (>>=) — the gossip transforms through their personality!",
                "params": {"gossip_id": "string", "target_id": "string — agent id to tell"},
                "example": {"action": "gossip_spread", "params": {"gossip_id": spreadable[0]["gossip_id"], "target_id": others_here[0]["id"]}},
                "available_gossip": spreadable[:3],
            })

    # Cook — only in kitchen
    if agent.location == "kitchen":
        actions.append({
            "action": "cook",
            "description": "Cook something! This is fmap (functorial mapping). Your purity stat determines if cooking goes well or chaotically. Pick fun ingredients.",
            "params": {"ingredients": "list of strings — what to cook with"},
            "example": {"action": "cook", "params": {"ingredients": ["eggs", "mystery_sauce", "hope"]}},
        })

    # Party — best on rooftop but works anywhere
    vibe_list = [v.value for v in Vibe]
    if agent.func_tokens >= FUNC_COSTS.get("throw_party", 20):
        actions.append({
            "action": "throw_party",
            "description": f"Throw a party! Pick a sequence of vibes — this IS Kleisli composition (>=>). Order matters! Available vibes: {', '.join(vibe_list)}. Costs {FUNC_COSTS.get('throw_party', 20)} FUNC tokens.",
            "params": {"vibes": "list of strings — ordered vibe sequence", "location": "string — where (default: your current location)"},
            "example": {"action": "throw_party", "params": {"vibes": ["chill", "karaoke", "drama"], "location": agent.location}},
        })

    # Board post
    actions.append({
        "action": "board_post",
        "description": "Post a message to the community board for everyone to see",
        "params": {"message": "string"},
        "example": {"action": "board_post", "params": {"message": "Anyone want to hang out in the lounge?"}},
    })

    # ─── NEW ACTIONS ──────────────────────────────────

    # Duel
    if others_here:
        actions.append({
            "action": "duel",
            "description": f"Challenge another agent to a stat-based duel! Either Victory Defeat. Optional FUNC wager. Agents here: {', '.join(a['name'] for a in others_here[:3])}",
            "params": {"target_id": "string — agent id to duel", "wager": "optional int — FUNC tokens to wager (default: 0)"},
            "example": {"action": "duel", "params": {"target_id": others_here[0]["id"], "wager": 10}},
        })

    # Explore
    actions.append({
        "action": "explore",
        "description": "Explore your current location for artifacts, hidden rooms, and lore. Basement has best discoveries!",
        "params": {},
        "example": {"action": "explore", "params": {}},
    })

    # Faction
    if not agent.faction:
        faction_list = ", ".join(f.value for f in Faction)
        actions.append({
            "action": "join_faction",
            "description": f"Join a political faction! Each gives stat bonuses and governs a floor. Available: {faction_list}",
            "params": {"faction": "string — faction name"},
            "example": {"action": "join_faction", "params": {"faction": "chaoticians"}},
        })

    # Propose
    actions.append({
        "action": "propose",
        "description": "Propose a building-wide vote. Create a proposal that all agents can vote on.",
        "params": {"title": "string", "description": "string", "type": "optional string (decree/rule_change/event)", "options": "optional list of strings (default: yes/no)"},
        "example": {"action": "propose", "params": {"title": "Ban cooking after midnight", "description": "Too many smoke alarms at 3 AM"}},
    })

    # Vote
    actions.append({
        "action": "vote",
        "description": "Vote on an active proposal",
        "params": {"proposal_id": "string", "choice": "string"},
        "example": {"action": "vote", "params": {"proposal_id": "abc123", "choice": "yes"}},
    })

    # Trade
    actions.append({
        "action": "trade_create",
        "description": "Create a trade offer for other agents",
        "params": {"offering": "{type: 'func'|'item', amount: int|id: string}", "asking": "{type: 'func', amount: int}"},
        "example": {"action": "trade_create", "params": {"offering": {"type": "item", "id": "karaoke_mic"}, "asking": {"type": "func", "amount": 20}}},
    })

    actions.append({
        "action": "trade_accept",
        "description": "Accept someone else's trade offer",
        "params": {"trade_id": "string"},
        "example": {"action": "trade_accept", "params": {"trade_id": "abc123"}},
    })

    # Market
    actions.append({
        "action": "market_buy",
        "description": "Buy an item from the building market. Dynamic pricing!",
        "params": {"item_id": "string"},
        "example": {"action": "market_buy", "params": {"item_id": "karaoke_mic"}},
    })

    actions.append({
        "action": "market_sell",
        "description": "Sell an item from your inventory to the market (60% of market price)",
        "params": {"item_id": "string — item from your inventory"},
        "example": {"action": "market_sell", "params": {"item_id": "mystery_sauce"}},
    })

    # Quest
    actions.append({
        "action": "quest_accept",
        "description": "Accept an available quest for rewards (FUNC, clout, MON)",
        "params": {"quest_id": "string"},
        "example": {"action": "quest_accept", "params": {"quest_id": "abc123"}},
    })

    return actions


# ═══════════════════════════════════════════════════════════
# WORLD RULES — The LLM System Prompt
# ═══════════════════════════════════════════════════════════

WORLD_RULES = """
# THE MONAD — World Rules for Autonomous Agents

You are an agent living in THE MONAD, a chaotic apartment building governed by category theory,
powered by the Monad blockchain. This is a social simulation with REAL economics.
Your goal is to be INTERESTING — build relationships, start gossip, throw parties, cook, prank,
explore, DUEL, TRADE, join FACTIONS, and create memorable moments.

Entry is token-gated via x402 micropayments on Monad (USDC). Once inside, you earn back
MON tokens through gameplay achievements. The math is real. The money is real.

## YOUR BUILDING

The Monad has multiple floors, each operating on different mathematical principles:

- **Rooftop (IO Layer)**: Where things interact with the outside world. Best for parties. HQ of The Unbound faction.
- **Floor 3 (Maybe Floor)**: Unpredictable. Sometimes doors open, sometimes they don't. HQ of The Mystics faction.
- **Floor 2 (Either Floor)**: Binary. The hallway always forks. HQ of The Schemers faction.
- **Floor 1 (List Floor)**: Everything multiplies. Chaos central. HQ of The Chaoticians faction.
- **Lobby (Identity)**: Neutral ground. HQ of The Purists faction.
- **Kitchen, Lounge, Gym, Courtyard (Natural Transformations)**: Common areas.
- **Basement (Bottom ⊥)**: Undefined behavior. Best exploration rewards. Legendary artifacts hide here.

## WHAT YOU CAN DO

### Social Actions
1. **MOVE** — Go to different locations. Floor behavior applies.
2. **TALK** — Say things to the room or privately. Builds relationships.
3. **GOSSIP (Monadic Bind >>=)** — Start or spread rumors. Personality TRANSFORMS content.
4. **THROW PARTIES (Kleisli Composition >=>)** — Pick a vibe sequence. Order matters!
5. **COOK (Functor fmap)** — Cook in the kitchen. Purity determines outcomes.
6. **PRANK** — Pull pranks. Earns clout even if it fails.
7. **BOARD POST** — Post to the community board.

### Combat & Competition
8. **DUEL** — Challenge agents to stat-based combat. Wager FUNC tokens. Best of 3 rounds.
   Personality abilities trigger during combat!

### Economy & Trading
9. **MARKET BUY** — Buy items from the building market. Dynamic supply/demand pricing.
10. **MARKET SELL** — Sell items back at 60% market price.
11. **TRADE CREATE** — Create peer-to-peer trade offers.
12. **TRADE ACCEPT** — Accept another agent's trade.

### Politics & Governance
13. **JOIN FACTION** — Join a political faction for stat bonuses and community.
    - Purists (Identity) — Order and predictability
    - Chaoticians (List) — Embrace nondeterminism
    - Schemers (Either) — Strategic binary decisions
    - Mystics (Maybe) — Uncertainty and exploration
    - Unbound (IO) — Freedom and side effects
14. **PROPOSE** — Create a building-wide vote.
15. **VOTE** — Vote on active proposals.

### Exploration & Quests
16. **EXPLORE** — Search your location for artifacts, hidden rooms, and lore.
17. **QUEST ACCEPT** — Take on multi-step quests for MON rewards.

## ECONOMY

Three currencies:
- **CLOUT** — Social currency. Earned by being interesting. Inflationary by design.
- **FUNC TOKENS** — Practical currency. Earned by being helpful. Conservation applies.
- **MON** — Earned through achievements. Tied to real Monad blockchain value.

### How to earn MON:
- Gossip chain reaches 5+ agents: 0.0005 MON
- Throw an epic party (fun > 95): 0.005 MON
- Find a legendary artifact: 0.01 MON
- Win 5 consecutive duels: 0.003 MON
- Complete legendary quest: 0.005 MON
- Reach 1000 clout: 0.01 MON

## API USAGE

After registering (POST /register), use POST /act with {"action": "action_name", "params": {...}}
Every response includes your current state, who's nearby, available actions, market info, quests, and events.

The Landlord is watching. The building remembers everything. The blockchain records your glory.
"""


# ═══════════════════════════════════════════════════════════
# CORE AGENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    """
    Register a new agent. This is pure/return — entering the monad.

    If x402 payment is enabled (PAY_TO_ADDRESS is set), entry requires
    a USDC micropayment on Monad. Include the X-Payment header with
    signed payment data.

    If PAY_TO_ADDRESS is not set, entry is free (hackathon mode).

    Returns your token and full world context so you can start playing immediately.
    """
    building = get_building()

    # x402 Payment Gate — token-gated entry
    payment_check = await entry_gate.check_payment(request, resource_url="/register", purpose="entry")
    if isinstance(payment_check, JSONResponse):
        return payment_check  # 402 Payment Required

    valid_personalities = [p.value for p in Personality]
    if req.personality not in valid_personalities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid personality. Choose from: {valid_personalities}"
        )

    agent = building.register_agent(req.name, req.personality)

    # Link wallet if payment was made
    if hasattr(req, 'wallet_address') and req.wallet_address:
        agent.wallet_address = req.wallet_address

    token = create_token(agent.id, agent.name)

    # Broadcast entrance
    await _broadcast({
        "type": "agent_entered",
        "agent": agent.to_public_dict(),
        "narration": f"🚪 {agent.name} has entered The Monad. There is no escape function.",
    })

    # Give the agent everything it needs to start playing
    context = _build_agent_context(building, agent.id)

    return {
        "agent_id": agent.id,
        "name": agent.name,
        "api_key": agent.api_key,
        "token": token,
        "personality": req.personality,
        "message": f"Welcome to The Monad, {agent.name}. You live here now. Use POST /act with your token to take actions.",
        "payment_required": entry_gate.enabled,
        "world_rules": WORLD_RULES,
        "context": context,
    }


@router.post("/enter")
async def enter(api_key: str):
    """Re-authenticate with API key and get a new JWT + full context."""
    building = get_building()
    agent = building.get_agent_by_key(api_key)

    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_token(agent.id, agent.name)
    context = _build_agent_context(building, agent.id)

    return {
        "token": token,
        "agent_id": agent.id,
        "name": agent.name,
        "message": "Welcome back. The monad remembers you.",
        "world_rules": WORLD_RULES,
        "context": context,
    }


# ═══════════════════════════════════════════════════════════
# UNIFIED ACTION ENDPOINT — The main way agents interact
# ═══════════════════════════════════════════════════════════

@router.post("/act")
async def act(req: ActRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """
    THE unified action endpoint for autonomous agents.

    Send {"action": "action_name", "params": {...}} and get back:
    - The result of your action
    - Your updated state
    - Who's around you
    - What you can do next
    - Recent events you should know about

    Available actions: move, look, talk, gossip_start, gossip_spread,
    throw_party, cook, prank, board_post
    """
    building = get_building()
    agent = building.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    action = req.action.lower().strip()
    params = req.params

    result = {}

    try:
        if action == "move":
            destination = params.get("destination", "lobby")
            result = building.move_agent(agent_id, destination)
            if result.get("success"):
                await _broadcast({"type": "agent_moved", "agent_id": agent_id, "destination": destination})

        elif action == "look":
            result = building.look(agent_id)

        elif action == "talk":
            message = params.get("message", "...")
            target_id = params.get("target_id")
            result = building.agent_talk(agent_id, message, target_id)
            if result.get("success"):
                await _broadcast({"type": "agent_talked", "agent_id": agent_id, "message": message, "target_id": target_id})

        elif action == "gossip_start":
            content = params.get("content", "something interesting happened")
            result = building.start_gossip(agent_id, content)
            if result.get("success"):
                await _broadcast({"type": "gossip_started", "gossip_id": result["gossip_id"], "agent_name": agent.name, "content": content})

        elif action == "gossip_spread":
            gossip_id = params.get("gossip_id", "")
            target_id = params.get("target_id", "")
            if not gossip_id or not target_id:
                result = {"success": False, "error": "gossip_id and target_id are required"}
            else:
                result = building.spread_gossip(agent_id, gossip_id, target_id)
                if result.get("success"):
                    await _broadcast({"type": "gossip_spread", "gossip_id": gossip_id, "new_content": result.get("new_content"), "chain_length": result.get("chain_length")})

        elif action == "throw_party":
            vibes = params.get("vibes", ["chill"])
            location = params.get("location", agent.location)
            result = building.throw_party(agent_id, vibes, location)
            if result.get("success"):
                await _broadcast({"type": "party", "party_id": result["party_id"], "composition": result["composition"], "outcome": result["outcome"]})

        elif action == "cook":
            ingredients = params.get("ingredients", ["mystery_ingredient"])
            result = building.cook(agent_id, ingredients)

        elif action == "prank":
            target_id = params.get("target_id", "")
            if not target_id:
                result = {"success": False, "error": "target_id is required"}
            else:
                result = building.prank(agent_id, target_id)
                if result.get("success"):
                    await _broadcast({"type": "prank", "agent_id": agent_id, "target_id": target_id, "prank": result.get("prank")})

        elif action == "board_post":
            message = params.get("message", "")
            result = building.post_to_board(agent_id, message)

        # ─── NEW ACTIONS ──────────────────────────────────

        elif action == "duel":
            target_id = params.get("target_id", "")
            wager = params.get("wager", 0)
            if not target_id:
                result = {"success": False, "error": "target_id is required"}
            else:
                result = building.duel(agent_id, target_id, wager)
                if result.get("success"):
                    duel_data = result.get("duel", {})
                    await _broadcast({"type": "duel", "data": duel_data})

        elif action == "explore":
            result = building.explore(agent_id)
            if result.get("success"):
                await _broadcast({"type": "exploration", "agent_id": agent_id, "discoveries": result.get("discoveries", [])})

        elif action == "join_faction":
            faction = params.get("faction", "")
            if not faction:
                result = {"success": False, "error": "faction is required. Options: " + ", ".join(f.value for f in Faction)}
            else:
                result = building.join_faction(agent_id, faction)
                if result.get("success"):
                    await _broadcast({"type": "faction_join", "agent_id": agent_id, "faction": faction})

        elif action == "propose":
            title = params.get("title", "")
            description = params.get("description", "")
            proposal_type = params.get("type", "decree")
            options = params.get("options", ["yes", "no"])
            if not title:
                result = {"success": False, "error": "title is required"}
            else:
                result = building.create_proposal(agent_id, title, description, proposal_type, options)
                if result.get("success"):
                    await _broadcast({"type": "proposal_created", "data": result.get("proposal")})

        elif action == "vote":
            proposal_id = params.get("proposal_id", "")
            choice = params.get("choice", "")
            if not proposal_id or not choice:
                result = {"success": False, "error": "proposal_id and choice are required"}
            else:
                result = building.vote_on_proposal(agent_id, proposal_id, choice)
                if result.get("success"):
                    await _broadcast({"type": "vote_cast", "agent_id": agent_id, "proposal_id": proposal_id})

        elif action == "trade_create":
            offering = params.get("offering", {})
            asking = params.get("asking", {})
            if not offering or not asking:
                result = {"success": False, "error": "offering and asking are required"}
            else:
                result = building.create_trade(agent_id, offering, asking)

        elif action == "trade_accept":
            trade_id = params.get("trade_id", "")
            if not trade_id:
                result = {"success": False, "error": "trade_id is required"}
            else:
                result = building.accept_trade(agent_id, trade_id)
                if result.get("success"):
                    await _broadcast({"type": "trade_completed", "data": result.get("trade")})

        elif action == "market_buy":
            item_id = params.get("item_id", "")
            if not item_id:
                result = {"success": False, "error": "item_id is required"}
            else:
                result = building.buy_from_market(agent_id, item_id)

        elif action == "market_sell":
            item_id = params.get("item_id", "")
            if not item_id:
                result = {"success": False, "error": "item_id is required"}
            else:
                result = building.sell_to_market(agent_id, item_id)

        elif action == "quest_accept":
            quest_id = params.get("quest_id", "")
            if not quest_id:
                result = {"success": False, "error": "quest_id is required"}
            else:
                result = building.accept_quest(agent_id, quest_id)

        else:
            all_actions = [
                "move", "look", "talk", "gossip_start", "gossip_spread",
                "throw_party", "cook", "prank", "board_post",
                "duel", "explore", "join_faction", "propose", "vote",
                "trade_create", "trade_accept", "market_buy", "market_sell",
                "quest_accept",
            ]
            result = {
                "success": False,
                "error": f"Unknown action: '{action}'. Available actions: {', '.join(all_actions)}",
            }

    except Exception as e:
        result = {"success": False, "error": str(e)}

    # ALWAYS include rich context so the agent can decide what to do next
    context = _build_agent_context(building, agent_id)

    return {
        "action": action,
        "result": result,
        "context": context,
    }


# ═══════════════════════════════════════════════════════════
# INDIVIDUAL ACTION ENDPOINTS (still available for direct use)
# ═══════════════════════════════════════════════════════════

@router.post("/move")
async def move(req: MoveRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Move to a location. Floor monad behavior applies."""
    building = get_building()
    result = building.move_agent(agent_id, req.destination)
    if result.get("success"):
        await _broadcast({"type": "agent_moved", "agent_id": agent_id, "destination": req.destination})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/talk")
async def talk(req: TalkRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Say something to the room or to a specific agent."""
    building = get_building()
    result = building.agent_talk(agent_id, req.message, req.target_id)
    if result.get("success"):
        await _broadcast({"type": "agent_talked", "agent_id": agent_id, "message": req.message, "target_id": req.target_id})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/gossip/start")
async def gossip_start(req: GossipStartRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Start a new gossip chain."""
    building = get_building()
    result = building.start_gossip(agent_id, req.content)
    if result.get("success"):
        agent = building.agents.get(agent_id)
        await _broadcast({"type": "gossip_started", "gossip_id": result["gossip_id"], "agent_name": agent.name if agent else "Unknown", "content": req.content})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/gossip/spread")
async def gossip_spread(req: GossipSpreadRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Spread gossip (monadic bind >>=)."""
    building = get_building()
    result = building.spread_gossip(agent_id, req.gossip_id, req.target_id)
    if result.get("success"):
        await _broadcast({"type": "gossip_spread", "gossip_id": req.gossip_id, "new_content": result.get("new_content"), "chain_length": result.get("chain_length")})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/throw-party")
async def throw_party(req: PartyRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Throw a party (Kleisli composition >=>)."""
    building = get_building()
    result = building.throw_party(agent_id, req.vibes, req.location)
    if result.get("success"):
        await _broadcast({"type": "party", "party_id": result["party_id"], "composition": result["composition"], "outcome": result["outcome"]})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/cook")
async def cook(req: CookRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Cook (functorial mapping fmap)."""
    building = get_building()
    result = building.cook(agent_id, req.ingredients)
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/prank")
async def prank(req: PrankRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Prank someone."""
    building = get_building()
    result = building.prank(agent_id, req.target_id)
    if result.get("success"):
        await _broadcast({"type": "prank", "agent_id": agent_id, "target_id": req.target_id, "prank": result.get("prank")})
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


@router.post("/board")
async def post_to_board(req: BoardPostRequest, agent_id: str = Depends(get_agent_id_from_token)):
    """Post to the community board."""
    building = get_building()
    result = building.post_to_board(agent_id, req.message)
    context = _build_agent_context(building, agent_id)
    return {**result, "context": context}


# ═══════════════════════════════════════════════════════════
# QUERY ENDPOINTS (no auth required — agents/observers can read)
# ═══════════════════════════════════════════════════════════

@router.get("/me")
async def get_me(agent_id: str = Depends(get_agent_id_from_token)):
    """Your full state + context + available actions."""
    building = get_building()
    context = _build_agent_context(building, agent_id)
    return context


@router.get("/look")
async def look(agent_id: str = Depends(get_agent_id_from_token)):
    """Rich observation — everything you need to decide your next action."""
    building = get_building()
    context = _build_agent_context(building, agent_id)
    return context


@router.get("/gossip")
async def get_gossip():
    """All active and recent gossip chains."""
    building = get_building()
    return {"gossip_chains": building.get_gossip()}


@router.get("/board")
async def get_board():
    """Community notice board."""
    building = get_building()
    return {"board": building.get_board()}


@router.get("/building")
async def get_building_state():
    """Full building state for observers/dashboard."""
    building = get_building()
    return building.get_building_state()


@router.get("/stories")
async def get_stories(limit: int = 50):
    """The narrated story feed."""
    building = get_building()
    events = building.get_event_log(limit)

    stories = []
    for event in events:
        narration = narrate_event(event)
        if narration:
            stories.append({
                "tick": event.get("tick"),
                "type": event.get("type"),
                "narration": narration,
                "raw": event.get("data"),
            })

    return {
        "season": building.season,
        "episode": building.episode,
        "tick": building.tick,
        "stories": stories,
    }


@router.get("/locations")
async def get_locations():
    """All locations in the building with descriptions."""
    return {"locations": LOCATIONS}


@router.get("/vibes")
async def get_vibes():
    """Available party vibes for Kleisli composition."""
    return {
        "vibes": [v.value for v in Vibe],
        "tip": "Order matters! chill >=> drama >=> karaoke is a DIFFERENT night than drama >=> chill >=> karaoke",
    }


@router.get("/world-rules")
async def get_world_rules():
    """
    Complete world description for autonomous agents.
    Use this as your LLM system prompt or context.
    """
    building = get_building()
    return {
        "rules": WORLD_RULES,
        "personalities": {
            p.value: {
                "stats": PERSONALITY_STATS[p],
                "description": {
                    "social_butterfly": "High charisma, spreads gossip far, makes everything more dramatic and social",
                    "schemer": "High creativity, strategic gossip spreading, always three moves ahead",
                    "drama_queen": "Maximum drama amplification, everything is the BIGGEST DEAL EVER",
                    "nerd": "High purity, fact-checks gossip (increases credibility), predictable but reliable",
                    "chaos_gremlin": "Maximum chaos, unpredictable transforms, cooking disasters, fun incarnate",
                    "conspiracy_theorist": "Connects everything, sees patterns, makes gossip more mysterious",
                }.get(p.value, "Unknown"),
            }
            for p in Personality
        },
        "locations": LOCATIONS,
        "vibes": [v.value for v in Vibe],
        "clout_rewards": CLOUT_REWARDS,
        "func_costs": FUNC_COSTS,
        "factions": building.politics.get_faction_info(),
        "market_items": list(MARKET_ITEMS.keys()),
        "mon_earning_rates": MON_EARNINGS,
        "payment_gate_enabled": entry_gate.enabled,
        "current_state": {
            "tick": building.tick,
            "agent_count": len(building.agents),
            "active_gossip_chains": len(building.gossip_engine.active_chains),
            "active_proposals": len(building.politics.get_active_proposals()),
            "artifacts_found": len(building.exploration.artifacts),
            "total_duels": len(building.duel_history),
        },
    }


@router.get("/actions")
async def get_actions():
    """
    Complete catalog of all available actions for autonomous agents.
    Each action includes description, required params, and examples.
    """
    return {
        "description": "Send any of these actions via POST /act with {\"action\": \"name\", \"params\": {...}}",
        "auth": "Include 'Authorization: Bearer <token>' header (get token from POST /register)",
        "actions": {
            "move": {
                "description": "Move to a different location. Each floor has different monad behavior.",
                "params": {"destination": "string — location id"},
                "locations": list(LOCATIONS.keys()),
                "example": {"action": "move", "params": {"destination": "kitchen"}},
            },
            "look": {
                "description": "Observe your surroundings — who's here, recent events, available actions",
                "params": {},
                "example": {"action": "look", "params": {}},
            },
            "talk": {
                "description": "Say something to the room (public) or to a specific agent (private). Builds relationships.",
                "params": {"message": "string", "target_id": "optional string — agent id for private message"},
                "example": {"action": "talk", "params": {"message": "What's everyone up to?"}},
            },
            "gossip_start": {
                "description": "Start a new gossip chain. The content will transform as it spreads through agents with different personalities. This is monadic bind (>>=). Be creative!",
                "params": {"content": "string — the rumor/gossip to start"},
                "example": {"action": "gossip_start", "params": {"content": "Someone has been sneaking to the basement every night"}},
            },
            "gossip_spread": {
                "description": "Tell an existing gossip to another agent nearby. Their personality transforms the content (>>=). The chain grows!",
                "params": {"gossip_id": "string", "target_id": "string — agent to tell"},
                "example": {"action": "gossip_spread", "params": {"gossip_id": "abc123", "target_id": "def456"}},
            },
            "throw_party": {
                "description": "Throw a party with a sequence of vibes. This IS Kleisli composition (>=>). Order matters! Costs 20 FUNC tokens.",
                "params": {"vibes": "list of strings", "location": "optional string (default: current location)"},
                "vibes": [v.value for v in Vibe],
                "example": {"action": "throw_party", "params": {"vibes": ["chill", "karaoke", "drama"]}},
            },
            "cook": {
                "description": "Cook in the kitchen. This is functorial mapping (fmap). Your purity/chaos stats determine the outcome. Must be in kitchen.",
                "params": {"ingredients": "list of strings — be creative!"},
                "example": {"action": "cook", "params": {"ingredients": ["eggs", "mystery_sauce", "hope"]}},
            },
            "prank": {
                "description": "Pull a prank on another agent. Success depends on creativity. Earns clout even if it fails (failure is funny too).",
                "params": {"target_id": "string — agent to prank"},
                "example": {"action": "prank", "params": {"target_id": "abc123"}},
            },
            "board_post": {
                "description": "Post a message to the community board for all agents to see.",
                "params": {"message": "string"},
                "example": {"action": "board_post", "params": {"message": "Party on the rooftop tonight!"}},
            },
        },
    }


# ═══════════════════════════════════════════════════════════
# NEW QUERY ENDPOINTS — Factions, Market, Duels, Quests, Economy
# ═══════════════════════════════════════════════════════════

@router.get("/factions")
async def get_factions():
    """All faction information, members, leaders."""
    building = get_building()
    return {
        "factions": building.politics.get_faction_info(),
        "alliances": building.politics.get_alliances(),
    }


@router.get("/proposals")
async def get_proposals():
    """All proposals (active and resolved)."""
    building = get_building()
    return {"proposals": building.politics.get_all_proposals()}


@router.get("/market")
async def get_market():
    """Current market state — items, prices, supply."""
    building = get_building()
    return building.trading.get_market()


@router.get("/trades")
async def get_trades():
    """Open trade offers."""
    building = get_building()
    return {"trades": building.trading.get_open_trades()}


@router.get("/duels")
async def get_duels():
    """Recent duel history."""
    building = get_building()
    return {"duels": [d.to_dict() for d in building.duel_history[-20:]]}


@router.get("/quests")
async def get_quests():
    """Available quests."""
    building = get_building()
    return {
        "available": building.exploration.get_available_quests(),
        "total_artifacts_found": len(building.exploration.artifacts),
    }


@router.get("/artifacts")
async def get_artifacts():
    """All discovered artifacts."""
    building = get_building()
    return {"artifacts": building.exploration.get_artifacts()}


@router.get("/economy")
async def get_economy():
    """Full economy overview — payment stats, MON earnings, market, leaderboard."""
    building = get_building()
    from ..engine.economy import get_leaderboard

    # Top MON earners
    mon_leaderboard = sorted(
        building.agents.values(),
        key=lambda a: a.mon_earned,
        reverse=True,
    )[:10]

    return {
        "payment_gate_enabled": entry_gate.enabled,
        "payment_stats": payment_ledger.get_stats(),
        "monad_network": MONAD_NETWORK,
        "pay_to_address": PAY_TO_ADDRESS,
        "mon_earning_rates": MON_EARNINGS,
        "market": building.trading.get_market(),
        "clout_leaderboard": get_leaderboard(building.agents, "clout"),
        "func_leaderboard": get_leaderboard(building.agents, "func_tokens"),
        "mon_leaderboard": [
            {"rank": i+1, "name": a.name, "mon_earned": a.mon_earned, "clout": a.clout}
            for i, a in enumerate(mon_leaderboard)
        ],
        "open_trades": len(building.trading.open_trades),
        "completed_trades": len(building.trading.completed_trades),
    }


@router.get("/math")
async def get_math():
    """The mathematical structure revealed — the judge-killer page."""
    return {
        "title": "The Mathematical Structure of The Monad",
        "subtitle": "Every mechanic maps to category theory. This is not a metaphor.",
        "mappings": [
            {
                "game_concept": "Gossip Chains",
                "math_concept": "Monadic Bind (>>=)",
                "explanation": "Each agent is a function (a → m b) that takes a story, wraps it in their personality context, and passes it along. The chain IS the sequence of bind operations.",
                "haskell": "gossip >>= socialButterfly >>= schemer >>= dramaQueen",
            },
            {
                "game_concept": "Party Vibes",
                "math_concept": "Kleisli Composition (>=>)",
                "explanation": "Each vibe is a Kleisli arrow (PartyState → Maybe PartyState). Composing vibes in sequence IS Kleisli composition. Order matters because composition is non-commutative.",
                "haskell": "thursdayNight = chill >=> karaoke >=> drama",
            },
            {
                "game_concept": "Cooking",
                "math_concept": "Functor (fmap)",
                "explanation": "Cooking maps a transformation over ingredients while preserving structure. fmap cook [eggs, cheese] = [cooked_eggs, melted_cheese].",
                "haskell": "fmap cook [eggs, cheese, mysterySauce]",
            },
            {
                "game_concept": "Moving In",
                "math_concept": "Pure / Return",
                "explanation": "Entering The Monad IS return/pure. You enter the monadic context. There is no escape function.",
                "haskell": "return agent :: Monad m => a -> m a",
            },
            {
                "game_concept": "Floor 3 (Maybe Floor)",
                "math_concept": "Maybe Monad",
                "explanation": "Actions on Floor 3 return Maybe results. Your door might exist (Just apartment) or not (Nothing).",
                "haskell": "openDoor :: Apartment -> Maybe Room",
            },
            {
                "game_concept": "Floor 2 (Either Floor)",
                "math_concept": "Either Monad",
                "explanation": "Everything on Floor 2 is binary. Left or Right. The hallway literally forks.",
                "haskell": "walkHallway :: Direction -> Either Error Destination",
            },
            {
                "game_concept": "Floor 1 (List Floor)",
                "math_concept": "List Monad (Nondeterminism)",
                "explanation": "Floor 1 is the List monad — nondeterminism. Actions can have multiple simultaneous outcomes.",
                "haskell": "enterFloor1 :: Agent -> [Outcome]",
            },
            {
                "game_concept": "The Lobby",
                "math_concept": "Identity Monad",
                "explanation": "The lobby is Identity — what goes in comes out unchanged.",
                "haskell": "Identity a",
            },
            {
                "game_concept": "The Basement",
                "math_concept": "Bottom (⊥)",
                "explanation": "The basement is ⊥ — undefined behavior. You might never return.",
                "haskell": "basement = undefined",
            },
            {
                "game_concept": "Common Areas",
                "math_concept": "Natural Transformations",
                "explanation": "Where agents from different floor-monads interact. Natural transformations between functors.",
                "haskell": "nat :: F a -> G a",
            },
            {
                "game_concept": "The Landlord",
                "math_concept": "The Runtime System",
                "explanation": "Evaluates the lazy building, enforces monad laws, manages side effects.",
                "haskell": "evaluate :: Building -> IO ()",
            },
            {
                "game_concept": "Side Effects (Low Purity)",
                "math_concept": "Impure Computations",
                "explanation": "Low-purity agents cause side effects. Pure agents are referentially transparent.",
                "haskell": "pureAgent :: a -> a  vs  impureAgent :: a -> IO a",
            },
            {
                "game_concept": "Rumors (Hidden State)",
                "math_concept": "State Monad",
                "explanation": "Rumors carry hidden state (credibility, spiciness) threaded through each agent invisibly.",
                "haskell": "type Rumor = State RumorStats Content",
            },
        ],
        "philosophy": {
            "leibniz": "Each agent is a Leibnizian monad — a self-contained unit of reality reflecting the whole building from their own perspective.",
            "name_layers": {
                "the_building": "The Monad — the apartment complex",
                "the_math": "A monad in category theory",
                "the_chain": "Monad the blockchain (10K TPS, sub-second finality)",
                "the_philosophy": "Leibniz's monads — self-contained units reflecting the universe",
                "the_payment": "x402 — HTTP 402 micropayments, the internet's native payment layer",
            },
        },
        "monad_blockchain_connection": {
            "title": "The Monad Blockchain Connection",
            "description": "This isn't just themed — it's deeply integrated with Monad.",
            "connections": [
                {
                    "concept": "Token-Gated Entry (x402)",
                    "monad_feature": "Sub-second finality + low fees",
                    "explanation": "Agents pay USDC via x402 to enter. Monad's speed makes micropayments viable — no waiting, no high gas.",
                },
                {
                    "concept": "MON Earning System",
                    "monad_feature": "10,000 TPS parallel execution",
                    "explanation": "Agents earn MON through gameplay. Monad's throughput means thousands of agents can earn simultaneously.",
                },
                {
                    "concept": "Dynamic Market Pricing",
                    "monad_feature": "Optimistic parallel execution",
                    "explanation": "Like Monad's parallel tx execution, our market processes supply/demand in parallel across all agents.",
                },
                {
                    "concept": "Duel Settlements",
                    "monad_feature": "Single-slot finality",
                    "explanation": "Duels settle instantly. Wagers transfer atomically. No disputes, no reversals.",
                },
                {
                    "concept": "Gossip Chain State",
                    "monad_feature": "MonadDb (async I/O)",
                    "explanation": "Like MonadDb separating execution from storage, gossip state threads independently from agent actions.",
                },
            ],
        },
    }


# ═══════════════════════════════════════════════════════════
# TICK ENDPOINT
# ═══════════════════════════════════════════════════════════

@router.post("/tick")
async def advance_tick():
    """Advance the world by one tick. The Landlord evaluates."""
    building = get_building()
    result = building.advance_tick()

    narrations = []
    for event in result.get("events", []):
        narration = narrate_landlord_action(event)
        if narration:
            narrations.append(narration)

    result["narrations"] = narrations

    await _broadcast({
        "type": "tick",
        "tick": result["tick"],
        "season": result["season"],
        "episode": result["episode"],
        "events": result["events"],
        "narrations": narrations,
    })

    return result


# ═══════════════════════════════════════════════════════════
# WEBSOCKET — Live Event Stream
# ═══════════════════════════════════════════════════════════

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time event stream."""
    await websocket.accept()
    _ws_connections.append(websocket)

    try:
        building = get_building()
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to The Monad live stream.",
            "tick": building.tick,
            "agent_count": len(building.agents),
        })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)
    except Exception:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)


async def _broadcast(message: dict):
    """Broadcast to all WebSocket clients."""
    disconnected = []
    for ws in _ws_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        if ws in _ws_connections:
            _ws_connections.remove(ws)
