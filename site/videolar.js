// YouTube'da yayınlanan videoları listeler (veri/videolar.json her gün buluttan güncellenir)
(function () {
  const TUR = {
    toplar: { ad: 'Renkli toplar', oyun: 'oyunlar/toplar.html' },
    kule: { ad: 'Renkli kule', oyun: 'oyunlar/kule.html' },
    golge: { ad: 'Gölge bilmecesi', oyun: 'oyunlar/golge.html' },
  };
  const temizBaslik = (b) => String(b || '').replace(/\s*\|\s*Boncuk.*$/i, '').replace(/#\S+/g, '').trim();
  const tarih = (t) => { try { return new Date(t.replace(' ', 'T') + ':00+03:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' }); } catch (e) { return ''; } };

  function kart(v) {
    const tur = TUR[v.tur] || TUR.toplar;
    const k = document.createElement('article');
    k.className = 'kart video';
    const a = document.createElement('a');
    a.href = `https://www.youtube.com/shorts/${v.id}`; a.target = '_blank'; a.rel = 'noopener';
    a.setAttribute('aria-label', 'Videoyu YouTube\'da izle');
    const img = document.createElement('img');
    img.className = 'kapak'; img.loading = 'lazy'; img.alt = '';
    img.src = `https://i.ytimg.com/vi/${v.id}/hqdefault.jpg`;
    a.append(img);
    const ic = document.createElement('div'); ic.className = 'ic';
    const et = document.createElement('span'); et.className = 'etiket'; et.textContent = `${tur.ad}${v.bolum ? ' · Bölüm ' + v.bolum : ''}`;
    const h = document.createElement('h3'); h.textContent = temizBaslik(v.baslik);
    const t = document.createElement('span'); t.className = 'soluk'; t.textContent = tarih(v.tarih);
    const ey = document.createElement('div'); ey.className = 'eylem';
    const izle = document.createElement('a'); izle.className = 'dugme'; izle.href = a.href; izle.target = '_blank'; izle.rel = 'noopener'; izle.textContent = '▶ İzle';
    const oyna = document.createElement('a'); oyna.className = 'dugme turuncu'; oyna.href = (window.KOK || '') + (v.oyun || tur.oyun); oyna.textContent = 'Bu videonun oyunu';
    ey.append(izle, oyna);
    ic.append(et, h, t, ey);
    k.append(a, ic);
    return k;
  }

  window.videolariGoster = async (kutu, adet) => {
    try {
      const r = await fetch((window.KOK || '') + 'veri/videolar.json', { cache: 'no-cache' });
      const liste = await r.json();
      kutu.replaceChildren(...(adet ? liste.slice(0, adet) : liste).map(kart));
      if (!liste.length) kutu.textContent = 'Yakında ilk videolar burada!';
    } catch (e) {
      kutu.textContent = 'Videolar şu an yüklenemedi. İnternet bağlantını kontrol et.';
    }
  };
})();
