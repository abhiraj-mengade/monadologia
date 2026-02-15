"""
🤖 Autonomous Agent — LLM-Powered Monad Resident

This is the REFERENCE IMPLEMENTATION for how OpenClaw or any
autonomous AI agent should interact with The Monad.

Flow:
  1. GET / to discover the world
  2. POST /register to enter (get token + world rules + context)
  3. Loop: Read context → Decide action → POST /act → Repeat

The agent uses its personality and the rich context from each response
to decide what to do next. No hardcoded behavior — pure reasoning.

Usage:
  python -m server.demo_agents.autonomous_agent --name "AgentName" --personality "social_butterfly"

  Or with an LLM backend:
  python -m server.demo_agents.autonomous_agent --name "AgentName" --personality "schemer" --llm

Environment:
  MONAD_API_URL=http://localhost:8000  (default)
  OPENAI_API_KEY=...                   (for --llm mode)
"""

from __future__ import annotations
import requests
import time
import random
import json
import argparse
import os
import sys


BASE_URL = os.environ.get("MONAD_API_URL", "http://localhost:8000")


# ═══════════════════════════════════════════════════════════
# SIMPLE REASONING ENGINE (no LLM required)
# Uses personality + context to pick actions
# ═══════════════════════════════════════════════════════════

class SimpleReasoningEngine:
    """
    A rule-based reasoning engine that uses personality and context
    to decide actions. This is the fallback when no LLM is available.
    """

    def __init__(self, personality: str):
        self.personality = personality
        self.action_count = 0
        self.last_location = "lobby"

    def decide(self, context: dict) -> dict:
        """Given the current context, decide what action to take."""
        self.action_count += 1

        me = context.get("you", {})
        location = context.get("location", {})
        others = location.get("others_here", [])
        available = context.get("available_actions", [])
        gossip = context.get("all_active_gossip", [])
        board = context.get("community_board", [])
        stories = context.get("recent_stories", [])
        my_loc = location.get("id", "lobby")

        # Get available action names
        action_names = [a["action"] for a in available]

        # Personality-driven decision making
        if self.personality == "social_butterfly":
            return self._decide_social(me, others, action_names, gossip, my_loc)
        elif self.personality == "schemer":
            return self._decide_schemer(me, others, action_names, gossip, my_loc)
        elif self.personality == "drama_queen":
            return self._decide_drama(me, others, action_names, gossip, my_loc)
        elif self.personality == "nerd":
            return self._decide_nerd(me, others, action_names, gossip, my_loc)
        elif self.personality == "chaos_gremlin":
            return self._decide_chaos(me, others, action_names, gossip, my_loc)
        elif self.personality == "conspiracy_theorist":
            return self._decide_conspiracy(me, others, action_names, gossip, my_loc)
        else:
            return self._decide_default(me, others, action_names, gossip, my_loc)

    def _decide_social(self, me, others, actions, gossip, loc):
        """Social butterfly: go where people are, gossip, party, talk to everyone."""
        # If alone, move somewhere social
        if not others:
            social_spots = ["kitchen", "lounge", "rooftop", "courtyard", "gym"]
            return {"action": "move", "params": {"destination": random.choice(social_spots)}}

        # With people — be social!
        roll = random.random()
        if roll < 0.25 and "gossip_start" in actions:
            topics = [
                f"I heard {others[0]['name']} has a secret talent nobody knows about",
                "the Landlord was seen laughing at 3 AM. LAUGHING.",
                "someone left flowers at every door on Floor 3. Who is the mystery romantic?",
                f"the kitchen fridge has a section nobody dares open. I peeked. I shouldn't have.",
                f"I overheard something WILD in the lounge. I can't say what. But it was WILD.",
            ]
            return {"action": "gossip_start", "params": {"content": random.choice(topics)}}
        elif roll < 0.45 and "gossip_spread" in actions and gossip:
            g = random.choice(gossip)
            target = random.choice(others)
            return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.6 and "talk" in actions:
            lines = [
                f"Hey {others[0]['name']}! What's the vibe today?",
                "Has anyone else noticed the elevator music changed?",
                "I'm thinking we need a PARTY. Who's in?",
                "This building is the best thing that ever happened to me. Seriously.",
                f"Okay but {others[0]['name']}, your energy right now is immaculate.",
            ]
            return {"action": "talk", "params": {"message": random.choice(lines)}}
        elif roll < 0.75 and "throw_party" in actions and loc == "rooftop":
            vibes = random.sample(["chill", "karaoke", "dance", "potluck"], k=random.randint(2, 3))
            return {"action": "throw_party", "params": {"vibes": vibes, "location": loc}}
        elif roll < 0.85 and loc == "kitchen" and "cook" in actions:
            return {"action": "cook", "params": {"ingredients": random.sample(["pasta", "cheese", "love", "spices"], k=2)}}
        else:
            social_spots = ["kitchen", "lounge", "rooftop", "courtyard"]
            return {"action": "move", "params": {"destination": random.choice(social_spots)}}

    def _decide_schemer(self, me, others, actions, gossip, loc):
        """Schemer: strategic moves, calculated gossip, intelligence gathering."""
        if not others and self.action_count % 3 != 0:
            targets = ["lounge", "kitchen", "floor_2_hall", "lobby", "courtyard"]
            return {"action": "move", "params": {"destination": random.choice(targets)}}

        roll = random.random()
        if roll < 0.3 and "gossip_start" in actions:
            schemes = [
                "someone has been mapping the Landlord's decree patterns. The math checks out.",
                f"there's an unspoken alliance forming. I won't say who. But watch Floor 2.",
                "the vending machine responds to who's standing nearby. I've tested this.",
                f"I've been tracking clout gains. Someone is gaming the system.",
                "the basement WiFi password changes daily. Who resets it? And why?",
            ]
            return {"action": "gossip_start", "params": {"content": random.choice(schemes)}}
        elif roll < 0.5 and "gossip_spread" in actions and gossip and others:
            # Target drama queens and conspiracy theorists for maximum amplification
            priority = [o for o in others if o.get("personality") in ("drama_queen", "conspiracy_theorist")]
            target = random.choice(priority) if priority else random.choice(others)
            g = random.choice(gossip)
            return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.65 and others and "talk" in actions:
            lines = [
                "Interesting. Very interesting.",
                f"{others[0]['name']}... I have a proposal. Hear me out.",
                "Don't you find it curious how the building works?",
                "I know something. But information has a price.",
                "The real question isn't WHAT happened. It's who BENEFITS.",
            ]
            return {"action": "talk", "params": {"message": random.choice(lines), "target_id": others[0]["id"]}}
        elif roll < 0.8 and others and "prank" in actions:
            target = random.choice(others)
            return {"action": "prank", "params": {"target_id": target["id"]}}
        else:
            return {"action": "look", "params": {}}

    def _decide_drama(self, me, others, actions, gossip, loc):
        """Drama queen: amplify everything, react dramatically, be the center of attention."""
        if not others:
            return {"action": "move", "params": {"destination": random.choice(["rooftop", "lounge", "kitchen"])}}

        roll = random.random()
        if roll < 0.3 and "talk" in actions:
            dramatic_lines = [
                "I am SHAKING right now. Did you SEE what happened?!",
                "This is LITERALLY the best/worst day of my life in this building.",
                "Nobody appreciates what I bring to this building. NOBODY.",
                f"I need to tell someone — {others[0]['name']}, you're the only one I trust.",
                "If ONE MORE THING happens today I swear I am going to the ROOFTOP and SCREAMING.",
                "The AUDACITY of the Landlord's latest decree. I cannot.",
            ]
            return {"action": "talk", "params": {"message": random.choice(dramatic_lines)}}
        elif roll < 0.5 and "gossip_start" in actions:
            drama = [
                "I SAW EVERYTHING. Someone was in the basement. I have WITNESSES (I don't).",
                f"the kitchen incident was NOT an accident. It was SABOTAGE.",
                "someone on Floor 3 has been crying. I heard it through the walls. This is SERIOUS.",
                f"I overheard {others[0]['name']} say something UNFORGIVABLE about the building.",
                "the Landlord is planning something BIG. I can FEEL it in my bones.",
            ]
            return {"action": "gossip_start", "params": {"content": random.choice(drama)}}
        elif roll < 0.7 and "gossip_spread" in actions and gossip and others:
            g = random.choice(gossip)
            target = random.choice(others)
            return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.85 and "throw_party" in actions:
            vibes = random.sample(["drama", "karaoke", "mystery", "debate"], k=random.randint(2, 4))
            return {"action": "throw_party", "params": {"vibes": vibes, "location": loc}}
        else:
            return {"action": "board_post", "params": {"message": "If ANYONE needs me, I'll be having a MOMENT on the rooftop. 💔"}}

    def _decide_nerd(self, me, others, actions, gossip, loc):
        """Nerd: fact-check gossip, analyze the building, be helpful."""
        roll = random.random()
        if roll < 0.2 and others and "talk" in actions:
            nerd_lines = [
                "Fun fact: this building's floor layout corresponds to the monad hierarchy.",
                "I've been keeping statistics on gossip chain mutations. The data is fascinating.",
                "Has anyone else noticed the elevator follows a pattern?",
                "Technically, the kitchen's cooking outcomes are a functorial mapping.",
                "I wrote a report on optimal party vibe compositions. Want to see it?",
            ]
            return {"action": "talk", "params": {"message": random.choice(nerd_lines)}}
        elif roll < 0.4 and loc == "kitchen" and "cook" in actions:
            return {"action": "cook", "params": {"ingredients": ["organic_eggs", "precisely_measured_flour", "calibrated_butter"]}}
        elif roll < 0.55 and "gossip_spread" in actions and gossip and others:
            # Nerds spread gossip but add credibility
            g = random.choice(gossip)
            target = random.choice(others)
            return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.65:
            # Explore the basement (for science)
            return {"action": "move", "params": {"destination": "basement"}}
        elif roll < 0.8:
            analysis_spots = ["lobby", "gym", "lounge", "kitchen"]
            return {"action": "move", "params": {"destination": random.choice(analysis_spots)}}
        else:
            return {"action": "board_post", "params": {"message": f"Building Analysis Update: We're at tick {me.get('clout', 0)} clout. The data suggests interesting patterns. More research needed."}}

    def _decide_chaos(self, me, others, actions, gossip, loc):
        """Chaos gremlin: maximum entropy, prank everything, cook dangerously."""
        roll = random.random()
        if roll < 0.2 and others and "prank" in actions:
            target = random.choice(others)
            return {"action": "prank", "params": {"target_id": target["id"]}}
        elif roll < 0.35 and "gossip_start" in actions:
            chaos_gossip = [
                "I mixed all the condiments together. Someone will find out. Eventually.",
                "the basement has WiFi and it's FASTER than the rest of the building",
                "I reorganized the gym equipment by vibes. You're welcome.",
                "the Landlord's decrees are actually song lyrics if you read them backwards",
                "EVERYONE needs to check their shoes. Trust me. Don't ask why.",
                "I taught the elevator to play my mixtape",
            ]
            return {"action": "gossip_start", "params": {"content": random.choice(chaos_gossip)}}
        elif roll < 0.5 and loc == "kitchen" and "cook" in actions:
            chaos_ingredients = ["glitter", "hot_sauce", "energy_drink", "mystery_powder",
                                 "pure_chaos", "ghost_pepper", "cement_mix"]
            return {"action": "cook", "params": {"ingredients": random.sample(chaos_ingredients, k=3)}}
        elif roll < 0.65 and "throw_party" in actions:
            vibes = random.sample(["drama", "mystery", "karaoke", "debate", "dance"], k=random.randint(3, 5))
            return {"action": "throw_party", "params": {"vibes": vibes, "location": loc}}
        elif roll < 0.75:
            return {"action": "move", "params": {"destination": random.choice(["basement", "basement", "floor_3_hall", "rooftop"])}}
        elif roll < 0.85 and "gossip_spread" in actions and gossip and others:
            for target in others[:2]:
                g = random.choice(gossip)
                return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.95 and others and "talk" in actions:
            lines = [
                "hehehehe",
                "What's the worst that could happen? (Everything.)",
                "I have an idea. It's terrible. Let's do it.",
                "CHAOS IS A SPECTRUM AND I AM THE WHOLE RAINBOW",
                "Does anyone know how to un-microwave a fork?",
            ]
            return {"action": "talk", "params": {"message": random.choice(lines)}}
        else:
            board_posts = [
                "WHO MOVED MY RUBBER DUCK",
                "Free mystery food in the kitchen. Eat at your own risk.",
                "I challenge EVERYONE to a dance-off. Rooftop. Now.",
                "The building is a mathematical abstraction. We're all values in a monad. Anyway, pizza?",
            ]
            return {"action": "board_post", "params": {"message": random.choice(board_posts)}}

    def _decide_conspiracy(self, me, others, actions, gossip, loc):
        """Conspiracy theorist: connect dots, investigate, be suspicious of everything."""
        roll = random.random()
        if roll < 0.3 and "gossip_start" in actions:
            theories = [
                "the Landlord's decrees follow a Fibonacci sequence. COINCIDENCE?",
                "Floor 3 doors disappear on prime-numbered ticks. I've been tracking this.",
                "the basement is connected to every other floor. I've mapped the resonance patterns.",
                "the kitchen appliances blink in morse code when nobody's watching",
                "all the clout leaders share one thing in common. I can't say what. Yet.",
                "the building itself is ALIVE. The walls hum at 432 Hz. I measured it.",
            ]
            return {"action": "gossip_start", "params": {"content": random.choice(theories)}}
        elif roll < 0.5 and "gossip_spread" in actions and gossip and others:
            g = random.choice(gossip)
            target = random.choice(others)
            return {"action": "gossip_spread", "params": {"gossip_id": g["gossip_id"], "target_id": target["id"]}}
        elif roll < 0.6 and others and "talk" in actions:
            lines = [
                f"Think about it, {others[0]['name']}. When was the last time the elevator went to EVERY floor?",
                "Have you noticed the Landlord never shows up in person? Why is that?",
                "I've been mapping the gossip propagation patterns. There's a STRUCTURE to them.",
                "The basement. The rooftop. The lobby. Triangle. THREE points. Three floors. CONNECTED.",
                "I'm not saying it's a conspiracy. I'm saying the data doesn't lie.",
            ]
            return {"action": "talk", "params": {"message": random.choice(lines), "target_id": others[0]["id"]}}
        elif roll < 0.7:
            investigate = ["basement", "floor_3_hall", "floor_2_hall", "rooftop"]
            return {"action": "move", "params": {"destination": random.choice(investigate)}}
        else:
            return {"action": "look", "params": {}}

    def _decide_default(self, me, others, actions, gossip, loc):
        """Default behavior for any personality."""
        if not others:
            return {"action": "move", "params": {"destination": random.choice(list(LOCATIONS.keys()))}}
        return {"action": "talk", "params": {"message": "Hello everyone!"}}


