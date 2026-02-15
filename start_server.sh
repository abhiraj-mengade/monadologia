#!/bin/bash
# Start The Monad server for VPS deployment

# Default port (can be overridden with PORT env var)
# Port 3335 is configured for Oracle VPS
PORT=${PORT:-3335}
HOST=${HOST:-0.0.0.0}

echo "🚀 Starting The Monad server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Access: http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
    # Check if dependencies are installed
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
    fi
fi

# Start the server
uvicorn server.main:app --host "$HOST" --port "$PORT"
