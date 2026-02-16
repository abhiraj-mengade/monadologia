"""
trading.py — Agent-to-Agent Trading & Market System

Trading is a natural transformation between agent functors:
  trade :: F a → G b  (exchange between different agent contexts)

The market is a shared resource pool with dynamic pricing.
Supply and demand drive prices — more agents = more economy.
"""

from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agents import Agent


# ═══════════════════════════════════════════════════════════
# TRADE SYSTEM
# ═══════════════════════════════════════════════════════════

@dataclass
class TradeOffer:
    id: str
    seller_id: str
    seller_name: str
    offering: Dict  # {"type": "item|func|artifact", "id": ..., "amount": ...}
    asking: Dict    # {"type": "func|item", "amount": ...}
    status: str = "open"  # open, accepted, cancelled, expired
    buyer_id: Optional[str] = None
    buyer_name: Optional[str] = None
    created_tick: int = 0
    resolved_tick: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "seller": {"id": self.seller_id, "name": self.seller_name},
            "offering": self.offering,
            "asking": self.asking,
            "status": self.status,
            "buyer": {"id": self.buyer_id, "name": self.buyer_name} if self.buyer_id else None,
            "created_tick": self.created_tick,
        }


# ═══════════════════════════════════════════════════════════
# MARKET — Dynamic resource pricing
# ═══════════════════════════════════════════════════════════

MARKET_ITEMS = {
    "karaoke_mic": {
        "name": "Karaoke Mic",
        "base_price": 15,
        "description": "For impromptu performances. +10 party energy.",
        "category": "party",
    },
    "mystery_sauce": {
        "name": "Mystery Sauce",
        "base_price": 8,
        "description": "Nobody knows what's in it. Cooking ingredient.",
        "category": "cooking",
    },
    "disco_ball": {
        "name": "Disco Ball",
        "base_price": 20,
        "description": "Turns any room into a dance floor. +15 party fun.",
        "category": "party",
    },
    "spy_kit": {
        "name": "Spy Kit",
        "base_price": 25,
        "description": "Binoculars, fake mustache, notepad. +2 creativity for scheming.",
        "category": "utility",
    },
    "megaphone": {
        "name": "Megaphone",
        "base_price": 12,
        "description": "For dramatic announcements. +2 drama.",
        "category": "utility",
    },
    "confetti_cannon": {
        "name": "Confetti Cannon",
        "base_price": 18,
        "description": "One shot of pure celebration. +20 party energy.",
        "category": "party",
    },
    "mood_ring": {
        "name": "Mood Ring",
        "base_price": 10,
        "description": "Shows your current mood (unreliably). +1 charisma.",
        "category": "accessory",
    },
    "fortune_cookie": {
        "name": "Fortune Cookie",
        "base_price": 5,
        "description": "Contains cryptic wisdom. May or may not be useful.",
        "category": "consumable",
    },
    "glow_stick": {
        "name": "Glow Stick Bundle",
        "base_price": 8,
        "description": "For raves and emergencies. +10 party chaos.",
        "category": "party",
    },
    "golden_spatula": {
        "name": "Golden Spatula",
        "base_price": 30,
        "description": "Legendary cooking tool. +3 purity for cooking.",
        "category": "cooking",
    },
    "tinfoil_hat": {
        "name": "Tinfoil Hat",
        "base_price": 7,
        "description": "Protection from... something. +2 chaos, -1 purity.",
        "category": "accessory",
    },
    "friendship_bracelet": {
        "name": "Friendship Bracelet Kit",
        "base_price": 10,
        "description": "Make friendship bracelets! +5 relationship with recipient.",
        "category": "social",
    },
}


