# Boncuk Kanalı: Kullanım Rehberi

## Haftada 15 dakika: senin işin bu kadar

1. **Pazar günü** `Video_Uret.bat` dosyasına çift tıkla, `7` yaz, Enter'a bas.
   Bilgisayar 7 videoyu kendisi üretir (yaklaşık 10-20 dakika, bu sırada başka iş yapabilirsin).
2. `videolar` klasörü açılır. Her bölüm klasöründe:
   - `Bolum_XXX.mp4`: video
   - `yukleme_bilgisi.txt`: kopyalayıp yapıştıracağın başlık ve açıklama (etiketler açıklamanın sonunda hashtag olarak)
3. **Videoları bir kere izle** (her biri 30-50 sn). Garip bir şey varsa yükleme. Bu kontrol önemli, çünkü YouTube insan eli değmemiş seri üretimi cezalandırıyor.
4. YouTube Studio'dan 7 videoyu yükle ve **her gün 1 tane çıkacak şekilde zamanla** (Yayınla → Planla → tarih/saat).
   Önerilen saat: **17:00-19:00** (çocukların tablete en çok baktığı saatler).

## Kanalı açarken (bir kerelik)

- **Kanal adı önerileri:** "Boncuk ile Öğreniyorum", "Boncuk Çocuk", "Boncuk TV"
- **Kanal açıklaması:**
  > Merhaba, ben Boncuk! 🌱 Renk değiştiren minik bir arkadaşım. Her gün yeni bir oyunla renkleri, hayvanları ve İngilizce kelimeleri birlikte öğreniyoruz. 2-6 yaş için eğitici, kısa ve neşeli videolar.
- **Profil resmi:** hazır, `profil_resmi.png`.
- **Ayarlar → Kanal → Gelişmiş ayarlar → Kitle:** "Evet, bu kanal çocuklara özel olarak ayarlansın" seç. **Bu yasal bir zorunluluk** (ABD COPPA yasası). Yanlış işaretlersen kanal kapatılabilir.

## Her yüklemede

| Alan | Ne yapılacak |
|---|---|
| Başlık / Açıklama | `yukleme_bilgisi.txt` dosyasından kopyala (hashtag'ler açıklamanın içinde) |
| Kitle | **Evet, çocuklara özel** |
| Değiştirilmiş/yapay içerik | **Hayır** (animasyon, gerçekçi değil) |
| Görünürlük | Planla → her gün 1 tane |

## Ayda bir: derleme videosu (asıl para buradan gelir)

Çocuk kanallarında para, televizyonda saatlerce izlenen **uzun videolardan** gelir. Ay sonunda bana
"bu ayın videolarını 20 dakikalık derleme yap" demen yeterli. Ben birleştiririm, sen normal video olarak yüklersin.

## Bölüm türleri (sırayla döner)

| Tür | İçerik | Neden |
|---|---|---|
| `toplar` | Renkli toplar aynı renk bardağa atlar | CoComelon'un en çok izlenen Shorts'larının çoğu bu tür (renk öğretimi) |
| `golge` | "Bu kimin gölgesi?" 3 hayvan bilmecesi | Etkileşimli, tekrar izlenme oranı yüksek |
| `kule` | Renkli bloklarla kule, sonunda "Eyvah!" yıkılır | Sürpriz son, videonun tekrar tekrar izlenmesini sağlar |

Her bölümde renkler, sıralar, cümleler ve müzik farklıdır. Böylece videolar birbirinin kopyası olmaz.

## Gerçekçi beklenti

- İlk 1-2 ay izlenmeler düşük olabilir. Bu normal, algoritma kanalı tanıyor.
- Para kazanma şartı: 1.000 abone + 90 günde 10 milyon Shorts izlenmesi **veya** 4.000 saat uzun video izlenmesi.
  Çocuk kanallarında ikinci yol (derleme videoları) genelde daha hızlı sonuç verir.
- 30. günde YouTube Studio → Analytics'e bak. Hangi tür daha çok izlendiyse bana söyle, o türü artırırız.

## Teknik notlar

- Sesler Microsoft Edge'in ücretsiz seslendirme servisiyle yapılıyor (internet gerekir). Bu servis resmi bir ticari lisans içermez.
  Kanal büyüyünce Boncuk'u kendi sesinle ya da lisanslı bir ses servisiyle seslendirmek daha güvenli olur.
- Görseller: Microsoft Fluent Emoji (MIT lisansı). Yazı tipi: Baloo 2 (OFL). Müzik ve efektler her bölüm için sıfırdan üretilir. Hepsi ticari kullanıma uygun.
- Sayaç `uretim/durum.json` dosyasında tutulur, silme. Silersen numaralar baştan başlar.
