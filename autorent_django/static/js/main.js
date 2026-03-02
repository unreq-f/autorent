
/* ===== catalog.html ===== */

function openModal(name, price) {
  document.getElementById('modalCarName').textContent = name;
  document.getElementById('modalPrice').textContent = price + ' USD / доба';
  document.getElementById('bookModal').classList.add('open');
}
function closeModal() {
  document.getElementById('bookModal').classList.remove('open');
}
document.getElementById('bookModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});


/* ===== car-detail.html ===== */

const prices = {
  base:{p1:200,p2:180,p3:160,p4:140,deposit:'2 500 USD'},
  prime:{p1:260,p2:234,p3:208,p4:182,deposit:'0 USD'}
};
let currentTariff='base';
function setTariff(t,btn){
  currentTariff=t;
  document.querySelectorAll('.tariff-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const p=prices[t];
  document.getElementById('p1').textContent=p.p1+' USD/доба';
  document.getElementById('p2').textContent=p.p2+' USD/доба';
  document.getElementById('p3').textContent=p.p3+' USD/доба';
  document.getElementById('p4').textContent=p.p4+' USD/доба';
  document.getElementById('deposit').textContent=p.deposit;
  calcTotal();
}
function calcTotal(){
  const f=document.getElementById('dateFrom').value;
  const t=document.getElementById('dateTo').value;
  if(!f||!t)return;
  const days=Math.ceil((new Date(t)-new Date(f))/(1000*60*60*24));
  if(days<=0)return;
  const p=prices[currentTariff];
  let rate=days>=29?p.p4:days>=8?p.p3:days>=3?p.p2:p.p1;
  document.getElementById('totalLabel').textContent=days+' діб × '+rate+' USD';
  document.getElementById('totalVal').textContent=(days*rate)+' USD';
}
document.querySelectorAll('.thumb').forEach(t=>{
  t.onclick=function(){document.querySelectorAll('.thumb').forEach(x=>x.classList.remove('active'));this.classList.add('active');}
});


/* ===== auth.html ===== */

function switchTab(id, btn){
  document.querySelectorAll('.auth-form').forEach(f=>f.classList.remove('active'));
  document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('form-'+id).classList.add('active');
  btn.classList.add('active');
}
function switchTabByName(id){
  const btns = document.querySelectorAll('.toggle-btn');
  const idx = id==='login'?0:1;
  switchTab(id, btns[idx]);
}
function togglePass(id, btn){
  const inp = document.getElementById(id);
  inp.type = inp.type==='password'?'text':'password';
  btn.textContent = inp.type==='password'?'👁':'🙈';
}
function checkStrength(val){
  const fill = document.getElementById('strengthFill');
  const label = document.getElementById('strengthLabel');
  let score = 0;
  if(val.length>=8) score++;
  if(/[A-Z]/.test(val)) score++;
  if(/[0-9]/.test(val)) score++;
  if(/[^A-Za-z0-9]/.test(val)) score++;
  const levels=[{w:'0%',c:'transparent',t:''},{w:'25%',c:'#cf6679',t:'Слабкий'},{w:'50%',c:'#e0924c',t:'Середній'},{w:'75%',c:'#c9a84c',t:'Добрий'},{w:'100%',c:'#4caf7d',t:'Надійний'}];
  const l=levels[score];
  fill.style.width=l.w; fill.style.background=l.c;
  label.textContent=l.t; label.style.color=l.c;
}


/* ===== order.html ===== */

function selectPay(el){
  document.querySelectorAll('.pay-option').forEach(p=>p.classList.remove('selected'));
  el.classList.add('selected');
}

