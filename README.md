# Boncuk Çocuk TV

2-6 yaş için reklamsız eğitici platform: YouTube kısa videoları, renk ve hayvan oyunları, telefona yüklenebilen uygulama.

- **Site:** https://salimhankizil-collab.github.io/boncukapp/
- **YouTube:** https://www.youtube.com/@BoncukCocukTV

## Nasıl çalışır

Her gün 17:30'da (Türkiye saati) GitHub Actions `uretim/gunluk.py` dosyasını çalıştırır:

1. Yüklenmemiş bölüm 7'den azsa yeni videolar üretir (`uretim/motor.py`, `uretim/uret.py`).
2. Otomatik yükleme açıksa (`veri/ayarlar.json` → `denetim_onayli: true`) sıradaki videoları yükleyip 18:00'e planlar (her zaman ~2 gün ileriye).
   Onaylı değilse yeni bölümleri indirilebilir bir GitHub Release olarak koyar.
3. Kanal istatistiklerini toplar, `site/rapor/` ve `site/veri/videolar.json` dosyalarını günceller.
4. Siteyi GitHub Pages'e yayınlar.

## Klasörler

| Klasör | İçerik |
|---|---|
| `site/` | Web sitesi ve oyunlar (PWA) |
| `uretim/` | Video motoru, günlük iş, YouTube bağlantısı |
| `veri/` | Bölüm kayıtları, istatistik geçmişi, ayarlar |
| `.github/workflows/` | Günlük bulut işi |

Gizli anahtarlar GitHub'da **Settings → Secrets → Actions** altında durur: `GOOGLE_CLIENT_SECRET`, `GOOGLE_TOKEN`.

## Lisanslar

Hayvan görselleri: [Microsoft Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (MIT). Yazı tipi: [Baloo 2](https://github.com/EkType/Baloo2) (SIL OFL). Boncuk karakteri, müzik ve ses efektleri bu projede üretilmiştir.
