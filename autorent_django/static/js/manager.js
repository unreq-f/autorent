
/* ===== manager-dashboard.html ===== */

// Calendar strip
const cal = document.getElementById('calStrip');
const days = ['Нд','Пн','Вт','Ср','Чт','Пт','Сб'];
const busy = [3,7,8,14,15,20,21,22];
const partial = [5,6,10,11,16,17,23,24];
for(let i=1;i<=28;i++){
  const d=document.createElement('div');
  d.className='cal-day'+(i===26?' today':'')+(busy.includes(i)?' busy':partial.includes(i)?' partial':'');
  const dt=new Date(2025,1,i);
  d.innerHTML=`<div class="cal-wd">${days[dt.getDay()]}</div><div class="cal-d">${i}</div><div class="cal-cnt">${busy.includes(i)?'12':partial.includes(i)?Math.floor(Math.random()*6+4):'0'}</div>`;
  cal.appendChild(d);
}
// Chart
const chart=document.getElementById('chartBars');
const weeks=[['1–7 лют',2800],['8–14 лют',3400],['15–21 лют',3100],['22–28 лют',4980]];
const max=5000;
weeks.forEach(([l,v])=>{
  const w=document.createElement('div');w.className='bar-wrap';
  const h=Math.round(v/max*90);
  w.innerHTML=`<div class="bar" style="height:${h}px"></div><div class="bar-label">${l}</div>`;
  chart.appendChild(w);
});


/* ===== manager-cars.html ===== */

function setView(v){
  if(v==='grid'){
    document.getElementById('gridView').style.display='grid';
    document.getElementById('listView').style.display='none';
    document.getElementById('gridBtn').classList.add('active');
    document.getElementById('listBtn').classList.remove('active');
  } else {
    document.getElementById('gridView').style.display='none';
    document.getElementById('listView').style.display='block';
    document.getElementById('gridBtn').classList.remove('active');
    document.getElementById('listBtn').classList.add('active');
  }
}
function openDrawer(){document.getElementById('carDrawer').classList.add('open');}
function closeDrawer(){document.getElementById('carDrawer').classList.remove('open');}
document.getElementById('carDrawer').addEventListener('click',function(e){if(e.target===this)closeDrawer();});


/* ===== manager-payments.html ===== */

const statusMap={
  success:'<span class="pay-pill pp-success" style="font-size:12px;padding:5px 14px;">Успішно</span>',
  pending:'<span class="pay-pill pp-pending" style="font-size:12px;padding:5px 14px;">Очікує</span>',
  failed:'<span class="pay-pill pp-failed" style="font-size:12px;padding:5px 14px;">Відхилено</span>',
  refund:'<span class="pay-pill pp-refund" style="font-size:12px;padding:5px 14px;">Повернення</span>',
  deposit:'<span class="pay-pill pp-deposit" style="font-size:12px;padding:5px 14px;">Застава</span>'
};
function openDrawer(id,client,order,amt,status,type){
  document.getElementById('drTxId').textContent=id;
  document.getElementById('drClient').textContent=client;
  document.getElementById('drOrder').textContent=order;
  document.getElementById('drAmt').textContent=amt+' USD';
  document.getElementById('drType').innerHTML=type+' · '+statusMap[status];
  document.getElementById('drStatus').innerHTML=statusMap[status];
  document.getElementById('txDrawer').classList.add('open');
}
function closeDrawer(){document.getElementById('txDrawer').classList.remove('open');}
document.getElementById('txDrawer').addEventListener('click',function(e){if(e.target===this)closeDrawer();});

// Mini chart
const mc=document.getElementById('miniChart');
const wData=[2800,3400,3100,4980];
const mMax=Math.max(...wData);
wData.forEach((v,i)=>{
  const w=document.createElement('div');w.className='mini-bar';
  w.style.height=(v/mMax*56)+'px';
  w.innerHTML=`<span class="mini-bar-label">Т${i+1}</span>`;
  mc.appendChild(w);
});

document.querySelectorAll('.stab').forEach(t=>{
  t.onclick=function(){document.querySelectorAll('.stab').forEach(s=>s.classList.remove('active'));this.classList.add('active');}
});


/* ===== manager-fines.html ===== */