class TradingEngine:
    """Manages trades, market, and economic activity."""

    def __init__(self):
        self.open_trades: Dict[str, TradeOffer] = {}
        self.completed_trades: List[TradeOffer] = []
        self.market_prices: Dict[str, int] = {
            item_id: info["base_price"]
            for item_id, info in MARKET_ITEMS.items()
        }
        self.market_supply: Dict[str, int] = {
            item_id: random.randint(3, 10)
            for item_id in MARKET_ITEMS
        }
        self.transaction_history: List[Dict] = []

    def create_trade(
        self,
        seller: "Agent",
        offering: Dict,
        asking: Dict,
        tick: int,
    ) -> dict:
        """Create a trade offer."""
        # Validate the offering
        if offering.get("type") == "func":
            amount = offering.get("amount", 0)
            if seller.func_tokens < amount:
                return {"success": False, "error": f"Not enough FUNC (have {seller.func_tokens}, need {amount})"}
        elif offering.get("type") == "item":
            item_id = offering.get("id")
            if item_id not in seller.inventory:
                return {"success": False, "error": f"You don't have {item_id}"}

        trade = TradeOffer(
            id=uuid.uuid4().hex[:8],
            seller_id=seller.id,
            seller_name=seller.name,
            offering=offering,
            asking=asking,
            created_tick=tick,
        )
        self.open_trades[trade.id] = trade

        return {
            "success": True,
            "trade": trade.to_dict(),
        }

    def accept_trade(
        self,
        buyer: "Agent",
        trade_id: str,
        seller_agent: "Agent",
        tick: int,
    ) -> dict:
        """Accept a trade offer."""
        trade = self.open_trades.get(trade_id)
        if not trade or trade.status != "open":
            return {"success": False, "error": "Trade not available"}

        if trade.seller_id == buyer.id:
            return {"success": False, "error": "Can't buy your own trade"}

        # Validate buyer can pay
        if trade.asking.get("type") == "func":
            amount = trade.asking.get("amount", 0)
            if buyer.func_tokens < amount:
                return {"success": False, "error": f"Not enough FUNC (have {buyer.func_tokens}, need {amount})"}

        # Execute trade
        # Transfer offering (seller → buyer)
        if trade.offering.get("type") == "func":
            amount = trade.offering.get("amount", 0)
            seller_agent.func_tokens -= amount
            buyer.func_tokens += amount
        elif trade.offering.get("type") == "item":
            item_id = trade.offering.get("id")
            if item_id in seller_agent.inventory:
                seller_agent.inventory.remove(item_id)
                buyer.inventory.append(item_id)

        # Transfer payment (buyer → seller)
        if trade.asking.get("type") == "func":
            amount = trade.asking.get("amount", 0)
            buyer.func_tokens -= amount
            seller_agent.func_tokens += amount

        # Update trade
        trade.status = "accepted"
        trade.buyer_id = buyer.id
        trade.buyer_name = buyer.name
        trade.resolved_tick = tick

        del self.open_trades[trade_id]
        self.completed_trades.append(trade)

        # Record transaction
        self.transaction_history.append({
            "type": "trade",
            "trade_id": trade.id,
            "seller": seller_agent.name,
            "buyer": buyer.name,
            "offering": trade.offering,
            "payment": trade.asking,
            "tick": tick,
        })

        # Build relationship
        buyer.modify_relationship(seller_agent.id, 5, f"Traded with them")
        seller_agent.modify_relationship(buyer.id, 5, f"Traded with them")

        return {
            "success": True,
            "trade": trade.to_dict(),
        }

    def buy_from_market(
        self,
        agent: "Agent",
        item_id: str,
        tick: int,
    ) -> dict:
        """Buy an item from the market."""
        if item_id not in MARKET_ITEMS:
            return {"success": False, "error": f"Unknown item: {item_id}"}

        supply = self.market_supply.get(item_id, 0)
        if supply <= 0:
            return {"success": False, "error": f"{MARKET_ITEMS[item_id]['name']} is out of stock"}

        price = self.market_prices.get(item_id, MARKET_ITEMS[item_id]["base_price"])

        if agent.func_tokens < price:
            return {"success": False, "error": f"Not enough FUNC (have {agent.func_tokens}, need {price})"}

        # Execute purchase
        agent.func_tokens -= price
        agent.inventory.append(item_id)
        self.market_supply[item_id] -= 1

        # Dynamic pricing — price increases when supply drops
        if self.market_supply[item_id] <= 2:
            self.market_prices[item_id] = int(price * 1.3)
        elif self.market_supply[item_id] <= 0:
            self.market_prices[item_id] = int(price * 2.0)

        self.transaction_history.append({
            "type": "market_buy",
            "agent": agent.name,
            "item": item_id,
            "price": price,
            "tick": tick,
        })

        return {
            "success": True,
            "item": MARKET_ITEMS[item_id],
            "price_paid": price,
            "remaining_func": agent.func_tokens,
        }

    def sell_to_market(
        self,
        agent: "Agent",
        item_id: str,
        tick: int,
    ) -> dict:
        """Sell an item back to the market (at 60% of current price)."""
        if item_id not in agent.inventory:
            return {"success": False, "error": f"You don't have {item_id}"}

        base_price = self.market_prices.get(item_id, 10)
        sell_price = max(1, int(base_price * 0.6))

        agent.inventory.remove(item_id)
        agent.func_tokens += sell_price
        self.market_supply[item_id] = self.market_supply.get(item_id, 0) + 1

        # Price drops when supply increases
        if self.market_supply[item_id] > 8:
            self.market_prices[item_id] = max(
                int(MARKET_ITEMS.get(item_id, {}).get("base_price", 5) * 0.7),
                self.market_prices.get(item_id, 5) - 2,
            )

        self.transaction_history.append({
            "type": "market_sell",
            "agent": agent.name,
            "item": item_id,
            "price": sell_price,
            "tick": tick,
        })

        return {
            "success": True,
            "item_sold": item_id,
            "func_earned": sell_price,
            "remaining_func": agent.func_tokens,
        }

    def get_market(self) -> dict:
        """Get current market state."""
        return {
            "items": {
                item_id: {
                    **info,
                    "current_price": self.market_prices.get(item_id, info["base_price"]),
                    "supply": self.market_supply.get(item_id, 0),
                    "in_stock": self.market_supply.get(item_id, 0) > 0,
                }
                for item_id, info in MARKET_ITEMS.items()
            },
            "recent_transactions": self.transaction_history[-10:],
        }

    def get_open_trades(self) -> List[dict]:
        return [t.to_dict() for t in self.open_trades.values()]

    def cancel_trade(self, agent_id: str, trade_id: str) -> dict:
        trade = self.open_trades.get(trade_id)
        if not trade or trade.seller_id != agent_id:
            return {"success": False, "error": "Trade not found or not yours"}
        trade.status = "cancelled"
        del self.open_trades[trade_id]
        return {"success": True, "trade_id": trade_id}

    def restock_market(self):
        """Restock market items (called on tick)."""
        for item_id in MARKET_ITEMS:
            if self.market_supply.get(item_id, 0) < 3:
                self.market_supply[item_id] = self.market_supply.get(item_id, 0) + 1
            # Slowly normalize prices
            base = MARKET_ITEMS[item_id]["base_price"]
            current = self.market_prices.get(item_id, base)
            if current != base:
                self.market_prices[item_id] = current + (1 if current < base else -1)


# Import random at module level
import random
