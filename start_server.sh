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
        echo "✅ Dependencies already installed, starting server..."
    else
        echo "⚠️  Some packages missing, installing..."
        pip install -r requirements.txt --quiet
    fi
fi

# Start the server
uvicorn server.main:app --host "$HOST" --port "$PORT"
