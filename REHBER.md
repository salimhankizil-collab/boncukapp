# Boncuk Çocuk TV: Kullanım Rehberi

## Adresler

| Ne | Adres |
|---|---|
| Çocuk platformu (oyunlar, videolar, uygulama) | https://salimhankizil-collab.github.io/boncukapp/ |
| Senin raporun (her gün 17:30'dan sonra güncellenir) | https://salimhankizil-collab.github.io/boncukapp/rapor/ |
| Yeni bölümleri indirme sayfası | https://github.com/salimhankizil-collab/boncukapp/releases |
| YouTube kanalı | https://www.youtube.com/@BoncukCocukTV |

## Her şey bulutta çalışır

Her gün 17:30'da GitHub kendisi çalışır. **Bilgisayarının ve Claude'un açık olması gerekmez.**
1. Yüklenmemiş bölüm 7'den azsa yeni videolar üretir.
2. YouTube istatistiklerini okur, raporu ve sitedeki video listesini günceller.
3. YouTube onayı geldikten sonra videoları kendisi yükleyip 18:00'e planlar.

## Senin işin

**YouTube onayı gelene kadar (haftada bir, ~10 dakika):**
1. Raporu aç. "Bugün yapman gerekenler" bölümü hangi bölümleri yükleyeceğini söyler.
2. Bölümleri indirme sayfasından indir.
3. YouTube Studio'dan yükle, `yukleme_bilgisi.txt` dosyasındaki başlık ve açıklamayı yapıştır, Kitle: **Evet, çocuklara özel**.
4. Her birini sırayla bir sonraki günün 18:00'ine planla. YouTube, bilgisayarın kapalıyken de yayınlar.

**YouTube onayı geldikten sonra:** Sadece raporu kontrol etmen yeterli.

## Sorun olursa

- Raporda "YouTube'a bağlanılamadı" yazıyorsa: bilgisayarda `YouTube_Baglan.bat` → izin ver → `Anahtarlari_GitHuba_Gonder.bat`.
- Elle çalıştırmak istersen: GitHub → Actions → "Günlük Boncuk işi" → **Run workflow**.

## Bilmen gerekenler

- Site ve rapor herkese açık adreslerde. Raporda gizli bilgi yok; abone ve izlenme sayıları zaten YouTube'da görünüyor.
- Gizli anahtarlar GitHub'ın şifreli "Secrets" bölümünde durur, kodun içinde yoktur.
- Sesler Microsoft Edge'in ücretsiz seslendirme servisiyle yapılıyor. Bu servisin resmi bir ticari lisansı yok; kanal büyüyünce lisanslı bir sese geçmek daha güvenli olur.
- Görseller: Microsoft Fluent Emoji (MIT). Yazı tipi: Baloo 2 (OFL). Müzik ve efektler her bölüm için sıfırdan üretilir.
