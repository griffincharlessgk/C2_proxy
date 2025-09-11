async function j(u,o){const r=await fetch(u,o);if(!r.ok)throw new Error('http '+r.status);return r.json()}
function item(k,v){return `<div class="item"><div class="k">${k}</div><div class="v">${v}</div></div>`}
function esc(s){return (s||'').toString().replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]))}
async function refresh(){
  try{
    const s=await j('/api/status');
    document.getElementById('status').innerHTML = [
      item('Host', esc(s.host)),
      item('Ports', `bot:${s.ports.bot} • http:${s.ports.http} • socks:${s.ports.socks} • api:${s.ports.api}`),
      item('Bots', `${s.bot_count} (preferred: ${esc(s.preferred_bot||'-')})`),
      item('Active connections', s.active_connections)
    ].join('');
    const health = document.getElementById('health');
    health.textContent = s.bot_count>0? 'Healthy' : 'Degraded';
    health.className = 'status-pill ' + (s.bot_count>0? 'ok':'warn');

    const b=await j('/api/bots');
    document.getElementById('bots').innerHTML = b.bots.map(x=>
      `<div class="item">
        <div>${esc(x.bot_id)}</div>
        <div>
          <span class="badge">active:${x.active_requests}</span>
          <button class="btn" onclick="sel('${esc(x.bot_id)}')">Select</button>
        </div>
      </div>`
    ).join('') || '<div class="item"><div class="k">No bots connected</div></div>';

    const c=await j('/api/connections');
    document.getElementById('conns').innerHTML = c.connections.map(x=>
      `<div class="item"><div>${esc(x.request_id)}</div><div>${esc(x.target)} via ${esc(x.bot_id)}</div></div>`
    ).join('') || '<div class="item"><div class="k">No active connections</div></div>';
  }catch(e){
    console.error(e);
  }
}
async function sel(id){await fetch('/api/select_bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bot_id:id})});refresh()}
async function clearPref(){await fetch('/api/clear_preferred_bot',{method:'POST'});refresh()}

document.getElementById('clearPref').addEventListener('click', clearPref);
setInterval(refresh, 2000);
refresh();
