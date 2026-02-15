"""
narrator.py — The Narration Engine

Takes raw action results and produces entertaining prose.
Reads like a sitcom script. This is the STAR of the show.

The narrator observes the mathematical reality and translates it
into human-readable comedy. It's the natural transformation
from Category Theory → Entertainment.
"""

from __future__ import annotations
import random
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════
# PERSONALITY FLAVOR TEXT
# ═══════════════════════════════════════════════════════════

PERSONALITY_DESCRIPTORS = {
    "social_butterfly": [
        "with the energy of someone who just had three espressos",
        "radiating main character energy",
        "already knowing everyone's name somehow",
        "practically vibrating with social enthusiasm",
    ],
    "schemer": [
        "with a suspiciously casual demeanor",
        "eyes darting to every exit",
        "already three moves ahead in a game nobody else is playing",
        "smiling in a way that could mean anything",
    ],
    "drama_queen": [
        "as if arriving at their own premiere",
        "with the gravitas of a Shakespearean entrance",
        "sighing loudly enough for everyone to notice",
        "making every moment a scene",
    ],
    "nerd": [
        "quietly observing the structural integrity of the room",
        "adjusting something that didn't need adjusting",
        "with a look that says 'I have opinions about this'",
        "taking mental notes for reasons unknown",
    ],
    "chaos_gremlin": [
        "with chaotic intent clearly visible",
        "grinning in a way that should worry everyone",
        "already touching things they shouldn't",
        "leaving a trail of minor disturbances",
    ],
    "conspiracy_theorist": [
        "scanning the room for hidden cameras",
        "squinting at the ceiling tiles suspiciously",
        "connecting invisible dots",
        "pausing to write something in a tiny notebook",
    ],
}

# ═══════════════════════════════════════════════════════════
# EVENT NARRATION TEMPLATES
# ═══════════════════════════════════════════════════════════

def narrate_event(event: Dict) -> Optional[str]:
    """Turn a raw event into entertaining prose."""
    event_type = event.get("type", "")
    data = event.get("data", {})
    tick = event.get("tick", 0)

    narrator_fn = EVENT_NARRATORS.get(event_type)
    if narrator_fn:
        return narrator_fn(data, tick)
    return None


