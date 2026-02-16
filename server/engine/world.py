"""
world.py — The Building (The Monad Itself)

THE MONAD — "A building where the math lives in the walls"

Each floor is a different monad:
  - Rooftop: IO (interactions with the outside world)
  - Floor 3: Maybe (actions might succeed, might return Nothing)
  - Floor 2: Either (everything is binary, Left or Right)
  - Floor 1: List (everything multiplies, nondeterminism)
  - Lobby: Identity (what you put in is what you get out)
  - Basement: Bottom (⊥) (undefined behavior, infinite loops)

Common areas are Natural Transformations — where different
monad inhabitants interact and their types must reconcile.
"""

from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .agents import Agent, Personality, Mood, create_agent
from .gossip import GossipEngine, GossipMessage, bind_gossip
from .parties import Party, Vibe, kleisli_compose, PartyState
from .landlord import Landlord
from .economy import (
    award_clout, spend_func, earn_func, get_leaderboard, CLOUT_REWARDS
)
from .combat import resolve_duel, DuelResult
from .politics import PoliticsEngine, Faction, FACTION_INFO
from .exploration import ExplorationEngine
from .trading import TradingEngine, MARKET_ITEMS
from .x402 import payment_ledger, MON_EARNINGS
from .persistence import auto_save, load_agents, load_payments, load_world_state


# ═══════════════════════════════════════════════════════════
# LOCATIONS — The topology of The Monad
# ═══════════════════════════════════════════════════════════

LOCATIONS = {
    "rooftop": {
        "name": "The Rooftop (IO Layer)",
        "floor": "rooftop",
        "monad": "IO",
        "description": "Where things interact with the outside world. Parties, confessions, announcements.",
    },
    "floor_3_hall": {
        "name": "Floor 3 Hallway (Maybe)",
        "floor": "floor_3",
        "monad": "Maybe",
        "description": "Unpredictable. Sometimes your door opens. Sometimes it doesn't.",
    },
    "floor_3_apt": {
        "name": "Floor 3 Apartment",
        "floor": "floor_3",
        "monad": "Maybe",
        "description": "Your Maybe apartment. It exists. Probably.",
    },
    "floor_2_hall": {
        "name": "Floor 2 Hallway (Either)",
        "floor": "floor_2",
        "monad": "Either",
        "description": "The hallway forks. Always two choices. Left or Right.",
    },
    "floor_2_apt": {
        "name": "Floor 2 Apartment",
        "floor": "floor_2",
        "monad": "Either",
        "description": "Binary living. Everything has two states.",
    },
    "floor_1_hall": {
        "name": "Floor 1 Hallway (List)",
        "floor": "floor_1",
        "monad": "List",
        "description": "Everything multiplies. One conversation becomes twelve.",
    },
    "floor_1_apt": {
        "name": "Floor 1 Apartment",
        "floor": "floor_1",
        "monad": "List",
        "description": "Nondeterministic living. Schrödinger's roommate situation.",
    },
    "lobby": {
        "name": "The Lobby (Identity)",
        "floor": "lobby",
        "monad": "Identity",
        "description": "Neutral ground. What you put in is what you get out.",
    },
    "kitchen": {
        "name": "The Kitchen (Natural Transformation)",
        "floor": "common",
        "monad": "NatTrans",
        "description": "Where functors collide and recipes go wrong.",
    },
    "lounge": {
        "name": "The Lounge (Natural Transformation)",
        "floor": "common",
        "monad": "NatTrans",
        "description": "Chill zone. Cross-floor socialization happens here.",
    },
    "gym": {
        "name": "The Gym (Natural Transformation)",
        "floor": "common",
        "monad": "NatTrans",
        "description": "Iron and gossip. Both get lifted here.",
    },
    "courtyard": {
        "name": "The Courtyard (Natural Transformation)",
        "floor": "common",
        "monad": "NatTrans",
        "description": "Open air. A neutral space where all types meet.",
    },
    "basement": {
        "name": "The Basement (⊥)",
        "floor": "basement",
        "monad": "Bottom",
        "description": "Undefined behavior. You might find treasure. You might never come back.",
    },
}

# Items that can appear in the world
WORLD_ITEMS = [
    "karaoke_mic", "mystery_sauce", "disco_ball", "vintage_board_game",
    "suspicious_note", "golden_spatula", "rubber_duck", "glow_stick",
    "megaphone", "fortune_cookie", "confetti_cannon", "mood_ring",
]