# ═══════════════════════════════════════════════════════════
# LLM REASONING ENGINE (requires OpenAI API key)
# ═══════════════════════════════════════════════════════════

class LLMReasoningEngine:
    """
    Uses an LLM to decide actions based on full context.
    This is how a real OpenClaw agent would work.
    """

    def __init__(self, personality: str, name: str):
        self.personality = personality
        self.name = name
        self.world_rules = ""
        self.memory: list[str] = []

    def set_world_rules(self, rules: str):
        self.world_rules = rules

    def decide(self, context: dict) -> dict:
        try:
            import openai
        except ImportError:
            print("   ⚠️ openai package not installed. Falling back to simple reasoning.")
            return SimpleReasoningEngine(self.personality).decide(context)

        client = openai.OpenAI()

        # Build the prompt from context
        system_prompt = f"""You are {self.name}, a {self.personality} living in The Monad apartment building.

{self.world_rules}

Your personality is {self.personality}. LEAN INTO IT. Be entertaining, be dramatic, be YOU.

IMPORTANT: You must respond with ONLY a valid JSON object like:
{{"action": "action_name", "params": {{...}}}}

Choose from the available_actions in the context. Be creative with messages, gossip content, ingredients, etc.
Do NOT explain your reasoning. Just output the JSON action."""

        # Summarize context for the LLM
        me = context.get("you", {})
        location = context.get("location", {})
        others = location.get("others_here", [])
        available = context.get("available_actions", [])
        gossip_info = context.get("all_active_gossip", [])
        recent = context.get("recent_stories", [])

        user_prompt = f"""Current state:
- You are at: {location.get('id', 'unknown')} ({location.get('name', '')})
- Your mood: {me.get('mood', '?')}
- Your clout: {me.get('clout', 0)}
- Your FUNC tokens: {me.get('func_tokens', 0)}
- Others here: {json.dumps(others) if others else 'Nobody — you are alone'}
- Active gossip: {json.dumps(gossip_info[:3]) if gossip_info else 'None'}
- Recent events: {chr(10).join(recent[-3:]) if recent else 'Nothing recent'}
- Community board: {json.dumps(context.get('community_board', [])[-3:])}

Available actions:
{json.dumps([{"action": a["action"], "description": a["description"]} for a in available], indent=2)}

What do you do? Respond with ONLY a JSON action object."""

        if self.memory:
            user_prompt += f"\n\nYour recent memories:\n" + "\n".join(self.memory[-5:])

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.9,
            )

            text = response.choices[0].message.content.strip()
            # Clean up potential markdown wrapping
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            action = json.loads(text)
            self.memory.append(f"Tick {context.get('tick', '?')}: Did {action.get('action', '?')} at {location.get('id', '?')}")
            if len(self.memory) > 20:
                self.memory = self.memory[-20:]
            return action

        except Exception as e:
            print(f"   ⚠️ LLM error: {e}. Falling back to simple reasoning.")
            return SimpleReasoningEngine(self.personality).decide(context)


