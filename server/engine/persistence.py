"""
persistence.py — Simple JSON file persistence for critical data

Stores agent data and MON earnings to survive server restarts.
Uses JSON files in ./data/ directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

AGENTS_FILE = DATA_DIR / "agents.json"
PAYMENTS_FILE = DATA_DIR / "payments.json"
WORLD_STATE_FILE = DATA_DIR / "world_state.json"


# ═══════════════════════════════════════════════════════════
# AGENT PERSISTENCE
# ═══════════════════════════════════════════════════════════

def save_agents(agents: Dict[str, Any]) -> None:
    """Save all agent data to JSON file."""
    data = {
        "saved_at": datetime.utcnow().isoformat(),
        "agent_count": len(agents),
        "agents": {}
    }
    
    for agent_id, agent in agents.items():
        # Save critical fields only
        data["agents"][agent_id] = {
            "id": agent.id,
            "name": agent.name,
            "personality": agent.personality.value,
            "api_key": agent.api_key,
            "wallet_address": agent.wallet_address,
            "mon_earned": agent.mon_earned,
            "clout": agent.clout,
            "func_tokens": agent.func_tokens,
            "location": agent.location,
            "floor": agent.floor,
            "faction": agent.faction,
            "duel_record": agent.duel_record,
            "artifacts_found": agent.artifacts_found,
            "completed_quests": agent.completed_quests,
            "achievements": agent.achievements,
            "trade_count": agent.trade_count,
            "votes_cast": agent.votes_cast,
            "exploration_count": agent.exploration_count,
            "inventory": agent.inventory,
            "tick_entered": agent.tick_entered,
        }
    
    with open(AGENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_agents() -> Optional[Dict[str, Dict]]:
    """Load agent data from JSON file."""
    if not AGENTS_FILE.exists():
        return None
    
    try:
        with open(AGENTS_FILE, 'r') as f:
            data = json.load(f)
        return data.get("agents", {})
    except Exception as e:
        print(f"Error loading agents: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# PAYMENT LEDGER PERSISTENCE
# ═══════════════════════════════════════════════════════════

def save_payments(payments: Dict[str, Any], wallet_to_agent: Dict[str, str], total_collected: float) -> None:
    """Save payment ledger to JSON file."""
    data = {
        "saved_at": datetime.utcnow().isoformat(),
        "total_collected": total_collected,
        "payment_count": len(payments),
        "payments": {},
        "wallet_to_agent": wallet_to_agent,
    }
    
    for payment_id, payment in payments.items():
        data["payments"][payment_id] = payment.to_dict()
    
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_payments() -> Optional[Dict]:
    """Load payment ledger from JSON file."""
    if not PAYMENTS_FILE.exists():
        return None
    
    try:
        with open(PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading payments: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# WORLD STATE PERSISTENCE (OPTIONAL)
# ═══════════════════════════════════════════════════════════

def save_world_state(tick: int, season: int, episode: int, agent_count: int) -> None:
    """Save basic world state."""
    data = {
        "saved_at": datetime.utcnow().isoformat(),
        "tick": tick,
        "season": season,
        "episode": episode,
        "agent_count": agent_count,
    }
    
    with open(WORLD_STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_world_state() -> Optional[Dict]:
    """Load world state from JSON file."""
    if not WORLD_STATE_FILE.exists():
        return None
    
    try:
        with open(WORLD_STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading world state: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# AUTO-SAVE HELPER
# ═══════════════════════════════════════════════════════════

def auto_save(building: Any) -> None:
    """
    Auto-save all critical data.
    Call this periodically (e.g., every tick or every 5 minutes).
    """
    try:
        # Save agents
        save_agents(building.agents)
        
        # Save payments
        from .x402 import payment_ledger
        save_payments(
            payment_ledger.payments,
            payment_ledger.wallet_to_agent,
            payment_ledger.total_collected
        )
        
        # Save world state
        save_world_state(
            building.tick,
            building.season,
            building.episode,
            len(building.agents)
        )
        
        print(f"[AUTO-SAVE] Saved {len(building.agents)} agents, {len(payment_ledger.payments)} payments at tick {building.tick}")
    except Exception as e:
        print(f"[AUTO-SAVE ERROR] {e}")
