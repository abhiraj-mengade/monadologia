#!/bin/bash
# Update The Monad server from git and restart

echo "🔄 Updating The Monad server..."
echo ""

# Check if git repo
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Cannot update."
    exit 1
fi

# Check if server is running
PIDFILE="monadologia.pid"
WAS_RUNNING=false

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        WAS_RUNNING=true
        echo "🛑 Stopping running server..."
        ./stop_server.sh
        sleep 2
    fi
fi

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Check your connection and try again."
    exit 1
fi

echo ""
echo "✅ Code updated successfully"
echo ""

# Check if requirements changed
if git diff HEAD@{1}..HEAD --name-only | grep -q "requirements.txt"; then
    echo "📦 Requirements.txt changed, reinstalling dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    echo "✅ Dependencies updated"
    echo ""
fi

# Restart server if it was running
if [ "$WAS_RUNNING" = true ]; then
    echo "🚀 Restarting server..."
    ./start_server.sh
else
    echo "ℹ️  Server was not running. Use ./start_server.sh to start it."
fi

echo ""
echo "✅ Update complete!"