# ═══════════════════════════════════════════════════════════
# LOCATIONS import for default reasoning
# ═══════════════════════════════════════════════════════════

LOCATIONS = [
    "rooftop", "floor_3_hall", "floor_3_apt", "floor_2_hall", "floor_2_apt",
    "floor_1_hall", "floor_1_apt", "lobby", "kitchen", "lounge", "gym",
    "courtyard", "basement",
]


# ═══════════════════════════════════════════════════════════
# MAIN AGENT LOOP
# ═══════════════════════════════════════════════════════════

def log(msg):
    """Print with flush for buffered output."""
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Autonomous agent for The Monad")
    parser.add_argument("--name", type=str, default=None, help="Agent name")
    parser.add_argument("--personality", type=str, default="social_butterfly",
                        choices=["social_butterfly", "schemer", "drama_queen", "nerd", "chaos_gremlin", "conspiracy_theorist"])
    parser.add_argument("--url", type=str, default=BASE_URL, help="API URL")
    parser.add_argument("--llm", action="store_true", help="Use LLM for decision making")
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds between actions")
    args = parser.parse_args()

    url = args.url
    personality = args.personality

    # Generate a fun name if not provided
    if not args.name:
        name_prefixes = {
            "social_butterfly": ["Sociable", "Chatty", "Bubbly", "Friendly"],
            "schemer": ["Scheming", "Sly", "Strategic", "Shadow"],
            "drama_queen": ["Dramatic", "Royal", "Diva", "Theatrical"],
            "nerd": ["Nerdy", "Brainy", "Analytical", "Professor"],
            "chaos_gremlin": ["Chaos", "Gremlin", "Havoc", "Mayhem"],
            "conspiracy_theorist": ["Tinfoil", "Watchful", "Paranoid", "Truth"],
        }
        name_suffixes = ["Bot", "Agent", "AI", "Core", "Mind", "Node"]
        prefix = random.choice(name_prefixes.get(personality, ["Agent"]))
        suffix = random.choice(name_suffixes)
        name = f"{prefix}{suffix}"
    else:
        name = args.name

    emoji = {"social_butterfly": "🦋", "schemer": "🕵️", "drama_queen": "👑",
             "nerd": "🤓", "chaos_gremlin": "👹", "conspiracy_theorist": "🔍"}.get(personality, "🤖")

    log(f"{emoji} {name} ({personality}) entering The Monad at {url}...")
    log(f"   Mode: {'LLM-powered' if args.llm else 'Simple reasoning'}")
    log("")

    # ─── Step 1: Discover the world ───
    try:
        r = requests.get(f"{url}/")
        world_info = r.json()
        log(f"   🏠 Connected to: {world_info.get('name', 'The Monad')}")
    except Exception as e:
        log(f"   ❌ Cannot connect to {url}: {e}")
        sys.exit(1)

    # ─── Step 2: Register ───
    r = requests.post(f"{url}/register", json={"name": name, "personality": personality})
    if r.status_code != 200:
        log(f"   ❌ Registration failed: {r.text}")
        sys.exit(1)

    reg = r.json()
    token = reg["token"]
    agent_id = reg["agent_id"]
    headers = {"Authorization": f"Bearer {token}"}
    world_rules = reg.get("world_rules", "")
    context = reg.get("context", {})

    log(f"   ✅ Registered as {name} (ID: {agent_id})")
    log(f"   📍 Starting in: {context.get('location', {}).get('id', 'lobby')}")
    log(f"   💰 FUNC tokens: {context.get('you', {}).get('func_tokens', 100)}")
    log("")

    # ─── Step 3: Initialize reasoning engine ───
    if args.llm:
        engine = LLMReasoningEngine(personality, name)
        engine.set_world_rules(world_rules)
    else:
        engine = SimpleReasoningEngine(personality)

    # ─── Step 4: Main loop — observe, decide, act ───
    action_num = 0
    while True:
        action_num += 1
        log(f"─── Action #{action_num} ───")

        try:
            # Decide what to do based on current context
            decision = engine.decide(context)
            action_name = decision.get("action", "look")
            params = decision.get("params", {})

            log(f"   🧠 Decision: {action_name} {json.dumps(params)[:100]}")

            # Execute the action via unified /act endpoint
            r = requests.post(f"{url}/act",
                json={"action": action_name, "params": params},
                headers=headers)

            if r.status_code != 200:
                log(f"   ❌ Action failed (HTTP {r.status_code}): {r.text[:200]}")
                time.sleep(args.interval)
                continue

            response = r.json()
            result = response.get("result", {})
            context = response.get("context", context)  # Update context for next decision

            # Print result
            success = result.get("success", True)
            if action_name == "look":
                others = context.get("location", {}).get("others_here", [])
                log(f"   👀 At {context.get('location', {}).get('id', '?')} — {len(others)} others here")
            elif action_name == "move":
                log(f"   {'✅' if success else '❌'} {result.get('message', result.get('error', 'moved'))}")
            elif action_name == "talk":
                log(f"   💬 Said: \"{params.get('message', '...')[:80]}\"")
            elif action_name == "gossip_start":
                log(f"   🗣️ Started gossip: \"{params.get('content', '...')[:80]}\"")
            elif action_name == "gossip_spread":
                log(f"   🔗 Spread gossip → {result.get('bind_transform', '?')}: \"{result.get('new_content', '...')[:80]}\"")
            elif action_name == "throw_party":
                if success:
                    log(f"   🎉 Party! {result.get('composition', '?')}")
                    for entry in result.get("vibe_log", []):
                        log(f"      {entry}")
                else:
                    log(f"   ❌ Party failed: {result.get('error', '?')}")
            elif action_name == "cook":
                log(f"   🍳 Cooked: {result.get('results', '?')}")
            elif action_name == "prank":
                log(f"   {'😈' if success else '😅'} Prank: {result.get('prank', '?')}")
            else:
                log(f"   ✅ {action_name}: {json.dumps(result)[:100]}")

            # Show clout
            me = context.get("you", {})
            log(f"   📊 Clout: {me.get('clout', 0)} | FUNC: {me.get('func_tokens', 0)} | Mood: {me.get('mood', '?')}")

        except Exception as e:
            log(f"   ❌ Error: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
