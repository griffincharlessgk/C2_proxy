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
        <td><button class='btn' onclick=\"sel('${x.bot_id}')\">Chọn làm exit</button></td>
      </tr>`;
    }).join('');
    document.getElementById('bots').innerHTML = `
      <div class='row'>
        <h2 style='margin-right:auto'>Bots</h2>
        <button class='btn' onclick='clearPref()'>Bỏ ưu tiên</button>
      </div>
      <table>
        <thead><tr><th>Bot ID</th><th>Active</th><th>Connections</th><th>Action</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='4' class='muted'>Chưa có bot</td></tr>"}</tbody>
      </table>`

    const c=await j('/api/connections');
    const rowsC=(c.connections||[]).map(x=>`<tr>
        <td class='muted'>${x.request_id}</td>
        <td>${x.target}</td>
        <td>${x.bot_id}</td>
        <td class='muted'>${x.client||''}</td>
      </tr>`).join('');
    document.getElementById('conns').innerHTML = `
      <h2>Kết nối đang hoạt động</h2>
      <table>
        <thead><tr><th>Request ID</th><th>Target</th><th>Bot</th><th>Client</th></tr></thead>
        <tbody>${rowsC || "<tr><td colspan='4' class='muted'>Không có kết nối</td></tr>"}</tbody>
      </table>`
  }catch(e){
    document.getElementById('status').innerHTML = `<span class='muted'>Lỗi tải dữ liệu</span>`
    console.warn(e)
  }
}

async function sel(id){
  await fetch('/api/select_bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bot_id:id})});
  refresh()
}

async function clearPref(){
  await fetch('/api/clear_preferred_bot',{method:'POST'});
  refresh()
}

// Auto refresh every 2 seconds
setInterval(refresh,2000);
window.addEventListener('load',refresh);
