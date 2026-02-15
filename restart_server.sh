#!/bin/bash
# Restart The Monad server

echo "🔄 Restarting The Monad server..."
echo ""

# Stop if running
./stop_server.sh

# Wait a moment
sleep 2

# Start again
./start_server.sh
