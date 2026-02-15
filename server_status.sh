#!/bin/bash
# Check The Monad server status

PIDFILE="monadologia.pid"
LOGFILE="monadologia.log"
PORT=${PORT:-3335}

echo "📊 The Monad Server Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Status: RUNNING"
        echo "   PID: $PID"
        echo "   Port: $PORT"
        echo "   Uptime: $(ps -o etime= -p $PID | tr -d ' ')"
        echo ""
        echo "📡 Endpoints:"
        echo "   http://localhost:$PORT/"
        echo "   http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT/"
        echo ""
        echo "📜 Recent logs (last 10 lines):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        tail -n 10 "$LOGFILE" 2>/dev/null || echo "   No logs available"
    else
        echo "❌ Status: NOT RUNNING (stale PID file)"
        echo "   Run ./start_server.sh to start"
    fi
else
    echo "❌ Status: NOT RUNNING"
    echo "   Run ./start_server.sh to start"
fi

echo ""
echo "Commands:"
echo "  ./start_server.sh   - Start server"
echo "  ./stop_server.sh    - Stop server"
echo "  ./restart_server.sh - Restart server"
echo "  tail -f $LOGFILE    - Follow logs"
