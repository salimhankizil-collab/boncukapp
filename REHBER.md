# Boncuk Çocuk TV: Kullanım Rehberi

## Adresler

| Ne | Adres |
|---|---|
| Çocuk platformu (oyunlar, videolar, uygulama) | https://salimhankizil-collab.github.io/boncukapp/ |
| Senin raporun (her gün 17:30'dan sonra güncellenir) | https://salimhankizil-collab.github.io/boncukapp/rapor/ |
| Yeni bölümleri indirme sayfası | https://github.com/salimhankizil-collab/boncukapp/releases |
| YouTube kanalı | https://www.youtube.com/@BoncukCocukTV |

## Her şey bulutta çalışır

Her gün akşam GitHub kendisi çalışır. **Bilgisayarının ve Claude'un açık olması gerekmez.**
1. Yüklenmemiş bölüm 7'den azsa yeni videolar üretir (her iki videodan biri Boncuk, Pamuk ve Minik hikâyesi).
2. Sıradaki videoları YouTube'a "çocuklara özel" olarak yükler ve her birini sırayla bir sonraki günün 18:00'ine planlar.
3. YouTube istatistiklerini okur, raporu ve sitedeki video listesini günceller.

## Senin işin

Sadece raporu kontrol etmen yeterli. **Bölümleri artık elle yükleme**, yoksa aynı bölüm iki kez yüklenir.

İstersen `Bilgisayari_Guncelle.bat` ile buluttaki son hâli ve yeni videoları bilgisayarına indirebilirsin.

## Sorun olursa

- Raporda "YouTube'a bağlanılamadı" yazıyorsa: bilgisayarda `YouTube_Baglan.bat` → izin ver → `Anahtarlari_GitHuba_Gonder.bat`.
- Elle çalıştırmak istersen: GitHub → Actions → "Günlük Boncuk işi" → **Run workflow**.

## Bilmen gerekenler

- Site ve rapor herkese açık adreslerde. Raporda gizli bilgi yok; abone ve izlenme sayıları zaten YouTube'da görünüyor.
- Gizli anahtarlar GitHub'ın şifreli "Secrets" bölümünde durur, kodun içinde yoktur.
- Sesler Microsoft Edge'in ücretsiz seslendirme servisiyle yapılıyor. Bu servisin resmi bir ticari lisansı yok; kanal büyüyünce lisanslı bir sese geçmek daha güvenli olur.
- Görseller: Microsoft Fluent Emoji (MIT). Yazı tipi: Baloo 2 (OFL). Müzik ve efektler her bölüm için sıfırdan üretilir.