const statusLabels={unpaid:'Непогашений',paid:'Сплачений',partial:'Часткова оплата',disputed:'Оскаржується',waived:'Скасований'};
const sevLabels={high:'Критична',med:'Середня',low:'Мінімальна'};
function openDrawer(){
  document.getElementById('drTitle').innerHTML='Новий <em>штраф</em>';
  document.getElementById('drFineId').textContent='';
  document.getElementById('fineAmtCard').style.display='none';
  document.getElementById('drFineClient').textContent='—';
  document.getElementById('drFineCar').textContent='—';
  document.getElementById('drFineReason').textContent='—';
  document.getElementById('fineAmtInput').value='';
  document.getElementById('fineDrawer').classList.add('open');
}
function openFineDrawer(id,client,car,reason,amt,status,sev){
  document.getElementById('drTitle').innerHTML='Штраф <em>'+id+'</em>';
  document.getElementById('fineAmtCard').style.display='block';
  document.getElementById('drFineAmt').textContent=amt+' USD';
  document.getElementById('drFineStatus').textContent=statusLabels[status]+' · '+sevLabels[sev];
  document.getElementById('drFineClient').textContent=client;
  document.getElementById('drFineCar').textContent=car;
  document.getElementById('drFineReason').textContent=reason;
  document.getElementById('fineStatusSel').value=status;
  document.getElementById('fineAmtInput').value=amt;
  document.getElementById('fineDrawer').classList.add('open');
}
function closeDrawer(){document.getElementById('fineDrawer').classList.remove('open');}
document.getElementById('fineDrawer').addEventListener('click',function(e){if(e.target===this)closeDrawer();});
document.querySelectorAll('.stab').forEach(t=>{
  t.onclick=function(){document.querySelectorAll('.stab').forEach(s=>s.classList.remove('active'));this.classList.add('active');}
});


/* ===== manager-reports.html ===== */

// REVENUE CHART
const revData=[
  {label:'Т1 (1-7 лют)',val:2800,prev:2400},
  {label:'Т2 (8-14)',val:3400,prev:2900},
  {label:'Т3 (15-21)',val:3100,prev:3200},
  {label:'Т4 (22-28)',val:4980,prev:4250},
];
const maxRev=5000;
function buildBarChart(id,data,maxVal,comparePrev=false){
  const c=document.getElementById(id);
  if(!c)return;
  c.innerHTML='';
  data.forEach(d=>{
    const col=document.createElement('div');col.className='bc-col';
    if(comparePrev){
      const prevH=Math.round(d.prev/maxVal*140)+'px';
      const bar2=document.createElement('div');
      bar2.className='bc-bar compare';bar2.style.height=prevH;bar2.dataset.val=d.prev;
      col.appendChild(bar2);
    }
    const h=Math.round(d.val/maxVal*140)+'px';
    const bar=document.createElement('div');
    bar.className='bc-bar';bar.style.height=h;bar.dataset.val=d.val;
    const lbl=document.createElement('span');lbl.className='bc-label';lbl.textContent=d.label;
    bar.appendChild(lbl);
    col.appendChild(bar);
    c.appendChild(col);
  });
}
buildBarChart('revenueChart',revData,maxRev,true);

// BOOKINGS CHART  
const bookData=[
  {label:'Т1',val:14},{label:'Т2',val:18},{label:'Т3',val:16},{label:'Т4',val:14},
];
buildBarChart('bookingsChart',bookData,20);

// CLIENTS CHART
const cliData=[
  {label:'Жов',val:420},{label:'Лис',val:380},{label:'Гру',val:510},{label:'Січ',val:460},{label:'Лют',val:520},
];
buildBarChart('clientsChart',cliData,600);

function setReport(name,btn){
  document.querySelectorAll('.rtab').forEach(t=>t.classList.remove('active'));
  btn.classList.add('active');
  ['revenue','bookings','fleet','clients'].forEach(p=>{
    document.getElementById('panel-'+p).style.display=p===name?'block':'none';
  });
  if(name==='bookings') setTimeout(()=>buildBarChart('bookingsChart',bookData,20),50);
  if(name==='clients') setTimeout(()=>buildBarChart('clientsChart',cliData,600),50);
}
function setPeriod(btn){
  document.querySelectorAll('.period-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
}