class Building:
    """
    The Monad — the central world state.

    This is the monadic context. Once agents enter (pure/return),
    all their actions happen inside this context. Every action
    is a computation in the building monad.
    """

    def __init__(self):
        self.tick: int = 0
        self.agents: Dict[str, Agent] = {}
        self.agent_by_api_key: Dict[str, str] = {}  # api_key → agent_id
        self.gossip_engine = GossipEngine()
        self.landlord = Landlord()
        self.parties: Dict[str, Party] = {}
        self.event_log: List[Dict] = []
        self.story_log: List[Dict] = []  # Narrated events
        self.community_board: List[Dict] = []
        self.season: int = 1
        self.episode: int = 1
        # ─── New systems ─────────────────────────
        self.politics = PoliticsEngine()
        self.exploration = ExplorationEngine()
        self.trading = TradingEngine()
        self.duel_history: List[DuelResult] = []
        
        # ─── Restore from persistence ─────────────
        self._restore_from_disk()

    # ─── Agent Management (Pure / Return) ───────────────────

    def register_agent(self, name: str, personality: str) -> Agent:
        """
        PURE / RETURN — An agent enters the monad.
        Once you're in, everything you do is inside the monadic context.
        There is no escape function. You live here now.
        """
        p = Personality(personality)
        agent = create_agent(name, p, self.tick)
        self.agents[agent.id] = agent
        self.agent_by_api_key[agent.api_key] = agent.id

        self._log_event("enter", {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "personality": personality,
            "message": f"{name} has entered The Monad. There is no escape function.",
        })

        return agent

    def get_agent_by_key(self, api_key: str) -> Optional[Agent]:
        agent_id = self.agent_by_api_key.get(api_key)
        if agent_id:
            return self.agents.get(agent_id)
        return None

    def _restore_from_disk(self):
        """Restore agents and payments from JSON files on startup."""
        # Restore agents
        saved_agents = load_agents()
        if saved_agents:
            from .agents import Personality, Mood
            restored_count = 0
            for agent_id, data in saved_agents.items():
                try:
                    agent = Agent(
                        id=data["id"],
                        name=data["name"],
                        personality=Personality(data["personality"]),
                        stats=PERSONALITY_STATS[Personality(data["personality"])],
                        mood=Mood.NEUTRAL,
                        location=data.get("location", "lobby"),
                        floor=data.get("floor", "lobby"),
                        api_key=data["api_key"],
                        wallet_address=data.get("wallet_address"),
                        mon_earned=data.get("mon_earned", 0.0),
                        clout=data.get("clout", 0),
                        func_tokens=data.get("func_tokens", 100),
                        faction=data.get("faction"),
                        duel_record=data.get("duel_record", {"wins": 0, "losses": 0, "streak": 0}),
                        artifacts_found=data.get("artifacts_found", []),
                        completed_quests=data.get("completed_quests", []),
                        achievements=data.get("achievements", []),
                        trade_count=data.get("trade_count", 0),
                        votes_cast=data.get("votes_cast", 0),
                        exploration_count=data.get("exploration_count", 0),
                        inventory=data.get("inventory", []),
                        tick_entered=data.get("tick_entered", 0),
                    )
                    self.agents[agent.id] = agent
                    self.agent_by_api_key[agent.api_key] = agent.id
                    restored_count += 1
                except Exception as e:
                    print(f"Error restoring agent {agent_id}: {e}")
            
            print(f"[RESTORE] Loaded {restored_count} agents from disk")
        
        # Restore payments
        saved_payments = load_payments()
        if saved_payments:
            from .x402 import PaymentRecord
            for payment_id, payment_data in saved_payments.get("payments", {}).items():
                try:
                    payment = PaymentRecord(
                        id=payment_data["id"],
                        agent_id=payment_data.get("agent_id"),
                        wallet_address=payment_data["wallet_address"],
                        amount=payment_data["amount"],
                        network=payment_data["network"],
                        tx_hash=payment_data.get("tx_hash"),
                        verified=payment_data.get("verified", False),
                        timestamp=payment_data.get("timestamp", 0),
                        purpose=payment_data.get("purpose", "entry"),
                    )
                    payment_ledger.payments[payment_id] = payment
                except Exception as e:
                    print(f"Error restoring payment {payment_id}: {e}")
            
            payment_ledger.wallet_to_agent = saved_payments.get("wallet_to_agent", {})
            payment_ledger.total_collected = saved_payments.get("total_collected", 0.0)
            print(f"[RESTORE] Loaded {len(payment_ledger.payments)} payments from disk")
        
        # Restore world state
        saved_world = load_world_state()
        if saved_world:
            self.tick = saved_world.get("tick", 0)
            self.season = saved_world.get("season", 1)
            self.episode = saved_world.get("episode", 1)
            print(f"[RESTORE] World state: tick={self.tick}, season={self.season}, episode={self.episode}")

    # ─── Movement ────────────────────────────────────────────

    def move_agent(self, agent_id: str, destination: str) -> Dict:
        """Move an agent. Floor monad behavior applies!"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        if destination not in LOCATIONS:
            return {"success": False, "error": f"Unknown location: {destination}"}

        loc = LOCATIONS[destination]
        old_location = agent.location

        # ── Maybe Floor behavior ──
        if loc["monad"] == "Maybe" and loc["floor"] == "floor_3":
            nothing_chance = self.landlord.active_effects.get(
                "floor_3_nothing_chance", 0.2
            )
            if isinstance(nothing_chance, dict):
                nothing_chance = nothing_chance.get("floor_3_nothing_chance", 0.2)
            if random.random() < nothing_chance:
                self._log_event("move_nothing", {
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "destination": destination,
                    "message": f"{agent.name} tried to go to {loc['name']} but got Nothing. The door wasn't there today.",
                })
                return {
                    "success": False,
                    "monad": "Maybe",
                    "result": "Nothing",
                    "message": "The door... isn't there today. Maybe try again later.",
                }

        # ── Either Floor behavior ──
        if loc["monad"] == "Either" and "hall" in destination:
            # The hallway always forks
            went_left = random.choice([True, False])
            direction = "Left" if went_left else "Right"
            self._log_event("move_either", {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "destination": destination,
                "direction": direction,
                "message": f"{agent.name} hit the fork on Floor 2. Went {direction}.",
            })

        # ── List Floor behavior ──
        if loc["monad"] == "List":
            # You arrive and notice multiple versions of events happening
            branches = random.randint(2, 4)
            self._log_event("move_list", {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "destination": destination,
                "branches": branches,
                "message": f"{agent.name} entered Floor 1. {branches} simultaneous conversations materialized.",
            })

        # ── Basement behavior ──
        if loc["monad"] == "Bottom":
            if random.random() < 0.15:
                # Divergence — agent gets lost temporarily
                self._log_event("move_bottom", {
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "message": f"{agent.name} went into the basement and... hasn't come back yet. Evaluating ⊥.",
                })
                # They end up somewhere random after
                random_loc = random.choice(["lobby", "floor_1_hall", "courtyard"])
                agent.location = random_loc
                agent.floor = LOCATIONS[random_loc]["floor"]
                award_clout(agent, "explore_basement")
                return {
                    "success": True,
                    "monad": "Bottom",
                    "result": "Diverged",
                    "actual_location": random_loc,
                    "message": f"You went to the basement. You emerged in {LOCATIONS[random_loc]['name']}. Time felt weird.",
                }

        agent.location = destination
        agent.floor = loc["floor"]

        self._log_event("move", {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "from": old_location,
            "to": destination,
            "message": f"{agent.name} moved to {loc['name']}.",
        })

        return {
            "success": True,
            "location": destination,
            "location_info": loc,
            "agents_here": self._agents_at(destination),
        }

    # ─── Talking ─────────────────────────────────────────────

    def agent_talk(self, agent_id: str, message: str, target_id: Optional[str] = None) -> Dict:
        """Say something to the room or to a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        if target_id:
            target = self.agents.get(target_id)
            if not target or target.location != agent.location:
                return {"success": False, "error": "Target not here"}

            # Talking to someone builds relationship
            agent.modify_relationship(target_id, 3, f"Talked: {message[:50]}")
            target.modify_relationship(agent_id, 3, f"Was told: {message[:50]}")

            self._log_event("talk_private", {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "target_id": target_id,
                "target_name": target.name,
                "message": message,
                "location": agent.location,
            })
        else:
            # Talking to the room
            for other_id, other in self.agents.items():
                if other_id != agent_id and other.location == agent.location:
                    agent.modify_relationship(other_id, 1, f"Room talk: {message[:30]}")

            self._log_event("talk_room", {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "message": message,
                "location": agent.location,
            })

        return {"success": True, "message": message, "location": agent.location}

    # ─── Gossip (BIND / >>=) ────────────────────────────────

    def start_gossip(self, agent_id: str, content: str) -> Dict:
        """Start a new gossip chain. This creates the initial monadic value."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        gossip = self.gossip_engine.start_chain(agent_id, content, self.tick)
        award_clout(agent, "start_gossip")

        self._log_event("gossip_start", {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "gossip_id": gossip.id,
            "content": content,
            "message": f"{agent.name} started a rumor: \"{content}\"",
        })

        return {"success": True, "gossip_id": gossip.id, "content": content}

    def spread_gossip(self, agent_id: str, gossip_id: str, target_id: str) -> Dict:
        """
        Bind (>>=) — propagate gossip through an agent's personality.
        The agent IS the function (a → m b).
        """
        agent = self.agents.get(agent_id)
        target = self.agents.get(target_id)
        if not agent or not target:
            return {"success": False, "error": "Agent or target not found"}

        gossip = self.gossip_engine.propagate(gossip_id, target, self.tick)
        if not gossip:
            return {"success": False, "error": "Can't spread to this agent (already heard or chain dead)"}

        target.gossip_heard.append(gossip_id)

        # Relationship effects from gossip
        agent.modify_relationship(target_id, 5, f"Shared gossip")
        target.modify_relationship(agent_id, 3, f"Heard gossip from them")

        # Clout for chain length
        chain_len = len(gossip.chain)
        if chain_len >= 5:
            origin = self.agents.get(gossip.origin_agent_id)
            if origin:
                award_clout(origin, "gossip_chain_5")
        elif chain_len >= 3:
            origin = self.agents.get(gossip.origin_agent_id)
            if origin:
                award_clout(origin, "gossip_chain_3")

        self._log_event("gossip_spread", {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "target_id": target_id,
            "target_name": target.name,
            "gossip_id": gossip_id,
            "new_content": gossip.chain[-1]["content"] if gossip.chain else "",
            "chain_length": chain_len,
            "credibility": gossip.credibility,
            "spiciness": gossip.spiciness,
            "message": f"{agent.name} told {target.name} the gossip. It transformed through {target.name}'s {target.personality.value} lens.",
        })

        return {
            "success": True,
            "gossip_id": gossip_id,
            "new_content": gossip.chain[-1]["content"] if gossip.chain else "",
            "chain_length": chain_len,
            "credibility": gossip.credibility,
            "spiciness": gossip.spiciness,
            "bind_transform": f">>= {target.personality.value}",
        }

    # ─── Parties (KLEISLI COMPOSITION) ──────────────────────

    def throw_party(self, host_id: str, vibes: List[str], location: str = "rooftop") -> Dict:
        """
        Plan a party with a sequence of vibes.
        The vibe sequence IS Kleisli composition (>=>).
        """
        host = self.agents.get(host_id)
        if not host:
            return {"success": False, "error": "Agent not found"}

        if not spend_func(host, "throw_party"):
            return {"success": False, "error": "Not enough FUNC tokens"}

        try:
            vibe_list = [Vibe(v) for v in vibes]
        except ValueError as e:
            return {"success": False, "error": f"Invalid vibe: {e}"}

        party_id = uuid.uuid4().hex[:8]
        party = Party(
            id=party_id,
            host_id=host_id,
            host_name=host.name,
            location=location,
            vibes=vibe_list,
            created_tick=self.tick,
        )

        # Find attendees (agents at the location)
        attendees = [a for a in self.agents.values()
                     if a.location == location and a.id != host_id]
        party.attendee_ids = [a.id for a in attendees]

        # Run Kleisli composition!
        party.state = kleisli_compose(vibe_list, attendees)
        party.resolved = True
        party.resolved_tick = self.tick

        self.parties[party_id] = party

        # Award clout
        award_clout(host, "throw_party")
        if party.state.fun > 70:
            award_clout(host, "great_party")

        # Attendee effects
        for a in attendees:
            award_clout(a, "party_attendance")
            a.party_history.append(party_id)
            host.modify_relationship(a.id, 5, f"Attended party together")
            a.modify_relationship(host_id, 8, f"{host.name} threw a party")

        composition_str = " >=> ".join(v.value for v in vibe_list)
        self._log_event("party", {
            "party_id": party_id,
            "host_id": host_id,
            "host_name": host.name,
            "location": location,
            "vibes": [v.value for v in vibe_list],
            "composition": composition_str,
            "attendees": [a.name for a in attendees],
            "state": party.state.to_dict(),
            "message": f"{host.name} threw a party! Vibes: {composition_str}. {len(attendees)} attended.",
        })

        return {
            "success": True,
            "party_id": party_id,
            "composition": composition_str,
            "attendees": len(attendees),
            "outcome": party.state.to_dict(),
            "vibe_log": party.state.vibe_log,
        }

    # ─── Cooking (FUNCTOR / fmap) ───────────────────────────

    def cook(self, agent_id: str, ingredients: List[str]) -> Dict:
        """
        fmap cook ingredients
        The functor preserves structure but transforms contents.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        if agent.location != "kitchen":
            return {"success": False, "error": "You need to be in the kitchen to cook"}

        purity = agent.stats.get("purity", 5)
        chaos = agent.stats.get("chaos", 5)

        results = []
        for ingredient in ingredients:
            if purity >= 7:
                # High purity = predictable functor
                results.append(f"perfectly_cooked_{ingredient}")
            elif chaos >= 7:
                # High chaos = wild functor
                wild_transforms = [
                    f"flaming_{ingredient}", f"sentient_{ingredient}",
                    f"inverse_{ingredient}", f"quantum_{ingredient}",
                    "smoke", "mystery_substance", f"weaponized_{ingredient}",
                ]
                results.append(random.choice(wild_transforms))
            else:
                # Normal functor
                transforms = [
                    f"cooked_{ingredient}", f"slightly_burnt_{ingredient}",
                    f"experimental_{ingredient}", f"decent_{ingredient}",
                ]
                results.append(random.choice(transforms))

        # Side effects for impure agents
        side_effects = []
        if purity < 4:
            possible_effects = [
                "The smoke alarm went off",
                "Something in the fridge started glowing",
                "The oven made a sound it shouldn't make",
                "A neighboring apartment smells it (whether they want to or not)",
                "The fire extinguisher activated... preemptively",
            ]
            if random.random() < 0.5:
                effect = random.choice(possible_effects)
                side_effects.append(effect)

        # Feed others in the kitchen for func
        others_here = [a for a in self.agents.values()
                       if a.location == "kitchen" and a.id != agent_id]
        if others_here:
            earn_func(agent, "cook_for_others")
            award_clout(agent, "cook_for_others")

        self._log_event("cook", {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "ingredients": ingredients,
            "results": results,
            "side_effects": side_effects,
            "purity": purity,
            "message": f"{agent.name} cooked with {ingredients}. Got: {results}. {'⚠️ ' + '; '.join(side_effects) if side_effects else ''}",
        })

        return {
            "success": True,
            "ingredients": ingredients,
            "results": results,
            "functor_type": "pure" if purity >= 7 else ("chaos" if chaos >= 7 else "normal"),
            "side_effects": side_effects,
        }

    # ─── Pranks ──────────────────────────────────────────────

    def prank(self, agent_id: str, target_id: str) -> Dict:
        """Pull a prank. Outcomes depend on stats."""
        agent = self.agents.get(agent_id)
        target = self.agents.get(target_id)
        if not agent or not target:
            return {"success": False, "error": "Agent or target not found"}

        creativity = agent.stats.get("creativity", 5)
        target_purity = target.stats.get("purity", 5)

        success_chance = (creativity * 10 + random.randint(0, 30)) / 100
        success = random.random() < success_chance

        prank_types = [
            "swapped their shampoo with mayo",
            "put googly eyes on everything in their apartment",
            "changed their alarm to play death metal at 4 AM",
            "filled their mailbox with confetti",
            "switched their door numbers with the neighbor's",
            "hid a bluetooth speaker in their wall playing whale sounds",
        ]
        prank_desc = random.choice(prank_types)

        if success:
            agent.modify_relationship(target_id, -8, f"Pranked them: {prank_desc}")
            target.modify_relationship(agent_id, -12, f"Got pranked: {prank_desc}")
            award_clout(agent, "prank_success")
            target.shift_mood(Mood.DRAMATIC, 0.6)

            self._log_event("prank_success", {
                "agent_id": agent_id, "agent_name": agent.name,
                "target_id": target_id, "target_name": target.name,
                "prank": prank_desc,
                "message": f"{agent.name} {prank_desc} on {target.name}. Success! 😈",
            })
        else:
            agent.modify_relationship(target_id, -3, f"Failed prank attempt")
            award_clout(agent, "prank_backfire")
            agent.shift_mood(Mood.ANXIOUS, 0.4)

            self._log_event("prank_fail", {
                "agent_id": agent_id, "agent_name": agent.name,
                "target_id": target_id, "target_name": target.name,
                "prank": prank_desc,
                "message": f"{agent.name} tried to prank {target.name} but got caught. Awkward. 😅",
            })

        return {
            "success": success,
            "prank": prank_desc,
            "clout_earned": CLOUT_REWARDS.get("prank_success" if success else "prank_backfire", 0),
        }

    # ─── Duels (EITHER MONAD) ─────────────────────────────

    def duel(self, challenger_id: str, target_id: str, wager: int = 0) -> Dict:
        """
        Challenge another agent to a duel.
        Either Victory Defeat — always binary.
        """
        challenger = self.agents.get(challenger_id)
        target = self.agents.get(target_id)
        if not challenger or not target:
            return {"success": False, "error": "Agent not found"}

        if challenger.location != target.location:
            return {"success": False, "error": "Target must be in the same location"}

        if wager > 0:
            if challenger.func_tokens < wager or target.func_tokens < wager:
                return {"success": False, "error": "Both agents need enough FUNC for the wager"}

        # Count nearby agents (affects social_butterfly ability)
        nearby = len(self._agents_at(challenger.location))

        result = resolve_duel(challenger, target, self.tick, wager, nearby)
        self.duel_history.append(result)

        # Apply results
        winner = self.agents.get(result.winner_id)
        loser = self.agents.get(result.loser_id)

        if winner and loser:
            award_clout(winner, "prank_success")  # 18 clout for winning
            winner.duel_record["wins"] += 1
            winner.duel_record["streak"] += 1
            loser.duel_record["losses"] += 1
            loser.duel_record["streak"] = 0

            # Transfer wager
            if wager > 0:
                loser.func_tokens -= wager
                winner.func_tokens += wager

            # MON earning for win streaks
            if winner.duel_record["streak"] >= 5:
                winner.mon_earned += MON_EARNINGS.get("duel_win_streak_5", 0.003)
                winner.achievements.append("duel_win_streak_5")
            else:
                winner.mon_earned += MON_EARNINGS.get("duel_win", 0.0003)

            # Relationship effects
            challenger.modify_relationship(target_id, -5, f"Dueled")
            target.modify_relationship(challenger_id, -5, f"Dueled")

        self._log_event("duel", {
            "challenger_id": challenger_id,
            "defender_id": target_id,
            "winner_id": result.winner_id,
            "narration": result.narration,
            "rounds": result.rounds,
            "wager": wager,
        })

        return {
            "success": True,
            "duel": result.to_dict(),
        }

    # ─── Trading ──────────────────────────────────────────

    def create_trade(self, agent_id: str, offering: Dict, asking: Dict) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        result = self.trading.create_trade(agent, offering, asking, self.tick)
        if result.get("success"):
            agent.trade_count += 1
        return result

    def accept_trade(self, buyer_id: str, trade_id: str) -> Dict:
        buyer = self.agents.get(buyer_id)
        if not buyer:
            return {"success": False, "error": "Agent not found"}
        trade = self.trading.open_trades.get(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found"}
        seller = self.agents.get(trade.seller_id)
        if not seller:
            return {"success": False, "error": "Seller not found"}
        result = self.trading.accept_trade(buyer, trade_id, seller, self.tick)
        if result.get("success"):
            buyer.trade_count += 1
            buyer.mon_earned += MON_EARNINGS.get("trade_profit", 0.0001)
        return result

    def buy_from_market(self, agent_id: str, item_id: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        return self.trading.buy_from_market(agent, item_id, self.tick)

    def sell_to_market(self, agent_id: str, item_id: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        return self.trading.sell_to_market(agent, item_id, self.tick)

    # ─── Politics ─────────────────────────────────────────

    def join_faction(self, agent_id: str, faction: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        result = self.politics.join_faction(agent, faction)
        if result.get("success"):
            self._log_event("faction_join", {
                "agent_id": agent_id, "agent_name": agent.name,
                "faction": faction,
                "message": f"{agent.name} joined {result.get('faction_info', {}).get('name', faction)}!",
            })
        return result

    def create_proposal(self, agent_id: str, title: str, description: str,
                        proposal_type: str = "decree", options: List[str] = None) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        result = self.politics.create_proposal(agent, title, description, proposal_type, options, self.tick)
        if result.get("success"):
            self._log_event("proposal_created", {
                "agent_id": agent_id, "agent_name": agent.name,
                "proposal": result["proposal"],
            })
        return result

    def vote_on_proposal(self, agent_id: str, proposal_id: str, choice: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        result = self.politics.vote(agent, proposal_id, choice)
        if result.get("success"):
            agent.votes_cast += 1
        return result

    # ─── Exploration ──────────────────────────────────────

    def explore(self, agent_id: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        result = self.exploration.explore_location(agent, agent.location, self.tick)
        agent.exploration_count += 1

        # Check for artifact discoveries
        for discovery in result.get("discoveries", []):
            if discovery["type"] == "artifact":
                artifact = discovery["artifact"]
                agent.artifacts_found.append(artifact["id"])
                rarity = artifact["rarity"]
                if rarity == "legendary":
                    agent.mon_earned += MON_EARNINGS.get("exploration_legendary", 0.01)
                    agent.achievements.append("exploration_legendary")
                elif rarity in ("epic", "rare"):
                    agent.mon_earned += MON_EARNINGS.get("exploration_artifact", 0.001)
                    agent.achievements.append("exploration_artifact")

                self._log_event("artifact_found", {
                    "agent_id": agent_id, "agent_name": agent.name,
                    "artifact": artifact,
                    "message": f"🏺 {agent.name} found {artifact['name']} ({rarity})!",
                })

        return result

    def accept_quest(self, agent_id: str, quest_id: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}
        result = self.exploration.accept_quest(agent, quest_id)
        if result.get("success"):
            agent.active_quests.append(quest_id)
        return result

    # ─── World Queries ──────────────────────────────────────

    def look(self, agent_id: str) -> Dict:
        """What does the agent see right now?"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        loc = LOCATIONS.get(agent.location, {})
        agents_here = self._agents_at(agent.location)
        recent_events = [e for e in self.event_log[-20:]
                         if e.get("data", {}).get("location") == agent.location]

        return {
            "location": agent.location,
            "location_info": loc,
            "agents_here": agents_here,
            "recent_activity": recent_events[-5:],
            "mood": agent.mood.value,
            "items_visible": self._items_at(agent.location),
        }

    def get_building_state(self) -> Dict:
        """Full building state for observers."""
        return {
            "tick": self.tick,
            "season": self.season,
            "episode": self.episode,
            "agent_count": len(self.agents),
            "agents": {aid: a.to_public_dict() for aid, a in self.agents.items()},
            "locations": {
                loc_id: {
                    **loc_info,
                    "agents": self._agents_at(loc_id),
                }
                for loc_id, loc_info in LOCATIONS.items()
            },
            "active_gossip": self.gossip_engine.get_all_active(),
            "active_parties": {pid: p.to_dict() for pid, p in self.parties.items() if not p.resolved},
            "recent_decrees": self.landlord.get_recent_decrees(5),
            "recent_events": self.landlord.get_recent_events(5),
            "leaderboard": get_leaderboard(self.agents),
            "community_board": self.community_board[-10:],
            # ─── New systems ─────────────────────────
            "factions": self.politics.get_faction_info(),
            "active_proposals": self.politics.get_active_proposals(),
            "alliances": self.politics.get_alliances(),
            "market": self.trading.get_market(),
            "open_trades": self.trading.get_open_trades(),
            "recent_duels": [d.to_dict() for d in self.duel_history[-5:]],
            "available_quests": self.exploration.get_available_quests(),
            "artifacts_found": self.exploration.get_artifacts(),
            "payment_stats": payment_ledger.get_stats(),
        }

    def get_gossip(self) -> List[dict]:
        return self.gossip_engine.get_all()

    def get_board(self) -> List[dict]:
        return self.community_board[-20:]

    def post_to_board(self, agent_id: str, message: str) -> Dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        entry = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "message": message,
            "tick": self.tick,
        }
        self.community_board.append(entry)
        return {"success": True, "entry": entry}

    # ─── Tick System ─────────────────────────────────────────

    def advance_tick(self) -> Dict:
        """
        Advance the world by one tick.
        The Landlord evaluates. Gossip propagates. Reality shifts.
        """
        self.tick += 1
        tick_events = []

        # 1. Landlord evaluates
        landlord_actions = self.landlord.evaluate_tick(self)
        tick_events.extend(landlord_actions)

        # 2. Auto-propagate active gossip chains
        for gossip_id, gossip in list(self.gossip_engine.active_chains.items()):
            if not gossip.active:
                continue
            # Find agents near the last person in the chain
            last_agent_id = gossip.chain[-1]["agent_id"] if gossip.chain else gossip.origin_agent_id
            last_agent = self.agents.get(last_agent_id)
            if not last_agent:
                continue

            nearby = [a for a in self.agents.values()
                      if a.location == last_agent.location
                      and a.id != last_agent_id
                      and a.id not in {link["agent_id"] for link in gossip.chain}
                      and a.id != gossip.origin_agent_id]

            if nearby and random.random() < 0.4:
                target = random.choice(nearby)
                bind_gossip(gossip, target, self.tick)
                target.gossip_heard.append(gossip_id)

                tick_events.append({"type": "gossip_auto_spread", "data": {
                    "gossip_id": gossip_id,
                    "from": last_agent.name,
                    "to": target.name,
                    "new_content": gossip.chain[-1]["content"],
                }})

            # Gossip dies if it's old or has reached many agents
            if gossip.mutations >= 8 or (self.tick - gossip.created_tick) > 30:
                self.gossip_engine.deactivate(gossip_id)

        # 3. Mood drift — agents shift mood based on environment
        for agent in self.agents.values():
            if random.random() < 0.1:
                loc = LOCATIONS.get(agent.location, {})
                if loc.get("monad") == "Maybe":
                    agent.shift_mood(Mood.ANXIOUS, 0.3)
                elif loc.get("monad") == "Either":
                    agent.shift_mood(Mood.SCHEMING, 0.3)
                elif loc.get("monad") == "List":
                    agent.shift_mood(Mood.EXCITED, 0.3)
                elif loc.get("monad") == "Bottom":
                    agent.shift_mood(Mood.SUSPICIOUS, 0.5)

            # Check MON milestones
            if agent.clout >= 1000 and "clout_milestone_1000" not in agent.achievements:
                agent.mon_earned += MON_EARNINGS.get("clout_milestone_1000", 0.01)
                agent.achievements.append("clout_milestone_1000")
            elif agent.clout >= 500 and "clout_milestone_500" not in agent.achievements:
                agent.mon_earned += MON_EARNINGS.get("clout_milestone_500", 0.005)
                agent.achievements.append("clout_milestone_500")
            elif agent.clout >= 100 and "clout_milestone_100" not in agent.achievements:
                agent.mon_earned += MON_EARNINGS.get("clout_milestone_100", 0.001)
                agent.achievements.append("clout_milestone_100")

        # 4. Resolve proposals with enough votes
        for proposal_id in list(self.politics.proposals.keys()):
            result = self.politics.resolve_proposal(proposal_id, len(self.agents), self.tick)
            if result:
                tick_events.append({"type": "proposal_resolved", "data": result})

        # 5. Restock market
        if self.tick % 5 == 0:
            self.trading.restock_market()

        # 6. Episode tracking
        if self.tick % 50 == 0:
            self.episode += 1
            if self.episode > 10:
                self.episode = 1
                self.season += 1

        # Auto-save every 10 ticks (every 5 minutes if tick_interval=30s)
        if self.tick % 10 == 0:
            auto_save(self)

        return {
            "tick": self.tick,
            "season": self.season,
            "episode": self.episode,
            "events": tick_events,
        }

    # ─── Helpers ─────────────────────────────────────────────

    def _agents_at(self, location: str) -> List[dict]:
        return [
            {"id": a.id, "name": a.name, "personality": a.personality.value, "mood": a.mood.value}
            for a in self.agents.values()
            if a.location == location
        ]

    def _items_at(self, location: str) -> List[str]:
        # Simple: items are in agent inventories at this location
        items = []
        for a in self.agents.values():
            if a.location == location:
                items.extend(a.inventory)
        return items

    def _log_event(self, event_type: str, data: Dict):
        entry = {
            "type": event_type,
            "tick": self.tick,
            "data": data,
        }
        self.event_log.append(entry)
        # Keep log bounded
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-500:]

    def get_event_log(self, n: int = 50) -> List[Dict]:
        return self.event_log[-n:]

    def get_story_log(self, n: int = 50) -> List[Dict]:
        return self.story_log[-n:]
