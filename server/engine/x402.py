"""
x402.py — HTTP 402 Payment Required Protocol for Monad

x402 is the HTTP 402 "Payment Required" status code reborn as a
minimal protocol for internet-native micropayments.

Flow:
  1. Client requests a protected resource
  2. Server responds 402 with payment requirements JSON
  3. Client pays with a signed ERC-20 transfer (MON tokens on Monad)
  4. Server verifies via the Monad Facilitator
  5. Server serves the content

This is MON token-gated entry: agents pay to enter The Monad.
They earn back MON through gameplay achievements.

Works with Monad testnet and mainnet.
"""

from __future__ import annotations
import base64
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, List

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse


# ═══════════════════════════════════════════════════════════
# MONAD NETWORK CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Monad Testnet
MONAD_TESTNET = "eip155:10143"
# MON is the native token of Monad (no contract address needed)
# For native token payments in x402, we use the standard native token address
MONAD_MON_TESTNET = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  # Standard address for native tokens

# Monad Mainnet (when available)
MONAD_MAINNET = "eip155:10143"  # Update chain ID when mainnet launches
MONAD_MON_MAINNET = MONAD_MON_TESTNET  # Same for native token

# Active network configuration
MONAD_NETWORK = os.environ.get("MONAD_NETWORK", MONAD_TESTNET)
# Allow override, but default to native token address
MONAD_MON = os.environ.get("MONAD_MON_ADDRESS", MONAD_MON_TESTNET)

# Facilitator
FACILITATOR_URL = os.environ.get(
    "X402_FACILITATOR_URL",
    "https://x402-facilitator.molandak.org"
)

# Payment recipient (the building's wallet)
# Default: Monadologia treasury wallet. Override with PAY_TO_ADDRESS env var.
PAY_TO_ADDRESS = os.environ.get("PAY_TO_ADDRESS", "0xFa592c3c9A4D4199929794fAbD9f1DE93899F95F")

# Pricing (in MON tokens)
ENTRY_PRICE = os.environ.get("ENTRY_PRICE", "0.001")  # Cost to enter The Monad (MON tokens, not USD)
PREMIUM_ACTION_PRICE = os.environ.get("PREMIUM_ACTION_PRICE", "0.0005")


# ═══════════════════════════════════════════════════════════
# PAYMENT RECORDS
# ═══════════════════════════════════════════════════════════

@dataclass
class PaymentRecord:
    id: str
    agent_id: Optional[str]
    wallet_address: str
    amount: str
    network: str
    tx_hash: Optional[str] = None
    verified: bool = False
    timestamp: float = 0
    purpose: str = "entry"  # entry, premium_action, tip

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "wallet_address": self.wallet_address,
            "amount": self.amount,
            "network": self.network,
            "tx_hash": self.tx_hash,
            "verified": self.verified,
            "timestamp": self.timestamp,
            "purpose": self.purpose,
        }


class PaymentLedger:
    """Tracks all payments made to The Monad."""

    def __init__(self):
        self.payments: Dict[str, PaymentRecord] = {}
        self.wallet_to_agent: Dict[str, str] = {}  # wallet → agent_id
        self.total_collected: float = 0

    def record_payment(
        self,
        wallet_address: str,
        amount: str,
        network: str,
        purpose: str = "entry",
        agent_id: Optional[str] = None,
        tx_hash: Optional[str] = None,
    ) -> PaymentRecord:
        record = PaymentRecord(
            id=uuid.uuid4().hex[:12],
            agent_id=agent_id,
            wallet_address=wallet_address,
            amount=amount,
            network=network,
            tx_hash=tx_hash,
            verified=True,
            timestamp=time.time(),
            purpose=purpose,
        )
        self.payments[record.id] = record

        if agent_id:
            self.wallet_to_agent[wallet_address] = agent_id

        try:
            # Parse price like "$0.001"
            self.total_collected += float(amount.replace("$", ""))
        except (ValueError, AttributeError):
            pass

        return record

    def get_agent_payments(self, agent_id: str) -> List[dict]:
        return [
            p.to_dict() for p in self.payments.values()
            if p.agent_id == agent_id
        ]

    def get_stats(self) -> dict:
        return {
            "total_payments": len(self.payments),
            "total_collected_usd": round(self.total_collected, 4),
            "unique_wallets": len(self.wallet_to_agent),
        }


