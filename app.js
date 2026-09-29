let sectionCache=[]; let riskChart,trendChart;

function pct(x){return (Number(x||0)*100).toFixed(1)+"%"}
function riskClass(r){return `<span class="pill ${r}">${r}</span>`}

async function loadDashboard(){
 const res=await fetch('/api/sections'); const data=await res.json(); sectionCache=data.sections;
 document.getElementById('total').textContent=sectionCache.length;
 document.getElementById('low').textContent=data.counts.LOW;
 document.getElementById('medium').textContent=data.counts.MEDIUM;
 document.getElementById('danger').textContent=data.counts.HIGH+data.counts.CRITICAL;
 renderRows(sectionCache);
 const ctx=document.getElementById('riskChart');
 riskChart=new Chart(ctx,{type:'doughnut',data:{labels:['LOW','MEDIUM','HIGH','CRITICAL'],datasets:[{data:[data.counts.LOW,data.counts.MEDIUM,data.counts.HIGH,data.counts.CRITICAL]}]},options:{plugins:{legend:{labels:{color:'#cbd7dc'}}}}});
 const trend = sectionCache.slice(0,12).map(x=>Number(x.probability||0)*100);
 trendChart=new Chart(document.getElementById('trendChart'),{type:'bar',data:{labels:trend.map((_,i)=>i+1),datasets:[{label:'Failure probability %',data:trend}]},options:{scales:{x:{ticks:{color:'#8399a5'}},y:{ticks:{color:'#8399a5'},beginAtZero:true,max:100}}}});
}
function renderRows(rows){
 document.getElementById('rows').innerHTML=rows.map(x=>`<tr>
 <td class="section">${x.section_id}</td><td>${x.location}</td>
 <td>${x.probability==null?'—':x.vibration??'—'} mm/s</td>
 <td>${x.acceleration??'—'} g</td><td>${x.temperature??'—'}°</td><td>${x.deformation??'—'} mm</td>
 <td class="prob">${pct(x.probability)}<span class="meter"><i style="width:${Math.min(100,(x.probability||0)*100)}%"></i></span></td>
 <td>${riskClass(x.risk||'LOW')}</td></tr>`).join('');
}
function filterRows(){const q=document.getElementById('search').value.toLowerCase();renderRows(sectionCache.filter(x=>(x.section_id+x.location).toLowerCase().includes(q)))}

async function simulate(id,severity){
 const r=await fetch('/api/simulate/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({severity})});
 const d=await r.json(); alert(`${d.section_id}\nFailure probability: ${pct(d.probability)}\nRisk: ${d.risk}\n\n${d.action}`);
 if(location.pathname==='/') loadDashboard(); else if(location.pathname==='/alerts') loadAlerts();
}
async function loadAlerts(){
 const d=await (await fetch('/api/alerts')).json();
 document.getElementById('alertRows').innerHTML=d.alerts.length?d.alerts.map(a=>`<tr><td>${a.id}</td><td class="section">${a.section_id}</td><td>${new Date(a.timestamp).toLocaleString()}</td><td>${pct(a.probability)}</td><td>${riskClass(a.risk)}</td><td>${a.status}</td><td>${a.recommended_action}</td></tr>`).join(''):`<tr><td colspan="7" style="text-align:center;padding:70px">No early warning alerts yet.</td></tr>`;
}
async function loadMap(){
 const d=await (await fetch('/api/sections')).json();
 const map=L.map('map').setView([11.1,78.2],7);
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
 d.sections.forEach(x=>{const c=x.risk==='CRITICAL'||x.risk==='HIGH'?'#ff5c67':x.risk==='MEDIUM'?'#f3b43b':'#48d2c2';
 const m=L.circleMarker([x.latitude,x.longitude],{radius:9,color:c,fillColor:c,fillOpacity:.8}).addTo(map);
 m.bindPopup(`<b>${x.section_id}</b><br>${x.location}<br>Risk: ${x.risk}<br>Probability: ${pct(x.probability)}`).on('click',()=>loadSectionDetail(x.section_id));});
}
async function loadSectionDetail(id){
 const d=await (await fetch('/api/section/'+id)).json(); const el=document.getElementById('detail'); el.classList.remove('hidden');
 const p=d.predictions.at(-1); el.innerHTML=`<h2>${d.track.section_id} — ${d.track.location}</h2><p>Failure probability: <b>${pct(p?.probability)}</b> · ${riskClass(p?.risk||'LOW')} · Health: ${(p?.health_score??0).toFixed(1)}/100</p><p>Latest readings are available through the API and stored in the persistent database.</p>`;
}
async function loadModel(){
 const res=await fetch('/api/metrics');
 const d=await res.json();
 if (d.error) {
  document.getElementById('metricCards').innerHTML=`<div class="card"><small>STATUS</small><strong class="metric">${d.error}</strong></div>`;
  document.getElementById('config').textContent='Run the training script first: python train_model.py';
  return;
 }
 const cards=[['Accuracy',d.accuracy],['Precision',d.precision],['Recall',d.recall],['F1',d.f1],['ROC-AUC',d.roc_auc]];
 document.getElementById('metricCards').innerHTML=cards.map(x=>`<div class="card"><small>${x[0].toUpperCase()}</small><strong class="metric">${Number.isFinite(x[1]) ? (x[1]*100).toFixed(2)+'%' : 'N/A'}</strong></div>`).join('');
 const h=d.history||{loss:[],val_loss:[],accuracy:[],val_accuracy:[]};
 new Chart(document.getElementById('lossChart'),{type:'line',data:{labels:(h.loss||[]).map((_,i)=>i+1),datasets:[{label:'Training loss',data:h.loss||[]},{label:'Validation loss',data:h.val_loss||[]}]},options:{scales:{x:{ticks:{color:'#8399a5'}},y:{ticks:{color:'#8399a5'}}}}});
 new Chart(document.getElementById('accChart'),{type:'line',data:{labels:(h.accuracy||[]).map((_,i)=>i+1),datasets:[{label:'Training accuracy',data:h.accuracy||[]},{label:'Validation accuracy',data:h.val_accuracy||[]}]},options:{scales:{x:{ticks:{color:'#8399a5'}},y:{ticks:{color:'#8399a5'},min:0,max:1}}}});
 document.getElementById('config').textContent=JSON.stringify({sequence_length:d.sequence_length,features:d.features},null,2);
}