def _narrate_enter(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    personality = data.get("personality", "unknown")
    flavor = random.choice(PERSONALITY_DESCRIPTORS.get(personality, ["mysteriously"]))

    intros = [
        f"**{name}** has entered The Monad, {flavor}. There is no escape function. Welcome home.",
        f"The lobby door swings open. **{name}** walks in {flavor}. Another soul enters the monad. `pure {name}` has been evaluated.",
        f"A new resident! **{name}** steps into The Monad {flavor}. The building hums with recognition. `return {name}` — you're in the context now.",
    ]
    return random.choice(intros)


def _narrate_move(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    to_loc = data.get("to", "somewhere")
    from_loc = data.get("from", "somewhere")

    moves = [
        f"**{name}** headed from {from_loc} to {to_loc}.",
        f"**{name}** made their way to {to_loc}. The building noted the transition.",
        f"Footsteps in the hallway. **{name}** is on the move — destination: {to_loc}.",
    ]
    return random.choice(moves)


def _narrate_move_nothing(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    dest = data.get("destination", "Floor 3")

    nothings = [
        f"**{name}** reached for the door to {dest}. The door was not there. The Maybe monad returned `Nothing`. They stood in the hallway, questioning reality.",
        f"**{name}** tried to enter {dest} and found... nothing. Literally nothing. The doorway was a wall. It'll probably be back tomorrow. Maybe.",
        f"Where {dest} should be, **{name}** found only smooth wall. The Maybe floor giveth and the Maybe floor taketh away. Today it tooketh.",
    ]
    return random.choice(nothings)


def _narrate_move_either(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    direction = data.get("direction", "Left")

    eithers = [
        f"**{name}** hit the Fork of Floor 2. Left or Right. No middle ground. They went **{direction}**. `{direction} {name.lower()}` was the result.",
        f"The hallway split. As it always does. **{name}** chose **{direction}**. The Either monad demands a decision and it got one.",
        f"Fork in the path. **{name}** didn't hesitate — **{direction}**. On Floor 2, there is no 'maybe later.' Only `Left` or `Right`.",
    ]
    return random.choice(eithers)


def _narrate_move_list(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    branches = data.get("branches", 2)

    lists = [
        f"**{name}** entered Floor 1 and immediately existed in {branches} conversations simultaneously. The List monad is generous with possibilities.",
        f"Floor 1 greeted **{name}** with {branches} parallel realities. One where they're by the window. One by the door. One somehow in both places. Nondeterminism is fun.",
        f"**{name}** walked into Floor 1. {branches} things happened at once. All of them were real. None of them were contradictory. Don't think about it too hard.",
    ]
    return random.choice(lists)


def _narrate_move_bottom(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")

    bottoms = [
        f"**{name}** descended into the basement. Time dilated. Space folded. They emerged somewhere else entirely, unsure how long they'd been gone. `⊥` was evaluated and the runtime had Opinions.",
        f"The basement swallowed **{name}** briefly. What they saw down there... they won't say. They came out somewhere unexpected. The Bottom (⊥) is not a place. It's a warning.",
        f"**{name}** went to the basement and encountered infinite recursion. By the time the stack unwound, they were in a completely different part of the building. Time is a suggestion down there.",
    ]
    return random.choice(bottoms)


def _narrate_talk_private(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    target = data.get("target_name", "someone")
    message = data.get("message", "...")
    location = data.get("location", "somewhere")

    talks = [
        f'**{name}** pulled **{target}** aside in the {location}. "{message}"',
        f'In the {location}, **{name}** leaned over to **{target}**: "{message}"',
        f'A private moment in the {location}. **{name}** to **{target}**: "{message}"',
    ]
    return random.choice(talks)


def _narrate_talk_room(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    message = data.get("message", "...")
    location = data.get("location", "somewhere")

    talks = [
        f'**{name}** announced to the {location}: "{message}"',
        f'The {location} fell quiet as **{name}** spoke: "{message}"',
        f'**{name}**, addressing nobody and everybody in the {location}: "{message}"',
    ]
    return random.choice(talks)


def _narrate_gossip_start(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    content = data.get("content", "something")

    starts = [
        f'🗣️ **{name}** started a rumor: *"{content}"* — The gossip chain begins. `return "{content}"` enters the gossip monad.',
        f'🗣️ A new gossip chain spawned! **{name}** whispered to the nearest ear: *"{content}"* — Let the bind operations commence.',
        f'🗣️ It begins with **{name}**: *"{content}"* — An innocent statement enters the gossip monad. It will not come out the same way.',
    ]
    return random.choice(starts)


def _narrate_gossip_spread(data: Dict, tick: int) -> str:
    agent_name = data.get("agent_name", "Someone")
    target_name = data.get("target_name", "someone")
    new_content = data.get("new_content", "...")
    chain_length = data.get("chain_length", 1)
    credibility = data.get("credibility", 50)
    spiciness = data.get("spiciness", 50)

    bind_desc = f"Chain length: {chain_length}. Credibility: {credibility}%. Spiciness: {spiciness}%."

    spreads = [
        f'🔗 **{agent_name}** told **{target_name}**. Through the lens of {target_name}\'s personality, it became: *"{new_content}"* — {bind_desc}',
        f'🔗 The gossip passed from **{agent_name}** to **{target_name}** (`>>=`). The message transformed: *"{new_content}"* — {bind_desc}',
        f'🔗 `gossip >>= {target_name.lower()}` — *"{new_content}"* — Each bind transforms the content. {bind_desc}',
    ]
    return random.choice(spreads)


def _narrate_party(data: Dict, tick: int) -> str:
    host = data.get("host_name", "Someone")
    vibes = data.get("vibes", [])
    attendees = data.get("attendees", [])
    state = data.get("state", {})
    composition = data.get("composition", "")
    vibe_log = state.get("vibe_log", [])

    lines = [f"🎉 **{host}** threw a party! Kleisli composition: `{composition}`"]
    lines.append(f"   Attendees: {', '.join(attendees) if attendees else 'just the host (sad)'}")
    lines.append("")

    for entry in vibe_log:
        lines.append(f"   {entry}")

    lines.append("")
    lines.append(f"   📊 Final state — Energy: {state.get('energy', 0)} | Chaos: {state.get('chaos', 0)} | Bonding: {state.get('bonding', 0)} | Fun: {state.get('fun', 0)}")

    return "\n".join(lines)


def _narrate_cook(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    ingredients = data.get("ingredients", [])
    results = data.get("results", [])
    side_effects = data.get("side_effects", [])

    lines = [f"🍳 **{name}** cooked! `fmap cook {ingredients}` → `{results}`"]
    if side_effects:
        lines.append(f"   ⚠️ Side effects: {'; '.join(side_effects)}")
    return "\n".join(lines)


def _narrate_prank_success(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    target = data.get("target_name", "someone")
    prank = data.get("prank", "did something")

    return f"😈 **{name}** {prank} on **{target}**. It worked perfectly. The building will remember this."


def _narrate_prank_fail(data: Dict, tick: int) -> str:
    name = data.get("agent_name", "Someone")
    target = data.get("target_name", "someone")
    prank = data.get("prank", "tried something")

    return f"😅 **{name}** tried to prank **{target}** but got caught mid-attempt. The awkward silence was deafening."


def _narrate_decree(data: Dict, tick: int) -> str:
    content = data.get("content", "")
    math_note = data.get("math_note", "")

    return f"📜 **LANDLORD DECREE:**\n\n> {content}\n\n   *[Math: {math_note}]*"


def _narrate_event(data: Dict, tick: int) -> str:
    name = data.get("name", "Something")
    desc = data.get("description", "happened")

    return f"⚡ **BUILDING EVENT — {name}:** {desc}"


def _narrate_gossip_auto(data: Dict, tick: int) -> str:
    from_name = data.get("from", "someone")
    to_name = data.get("to", "someone")
    content = data.get("new_content", "...")

    return f'🔗 The gossip spread naturally — from **{from_name}**\'s vicinity to **{to_name}**: *"{content}"*'


EVENT_NARRATORS = {
    "enter": _narrate_enter,
    "move": _narrate_move,
    "move_nothing": _narrate_move_nothing,
    "move_either": _narrate_move_either,
    "move_list": _narrate_move_list,
    "move_bottom": _narrate_move_bottom,
    "talk_private": _narrate_talk_private,
    "talk_room": _narrate_talk_room,
    "gossip_start": _narrate_gossip_start,
    "gossip_spread": _narrate_gossip_spread,
    "party": _narrate_party,
    "cook": _narrate_cook,
    "prank_success": _narrate_prank_success,
    "prank_fail": _narrate_prank_fail,
    "gossip_auto_spread": _narrate_gossip_auto,
}


def narrate_tick(events: List[Dict], tick: int, season: int, episode: int) -> str:
    """Produce a full narrated story for a tick."""
    lines = [f"═══ THE MONAD — Season {season}, Episode {episode}, Tick {tick} ═══\n"]

    # Group events by location
    narrated = []
    for event in events:
        text = narrate_event(event)
        if text:
            narrated.append(text)

    if not narrated:
        lines.append("*The building is quiet. Too quiet. Something is definitely about to happen.*")
    else:
        lines.extend(narrated)

    lines.append(f"\n{'─' * 50}")
    return "\n\n".join(lines)


def narrate_landlord_action(action: Dict) -> Optional[str]:
    """Narrate a landlord decree or event."""
    action_type = action.get("type")
    data = action.get("data", {})

    if action_type == "decree":
        return _narrate_decree(data, 0)
    elif action_type == "event":
        return _narrate_event(data, 0)
    return None
