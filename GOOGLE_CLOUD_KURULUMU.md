# Google Cloud Kurulumu (bir kerelik, ~15 dakika)

Bu adımlar bilgisayardaki programın, **senin izninle** kanalına video yükleyip istatistik okuyabilmesi içindir.
Hepsi ücretsizdir, kredi kartı istemez. Bir adım isterse **dur ve bana yaz**.

> ⚠️ Her adımda **kanalın bağlı olduğu Gmail hesabıyla** giriş yaptığından emin ol (sağ üstteki profil resmi).

---

## Adım 1: Proje oluştur
1. https://console.cloud.google.com adresini aç ve kanalın Gmail hesabıyla giriş yap.
2. İlk girişte şartlar sorulursa ülke olarak **Türkiye** seç ve kabul et.
3. Üst çubukta proje seçiciye tıkla (yazısı "Proje seçin" ya da "My First Project" olabilir) → **YENİ PROJE**.
4. Proje adı: `Boncuk Otomasyon` → **OLUŞTUR**.
5. Oluşunca üstteki bildirimden **PROJEYİ SEÇ**'e tıkla.

## Adım 2: YouTube API'sini aç
1. Üstteki arama kutusuna `YouTube Data API v3` yaz ve çıkan sonuca tıkla.
2. **ETKİNLEŞTİR** butonuna bas.

## Adım 3: İzin ekranı (OAuth)
1. Arama kutusuna `OAuth consent screen` (veya "OAuth izin ekranı") yaz ve aç.
2. **Başlayın / Get started** butonuna bas:
   - Uygulama adı: `Boncuk Otomasyon`
   - Kullanıcı destek e-postası: kendi Gmail'in
   - **İleri** → Kitle (Audience): **Harici / External** → **İleri**
   - İletişim bilgileri: kendi Gmail'in → **İleri**
   - Kullanıcı verileri politikasını kabul et → **Devam** → **Oluştur**
3. Sol menüden **Kitle / Audience** sayfasına git:
   - "Test kullanıcıları" bölümünde **+ ADD USERS** → kendi Gmail adresini ekle → Kaydet.
   - **"Publish app" butonu şimdilik çalışmaz** (ana sayfa ve gizlilik politikası adresi ister). Bu adımı atla, "Testing" modunda kal.
     Bu modda bağlantı 7 günde bir yenilenir: rapor sayfası haber verir, `YouTube_Baglan.bat` dosyasına çift tıklaman yeterli.

## Adım 4: Anahtar dosyasını indir
1. Sol menüden **İstemciler / Clients** → **+ İSTEMCİ OLUŞTUR / CREATE CLIENT**.
2. Uygulama türü: **Masaüstü uygulaması / Desktop app**, ad: `Boncuk PC` → **OLUŞTUR**.
3. Açılan pencerede **JSON'U İNDİR / DOWNLOAD JSON** butonuna bas.
4. İnen dosyanın adını `client_secret.json` yap ve şu klasöre taşı:
   **`C:\Users\Lenovo\YouTube\gizli\`**

> 🔒 Bu dosya kanalının anahtarı gibidir. **Kimseyle paylaşma, içeriğini bana da yapıştırma.** Klasöre koyman yeterli, ben dosyanın sadece yerinde olup olmadığına bakacağım.

## Adım 5: Bana "tamam" yaz
Ben bağlantıyı başlatınca tarayıcında bir Google izin sayfası açılacak:
- **"Google bu uygulamayı doğrulamadı"** uyarısı çıkacak. Bu normal, uygulama senin kendi uygulaman.
  **Gelişmiş → Boncuk Otomasyon'a git (güvenli değil)** yolunu izle.
- İstenen izinleri işaretle → **Devam**.

---

## Daha sonra: YouTube incelemesi (herkese açık otomatik yayın için)

YouTube, yeni API projelerinden yüklenen videoları **gizli** olarak kilitler. Kilidi kaldırmak için Google'a bir inceleme formu
gönderilir. Formun cevaplarını ben hazırlayacağım, sen sadece gönderirsin. Onay gelene kadar sistem videoları gizli olarak yükler,
rapor sayfası da sana her gün "şu videoyu herkese açık yap" diye hatırlatır (telefondan tek dokunuş).
