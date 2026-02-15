#!/bin/bash
# Start The Monad server for VPS deployment

# Default port (can be overridden with PORT env var)
# Port 3335 is configured for Oracle VPS
PORT=${PORT:-3335}
HOST=${HOST:-0.0.0.0}
LOGFILE="monadologia.log"
PIDFILE="monadologia.pid"

# Check if server is already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Server is already running (PID: $PID)"
        echo "   Use ./stop_server.sh to stop it first"
        exit 1
    else
        echo "🧹 Cleaning up stale PID file..."
        rm -f "$PIDFILE"
    fi
fi

echo "🚀 Starting The Monad server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Access: http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT"
echo "   Logs: $LOGFILE"
echo ""

# Activate or create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment (first time)..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt --quiet
    echo "✅ Setup complete!"
else
    echo "✅ Virtual environment found, activating..."
    source venv/bin/activate
    # Quick check if key packages exist (skip if they do)
    if python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
        echo "✅ Dependencies already installed"
    else
        echo "⚠️  Some packages missing, installing..."
        pip install -r requirements.txt --quiet
    fi
fi

# Start the server in background
echo "🚀 Starting server in background..."
nohup uvicorn server.main:app --host "$HOST" --port "$PORT" > "$LOGFILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > "$PIDFILE"

# Wait a moment and check if it started successfully
sleep 2
if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo "✅ Server started successfully!"
    echo "   PID: $SERVER_PID"
    echo "   View logs: tail -f $LOGFILE"
    echo "   Stop server: ./stop_server.sh"
else
    echo "❌ Server failed to start. Check $LOGFILE for errors."
    rm -f "$PIDFILE"
    exit 1
fi