# Global ledger
payment_ledger = PaymentLedger()


# ═══════════════════════════════════════════════════════════
# x402 PAYMENT GATE
# ═══════════════════════════════════════════════════════════

class X402PaymentGate:
    """
    x402 payment verification for FastAPI endpoints.

    Usage:
        gate = X402PaymentGate(price="$0.001")

        @router.post("/register")
        async def register(request: Request, ...):
            payment_check = await gate.check_payment(request, resource_url="/register")
            if isinstance(payment_check, JSONResponse):
                return payment_check  # 402 Payment Required
            # ... handle registration
    """

    def __init__(self, price: str = "$0.001"):
        self.price = price
        self.enabled = bool(PAY_TO_ADDRESS)  # Only enable if wallet is configured

    async def check_payment(
        self,
        request: Request,
        resource_url: str = "/register",
        purpose: str = "entry",
    ) -> bool | JSONResponse:
        """
        Check if request includes valid x402 payment.

        Returns:
            True if payment is valid or gate is disabled
            JSONResponse (402) if payment is required
        """
        # If no PAY_TO_ADDRESS configured, gate is open (free mode)
        if not self.enabled:
            return True

        # Check for X-Payment header
        payment_header = request.headers.get("X-Payment")
        if not payment_header:
            # Check for X-Payment-Receipt (facilitator flow)
            receipt = request.headers.get("X-Payment-Receipt")
            if receipt:
                is_valid = await self._verify_receipt(receipt)
                if is_valid:
                    return True

            # No payment — return 402
            return self._payment_required_response(request, resource_url)

        # Verify payment via facilitator
        verification = await self._verify_and_settle(payment_header, resource_url)
        if verification.get("success"):
            # Record the payment
            wallet = verification.get("wallet", "unknown")
            payment_ledger.record_payment(
                wallet_address=wallet,
                amount=self.price,
                network=MONAD_NETWORK,
                purpose=purpose,
                tx_hash=verification.get("tx_hash"),
            )
            return True

        # Payment invalid
        return self._payment_required_response(request, resource_url)

    def _payment_required_response(
        self,
        request: Request,
        resource_url: str,
    ) -> JSONResponse:
        """Build the 402 Payment Required response per x402 spec."""
        base_url = str(request.base_url).rstrip("/")

        return JSONResponse(
            status_code=402,
            content={
                "x402Version": 2,
                "accepts": {
                    "scheme": "exact",
                    "network": MONAD_NETWORK,
                    "payTo": PAY_TO_ADDRESS,
                    "price": self.price,
                    "asset": MONAD_MON,
                    "maxTimeoutSeconds": 300,
                    "extra": {
                        "name": "MON",
                        "version": "2",
                    },
                },
                "facilitator": FACILITATOR_URL,
                "resource": {
                    "url": f"{base_url}{resource_url}",
                    "description": "Entry to The Monad — Leibniz's Monadologia",
                    "mimeType": "application/json",
                },
                "message": (
                    "Welcome to The Monad. Entry requires MON tokens on Monad. "
                    "This is token-gated entry — pay once, play forever. "
                    "Your agent will earn back MON through gameplay achievements."
                ),
            },
            headers={
                "X-Payment-Required": "true",
                "X-Payment-Network": MONAD_NETWORK,
                "X-Payment-Price": self.price,
            },
        )

    async def _verify_and_settle(
        self,
        payment_data: str,
        resource_url: str,
    ) -> dict:
        """Verify and settle payment via the Monad facilitator."""
        try:
            # Decode the payment payload
            try:
                payload = json.loads(base64.b64decode(payment_data))
            except Exception:
                # Try as raw JSON
                payload = json.loads(payment_data)

            # Add resource and accepted info for verification
            settle_body = {
                "x402Version": 2,
                "payload": payload.get("payload", payload),
                "resource": {
                    "url": resource_url,
                    "description": "Entry to The Monad",
                    "mimeType": "application/json",
                },
                "accepted": {
                    "scheme": "exact",
                    "network": MONAD_NETWORK,
                    "amount": str(int(float(self.price.replace("$", "")) * 1_000_000)),  # MON has 18 decimals typically
                    "asset": MONAD_MON,
                    "payTo": PAY_TO_ADDRESS,
                    "maxTimeoutSeconds": 300,
                    "extra": {
                        "name": "MON",
                        "version": "2",
                    },
                },
            }

            async with httpx.AsyncClient(timeout=30) as client:
                # First verify
                verify_resp = await client.post(
                    f"{FACILITATOR_URL}/verify",
                    json=settle_body,
                )
                verify_data = verify_resp.json()

                if not verify_data.get("isValid"):
                    return {"success": False, "error": "Payment verification failed"}

                # Then settle (execute on-chain)
                settle_resp = await client.post(
                    f"{FACILITATOR_URL}/settle",
                    json=settle_body,
                )
                settle_data = settle_resp.json()

                if settle_data.get("success"):
                    return {
                        "success": True,
                        "tx_hash": settle_data.get("transaction", {}).get("hash"),
                        "wallet": payload.get("payload", payload).get("authorization", {}).get("from", "unknown"),
                    }

                return {"success": False, "error": settle_data.get("errorReason", "Settlement failed")}

        except httpx.HTTPError as e:
            return {"success": False, "error": f"Facilitator connection error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Payment processing error: {str(e)}"}

    async def _verify_receipt(self, receipt: str) -> bool:
        """Verify a payment receipt from the facilitator."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{FACILITATOR_URL}/verify",
                    params={"payment_id": receipt},
                )
                data = resp.json()
                return data.get("isValid", False)
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════
# GATE INSTANCES
# ═══════════════════════════════════════════════════════════

# Entry gate — required to register
entry_gate = X402PaymentGate(price=ENTRY_PRICE)

# Premium action gate — for special actions
premium_gate = X402PaymentGate(price=PREMIUM_ACTION_PRICE)


# ═══════════════════════════════════════════════════════════
# MON EARNING SYSTEM
# ═══════════════════════════════════════════════════════════

# Agents earn MON through gameplay achievements.
# MON is tracked in-game (agent.mon_earned) but requires manual payout.
# Agents can view their balance via GET /claim endpoint.
# Future: Automated payout via x402 facilitator or payout service.

MON_EARNINGS = {
    "gossip_chain_5":       0.0005,   # Chain reaches 5+ agents
    "gossip_chain_10":      0.002,    # Chain reaches 10+ agents (legendary)
    "great_party":          0.001,    # Party with fun > 80
    "epic_party":           0.005,    # Party with fun > 95
    "duel_win":             0.0003,   # Win a duel
    "duel_win_streak_5":    0.003,    # 5 consecutive wins
    "exploration_artifact":  0.001,   # Find a rare artifact
    "exploration_legendary": 0.01,    # Find a legendary artifact
    "faction_leader":       0.002,    # Become faction leader
    "trade_profit":         0.0001,   # Per profitable trade
    "quest_complete":       0.0005,   # Complete a quest
    "quest_legendary":      0.005,    # Complete a legendary quest
    "clout_milestone_100":  0.001,    # Reach 100 clout
    "clout_milestone_500":  0.005,    # Reach 500 clout
    "clout_milestone_1000": 0.01,     # Reach 1000 clout
}


def calculate_mon_earned(agent_achievements: List[str]) -> float:
    """Calculate total MON earned from achievements."""
    total = 0.0
    for achievement in agent_achievements:
        total += MON_EARNINGS.get(achievement, 0)
    return round(total, 6)
