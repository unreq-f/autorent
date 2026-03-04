/* ===== catalog.html ===== */

function openModal(name, price) {
  var m = document.getElementById('modalCarName');
  var p = document.getElementById('modalPrice');
  var b = document.getElementById('bookModal');
  if (m) m.textContent = name;
  if (p) p.textContent = price + ' USD / доба';
  if (b) b.classList.add('open');
}
function closeModal() {
  var b = document.getElementById('bookModal');
  if (b) b.classList.remove('open');
}
var _bookModal = document.getElementById('bookModal');
if (_bookModal) {
  _bookModal.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });
}


/* ===== car-detail.html ===== */

var prices = {
  base:{p1:200,p2:180,p3:160,p4:140,deposit:'2 500 USD'},
  prime:{p1:260,p2:234,p3:208,p4:182,deposit:'0 USD'}
};
var currentTariff = 'base';
function setTariff(t, btn) {
  currentTariff = t;
  document.querySelectorAll('.tariff-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  var p = prices[t];
  ['p1','p2','p3','p4'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.textContent = p[id] + ' USD/доба';
  });
  var dep = document.getElementById('deposit');
  if (dep) dep.textContent = p.deposit;
  calcTotal();
}
function calcTotal() {
  var fEl = document.getElementById('dateFrom');
  var tEl = document.getElementById('dateTo');
  if (!fEl || !tEl) return;
  var f = fEl.value, t = tEl.value;
  if (!f || !t) return;
  var days = Math.ceil((new Date(t) - new Date(f)) / 86400000);
  if (days <= 0) return;
  var p = prices[currentTariff];
  var rate = days >= 29 ? p.p4 : days >= 8 ? p.p3 : days >= 3 ? p.p2 : p.p1;
  var lbl = document.getElementById('totalLabel');
  var val = document.getElementById('totalVal');
  if (lbl) lbl.textContent = days + ' діб × ' + rate + ' USD';
  if (val) val.textContent = (days * rate) + ' USD';
}
document.querySelectorAll('.thumb').forEach(function(t) {
  t.onclick = function() {
    document.querySelectorAll('.thumb').forEach(function(x) { x.classList.remove('active'); });
    this.classList.add('active');
  };
});


/* ===== auth.html ===== */

function switchTab(id, btn) {
  document.querySelectorAll('.auth-form').forEach(function(f) { f.classList.remove('active'); });
  document.querySelectorAll('.toggle-btn').forEach(function(b) { b.classList.remove('active'); });
  var form = document.getElementById('form-' + id);
  if (form) form.classList.add('active');
  btn.classList.add('active');
}
function switchTabByName(id) {
  var btns = document.querySelectorAll('.toggle-btn');
  var idx = id === 'login' ? 0 : 1;
  if (btns[idx]) switchTab(id, btns[idx]);
}
function togglePass(id, btn) {
  var inp = document.getElementById(id);
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}
function checkStrength(val) {
  var fill  = document.getElementById('strengthFill');
  var label = document.getElementById('strengthLabel');
  if (!fill || !label) return;
  var score = 0;
  if (val.length >= 8) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  var levels = [
    {w:'0%', c:'transparent', t:''},
    {w:'25%', c:'#cf6679', t:'Слабкий'},
    {w:'50%', c:'#e0924c', t:'Середній'},
    {w:'75%', c:'#c9a84c', t:'Добрий'},
    {w:'100%', c:'#4caf7d', t:'Надійний'}
  ];
  var l = levels[score];
  fill.style.width = l.w; fill.style.background = l.c;
  label.textContent = l.t; label.style.color = l.c;
}


/* ===== order.html ===== */

function selectPay(el) {
  document.querySelectorAll('.pay-option').forEach(function(p) { p.classList.remove('selected'); });
  el.classList.add('selected');
}