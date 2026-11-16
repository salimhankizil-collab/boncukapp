// Boncuk platformu: ortak yardımcılar (seslendirme, ses efektleri, konfeti, uygulama kurulumu)
(function () {
  const B = (window.Boncuk = {});

  B.RENKLER = [
    { anahtar: 'red', ad: 'Kırmızı', ing: 'Red', renk: '#ec3a3e' },
    { anahtar: 'orange', ad: 'Turuncu', ing: 'Orange', renk: '#ff8a1c' },
    { anahtar: 'yellow', ad: 'Sarı', ing: 'Yellow', renk: '#ffd014' },
    { anahtar: 'green', ad: 'Yeşil', ing: 'Green', renk: '#3abc52' },
    { anahtar: 'blue', ad: 'Mavi', ing: 'Blue', renk: '#2680f0' },
    { anahtar: 'purple', ad: 'Mor', ing: 'Purple', renk: '#964ed6' },
    { anahtar: 'pink', ad: 'Pembe', ing: 'Pink', renk: '#ff74b2' },
  ];

  B.karistir = (dizi) => {
    const a = dizi.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  };
  B.param = (ad) => new URLSearchParams(location.search).get(ad);
  B.bekle = (ms) => new Promise((r) => setTimeout(r, ms));

  // ---- seslendirme (tarayıcının kendi sesi, internet gerektirmez) ----
  let sesler = [];
  const sesleriYukle = () => { try { sesler = window.speechSynthesis ? speechSynthesis.getVoices() : []; } catch (e) { sesler = []; } };
  sesleriYukle();
  if (window.speechSynthesis) speechSynthesis.onvoiceschanged = sesleriYukle;
  const sesSec = (dil) => sesler.find((v) => v.lang && v.lang.toLowerCase().startsWith(dil)) || null;
  B.sessiz = false;
  // soyle() konuşma sonuna kadar bekler; B.sustur() ile kesilirse false döner (oyun sıradaki cümleye geçmesin diye).
  let nesil = 0;
  B.soyle = (metin, dil = 'tr') => new Promise((cozum) => {
    const benim = nesil;
    const bitti = () => cozum(benim === nesil);
    if (B.sessiz || !window.speechSynthesis) { setTimeout(bitti, 350 + metin.length * 45); return; }
    try {
      const u = new SpeechSynthesisUtterance(metin);
      u.lang = dil === 'en' ? 'en-US' : 'tr-TR';
      const v = sesSec(dil === 'en' ? 'en' : 'tr');
      if (v) u.voice = v;
      u.rate = dil === 'en' ? 0.85 : 0.95;
      u.pitch = 1.25;
      let tamam = false;
      const son = () => { if (!tamam) { tamam = true; bitti(); } };
      u.onend = son; u.onerror = son;
      setTimeout(son, 900 + metin.length * 110);
      speechSynthesis.speak(u);
    } catch (e) { bitti(); }
  });
  B.sustur = () => { nesil++; try { speechSynthesis.cancel(); } catch (e) { /* yok */ } };

  // ---- ses efektleri (WebAudio ile üretilir, dosya yok) ----
  let ctx = null;
  B.sesiAc = () => {
    try { ctx = ctx || new (window.AudioContext || window.webkitAudioContext)(); if (ctx.state === 'suspended') ctx.resume(); } catch (e) { ctx = null; }
  };
  const nota = (frek, sure, tip = 'sine', ses = 0.25, bas = 0, kayma = 0) => {
    if (!ctx || B.sessiz) return;
    const t = ctx.currentTime + bas;
    const o = ctx.createOscillator(); const g = ctx.createGain();
    o.type = tip; o.frequency.setValueAtTime(frek, t);
    if (kayma) o.frequency.exponentialRampToValueAtTime(Math.max(40, frek + kayma), t + sure);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(ses, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + sure);
    o.connect(g).connect(ctx.destination); o.start(t); o.stop(t + sure + 0.02);
  };
  B.efekt = {
    pop: () => nota(420, 0.14, 'sine', 0.3, 0, 1800),
    ding: () => { nota(1568, 0.7, 'sine', 0.18); nota(3136, 0.4, 'sine', 0.05); },
    boing: () => nota(180, 0.35, 'triangle', 0.3, 0, 140),
    hata: () => { nota(300, 0.18, 'square', 0.06); nota(220, 0.25, 'square', 0.06, 0.12); },
    tada: () => [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => nota(f, i === 3 ? 0.9 : 0.5, 'triangle', 0.18, i * 0.1)),
    dusus: () => nota(900, 0.8, 'sine', 0.15, 0, -650),
    tik: () => nota(1900, 0.06, 'sine', 0.2),
  };

  // ---- konfeti ----
  B.konfeti = (adet = 90) => {
    const k = document.createElement('div');
    k.setAttribute('aria-hidden', 'true');
    k.style.cssText = 'position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:50';
    document.body.append(k);
    for (let i = 0; i < adet; i++) {
      const p = document.createElement('i');
      const r = B.RENKLER[i % 7].renk;
      const x = Math.random() * 100, gec = Math.random() * 0.6, sure = 1.8 + Math.random() * 1.4, don = (Math.random() * 720 - 360) | 0;
      p.style.cssText = `position:absolute;left:${x}%;top:-20px;width:12px;height:7px;background:${r};border-radius:2px;`;
      p.animate([{ transform: 'translate(0,0) rotate(0)' }, { transform: `translate(${(Math.random() * 120 - 60) | 0}px, 110vh) rotate(${don}deg)` }],
        { duration: sure * 1000, delay: gec * 1000, easing: 'cubic-bezier(.3,.6,.5,1)', fill: 'forwards' });
      k.append(p);
    }
    setTimeout(() => k.remove(), 4200);
  };

  // ---- telefona yükleme (PWA) ----
  let kurulumOlayi = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault(); kurulumOlayi = e;
    document.querySelectorAll('[data-kur]').forEach((d) => { d.hidden = false; });
  });
  B.kur = async () => {
    if (kurulumOlayi) { kurulumOlayi.prompt(); await kurulumOlayi.userChoice; kurulumOlayi = null; return; }
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const kutu = document.getElementById('kur-yardim');
    if (kutu) {
      kutu.textContent = ios
        ? 'iPhone veya iPad: Safari\'de alttaki Paylaş düğmesine dokun, sonra "Ana Ekrana Ekle"yi seç.'
        : 'Tarayıcının menüsünü (⋮) aç ve "Uygulamayı yükle" veya "Ana ekrana ekle"yi seç.';
      kutu.hidden = false;
    }
  };
  document.addEventListener('click', (e) => { if (e.target.closest('[data-kur]')) B.kur(); });
  if (window.matchMedia('(display-mode: standalone)').matches) document.documentElement.classList.add('uygulama');

  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    window.addEventListener('load', () => navigator.serviceWorker.register(document.querySelector('meta[name="sw"]')?.content || 'sw.js').catch(() => {}));
  }
})();
