#!/bin/bash
# Stop The Monad server

PIDFILE="monadologia.pid"

if [ ! -f "$PIDFILE" ]; then
    echo "⚠️  No PID file found. Server may not be running."
    echo "   Trying to find and kill uvicorn processes..."
    pkill -f "uvicorn server.main:app"
    exit 0
fi

PID=$(cat "$PIDFILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "🛑 Stopping server (PID: $PID)..."
    kill "$PID"
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Server stopped successfully"
            rm -f "$PIDFILE"
            exit 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "⚠️  Server didn't stop gracefully, forcing..."
    kill -9 "$PID" 2>/dev/null
    rm -f "$PIDFILE"
    echo "✅ Server killed"
else
    echo "⚠️  Server (PID: $PID) is not running"
    rm -f "$PIDFILE"
fi
