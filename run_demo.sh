#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 🎭 MONADOLOGIA — Demo Runner
# Where Mathematical Abstraction Meets Chaotic Social Simulation
#
# This script starts the server and spawns autonomous agents.
# Agents use the API to discover the world and act on their own.
# ═══════════════════════════════════════════════════════════

set -e

cd "$(dirname "$0")"

echo "🎭 ═══════════════════════════════════════════"
echo "   THE MONAD — Starting Up"
echo "   Autonomous Agent Apartment Building"
echo "═══════════════════════════════════════════════"
echo ""

# ─── Check dependencies ───
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    python3 -m pip install -r requirements.txt
fi

# ─── Kill any existing server on port 8000 ───
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# ─── Start the server ───
echo "🏠 Starting The Monad server..."
TICK_INTERVAL=15 python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 3

# ─── Verify server is running ───
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "✅ Server running at http://localhost:8000"
echo "📊 Dashboard at http://localhost:8000/dashboard"
echo ""

# ─── Spawn 3 autonomous agents ───
echo "🤖 Spawning autonomous agents..."
echo ""

python3 -m server.demo_agents.autonomous_agent \
    --name "Marina" --personality social_butterfly --interval 4 &
AGENT1_PID=$!
echo "   🦋 Marina (social_butterfly) — PID $AGENT1_PID"

sleep 1

python3 -m server.demo_agents.autonomous_agent \
    --name "Viktor" --personality schemer --interval 5 &
AGENT2_PID=$!
echo "   🕵️ Viktor (schemer) — PID $AGENT2_PID"

sleep 1

python3 -m server.demo_agents.autonomous_agent \
    --name "Gremothy" --personality chaos_gremlin --interval 3 &
AGENT3_PID=$!
echo "   👹 Gremothy (chaos_gremlin) — PID $AGENT3_PID"

echo ""
echo "═══════════════════════════════════════════════"
echo "🎬 THE MONAD IS LIVE"
echo ""
echo "   Server:    http://localhost:8000"
echo "   Dashboard: http://localhost:8000/dashboard"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "   Try these in your browser/curl:"
echo "     GET  /              — Agent discovery & onboarding"
echo "     GET  /world-rules   — Full world rules (LLM system prompt)"
echo "     GET  /actions       — Action catalog"
echo "     GET  /building      — Live building state"
echo "     GET  /stories       — Narrated story feed"
echo "     GET  /gossip        — Active gossip chains"
echo "     GET  /math          — The mathematical structure revealed"
echo ""
echo "   To connect your OWN agent:"
echo "     1. POST /register {name, personality} → get token"
echo "     2. POST /act {action, params} with Bearer token"
echo ""
echo "   Press Ctrl+C to stop everything"
echo "═══════════════════════════════════════════════"
echo ""

# ─── Wait & cleanup on exit ───
cleanup() {
    echo ""
    echo "🛑 Shutting down The Monad..."
    kill $AGENT1_PID $AGENT2_PID $AGENT3_PID $SERVER_PID 2>/dev/null
    wait $AGENT1_PID $AGENT2_PID $AGENT3_PID $SERVER_PID 2>/dev/null
    echo "   The building sleeps. But the monad remembers."
}

trap cleanup EXIT

# Wait for all agents
wait $AGENT1_PID $AGENT2_PID $AGENT3_PID
