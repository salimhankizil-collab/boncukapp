"""Sıradaki bölümleri üretir.

Kullanım:
    python uret.py              -> sıradaki 1 bölümü üretir
    python uret.py --adet 7     -> bir haftalık (7) bölüm üretir
    python uret.py --tur golge  -> türü elle seç (toplar / kule / golge / hikaye)
    python uret.py --yeniden 6-10 -> yüklenmemiş bölümleri aynı içerikle yeniden üret
"""
import argparse
import json
import pathlib

import numpy as np

import hikaye
import motor
from hayvanlar import HAYVANLAR
from hikayeler import HIKAYELER

KOK = pathlib.Path(__file__).parent
DURUM = KOK / "durum.json"
CIKTI = KOK.parent / "videolar"
SIRA = ["toplar", "golge", "kule"]  # 1-10. bölümlerin sırası (değiştirme: eski bölümler yeniden üretilebilsin)
YENI_SIRA_BASI = 13  # 11-12 bulutta eski sırayla üretildi (gölge, kule)
YENI_SIRA = ["hikaye", "toplar", "hikaye", "golge", "hikaye", "kule"]  # 11. bölümden itibaren: her iki videodan biri hikâye
TURLER = ["toplar", "golge", "kule", "hikaye"]


def tur_bul(no):
    if no < YENI_SIRA_BASI:
        return SIRA[(no - 1) % len(SIRA)]
    return YENI_SIRA[(no - YENI_SIRA_BASI) % len(YENI_SIRA)]


def hikaye_bul(no):
    """Bu bölümün hikâyesi: hikâyeler sırayla kullanılır, bitince baştan döner."""
    onceki = sum(1 for k in range(YENI_SIRA_BASI, no) if tur_bul(k) == "hikaye")
    return HIKAYELER[onceki % len(HIKAYELER)]


def sahne_kur(no, tur, rng, ses, durum):
    if tur == "toplar":
        return motor.Toplar(rng, ses)
    if tur == "kule":
        return motor.Kule(rng, ses)
    if tur == "hikaye":
        return hikaye.Hikaye(rng, ses, hikaye_bul(no))
    return motor.Golge(rng, ses, hayvan_sec(rng, durum))

# Açıklamanın sonuna hashtag olarak eklenir (Shorts yüklemede ayrı etiket alanı yok).
# Toplam 15'i geçmesin: YouTube çok fazla etiketi spam sayar.
ETIKETLER_ORTAK = ["çocukvideoları", "okulöncesi", "eğiticivideo", "çocuklariçiningilizce", "bebekvideoları",
                   "BoncukÇocukTV", "shorts"]


def durum_oku():
    if DURUM.exists():
        return json.loads(DURUM.read_text(encoding="utf-8"))
    return {"bolum": 0, "kullanilan_hayvanlar": []}


def hayvan_sec(rng, durum):
    kalan = [h for h in HAYVANLAR if h["kod"] not in durum["kullanilan_hayvanlar"]]
    if len(kalan) < 3:
        durum["kullanilan_hayvanlar"] = []
        kalan = list(HAYVANLAR)
    secilen = [kalan[i] for i in rng.choice(len(kalan), 3, replace=False)]
    durum["kullanilan_hayvanlar"] += [h["kod"] for h in secilen]
    return secilen


def bilgi_yaz(klasor, tur, no, sahne):
    if tur == "toplar":
        renkler = [f"{o['ad']} ({o['ing']})" for o in sahne.toplar]
        baslik = "Renkleri Öğrenelim! 🔴🟠🟡🟢🔵🟣 Topları Bardaklara Koy | Boncuk #shorts"
        aciklama = ("Boncuk ile renkli topları aynı renkteki bardaklara koyuyoruz! Hem Türkçe hem İngilizce renkleri öğreniyoruz.\n\n"
                    "Bu bölümdeki renkler: " + ", ".join(renkler))
        etiket = ["renkleriöğreniyorum", "renkler", "learncolors", "colorsforkids"]
    elif tur == "kule":
        renkler = [f"{b['ad']} ({b['ing']})" for b in sahne.bloklar]
        baslik = "Renkli Kule! 🟥🟧🟨🟩🟦🟪 Eyvah, Kule Yıkıldı! | Renkleri Öğren | Boncuk #shorts"
        aciklama = ("Boncuk ile renkli bloklardan kocaman bir kule yapıyoruz. Ama eyvah! Hem Türkçe hem İngilizce renkleri öğreniyoruz.\n\n"
                    "Bu bölümdeki renkler: " + ", ".join(renkler))
        etiket = ["renkleriöğreniyorum", "renklikule", "learncolors", "blocksforkids"]
    elif tur == "hikaye":
        h = sahne.senaryo
        tr, en = h["kelime"]
        baslik = f"{h['baslik']} {h['emoji']} Boncuk, Pamuk ve Minik | Çocuk Hikâyesi #shorts"
        aciklama = (f"Boncuk, kedi Pamuk ve bebek Minik ile yeni bir hikâye! {h['ozet']}. "
                    f"Bu bölümde {h['ders']} öğreniyoruz.\n\n"
                    f"Bu bölümdeki hikâye: {h['baslik']} – kelime: {tr} ({en})")
        etiket = ["boncukvearkadaşları", "çocukhikayeleri", "kediyavrusu", "değerlereğitimi", "kidsstories"]
    else:
        adlar = [f"{h['ad']} ({h['ing']})" for h in sahne.hayvanlar]
        baslik = "Bu Kimin Gölgesi? 🔦🤔 Hayvanları Tahmin Et! | Boncuk #shorts"
        aciklama = ("Gölgeye bak, 3-2-1 say ve hangi hayvan olduğunu tahmin et! Her hayvanın İngilizcesini ve ilginç bir bilgisini öğreniyoruz.\n\n"
                    "Bu bölümdeki hayvanlar (cevaplar!): " + ", ".join(adlar))
        etiket = ["bukimingölgesi", "hayvanlarıöğreniyorum", "hayvanlar", "guesstheanimal", "tahminoyunu"]
    aciklama += ("\n\nBoncuk her gün yeni bir eğitici oyunla burada! 🌱"
                 "\n🎮 Bu videonun oyunu ve diğer oyunlar (reklamsız, ücretsiz): salimhankizil-collab.github.io/boncukapp\n\n"
                 + " ".join("#" + e for e in etiket + ETIKETLER_ORTAK))
    metin = (f"BÖLÜM {no}\n\nBAŞLIK (kopyala):\n{baslik}\n\n"
             f"AÇIKLAMA (kopyala, etiketler sonunda hashtag olarak var):\n{aciklama}\n\n"
             "YÜKLERKEN UNUTMA:\n"
             "- Kitle: 'Evet, çocuklara özel' seç (yasal zorunluluk).\n"
             "- 'Değiştirilmiş veya yapay içerik' sorusu: Hayır (animasyon, gerçekçi değil).\n")
    (klasor / "yukleme_bilgisi.txt").write_text(metin, encoding="utf-8")
    meta_kaydet(no, tur, sahne, baslik, aciklama)


RENK_ANAHTAR = {"Kırmızı": "red", "Turuncu": "orange", "Sarı": "yellow", "Yeşil": "green", "Mavi": "blue", "Mor": "purple", "Pembe": "pink"}
BOLUMLER = KOK.parent / "veri" / "bolumler.json"


def meta_kaydet(no, tur, sahne, baslik, aciklama):
    """Bölümün içeriğini (renkler/hayvanlar, başlık, açıklama) veri/bolumler.json'a yazar: web sitesi oyunları ve
    kanal videolarını bölümlerle eşleştirmek için kullanılır."""
    BOLUMLER.parent.mkdir(exist_ok=True)
    try:
        hepsi = json.loads(BOLUMLER.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        hepsi = {}
    eski = hepsi.get(str(no), {})
    if tur == "toplar":
        renkler, hayvanlar = [RENK_ANAHTAR[o["ad"]] for o in sahne.toplar], []
    elif tur == "kule":
        renkler, hayvanlar = [RENK_ANAHTAR[b["ad"]] for b in sahne.bloklar], []
    elif tur == "hikaye":
        renkler, hayvanlar = [], []
    else:
        renkler, hayvanlar = [], [h["kod"] for h in sahne.hayvanlar]
    hepsi[str(no)] = {
        "tur": tur, "baslik": baslik, "aciklama": aciklama,
        "imza": next((s for s in aciklama.splitlines() if s.startswith("Bu bölümdeki")), ""),
        "renkler": renkler, "hayvanlar": hayvanlar, "release": eski.get("release"),
    }
    if tur == "hikaye":  # sitedeki kelime oyunu bu bölümün eşyasıyla açılır
        h = sahne.senaryo
        hepsi[str(no)]["hikaye"] = h["kod"]
        hepsi[str(no)]["esya"] = (h.get("nesne") or {}).get("emoji", "")
    BOLUMLER.write_text(json.dumps(dict(sorted(hepsi.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=1), encoding="utf-8")


def bolum_uret(tur=None, onizleme=False):
    durum = durum_oku()
    no = durum["bolum"] + 1
    tur = tur or tur_bul(no)
    rng = np.random.default_rng(1000 + no)
    ses = motor.Ses()
    sahne = sahne_kur(no, tur, rng, ses, durum)
    klasor = CIKTI / f"Bolum_{no:03d}_{tur}"
    klasor.mkdir(parents=True, exist_ok=True)
    print(f"Bölüm {no} ({tur}) üretiliyor, süre {sahne.T:.1f} sn ...")
    motor.video_yap(sahne, ses, 1000 + no, klasor / f"Bolum_{no:03d}.mp4", onizleme)
    bilgi_yaz(klasor, tur, no, sahne)
    if not onizleme:
        durum["bolum"] = no
        DURUM.write_text(json.dumps(durum, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Hazır:", klasor)
    return klasor


def bilgileri_yenile():
    """Videoları yeniden üretmeden, mevcut bölümlerin yukleme_bilgisi.txt dosyalarını baştan yazar."""
    son = durum_oku()["bolum"]
    durum = {"bolum": 0, "kullanilan_hayvanlar": []}
    for no in range(1, son + 1):
        tur = tur_bul(no)
        rng = np.random.default_rng(1000 + no)
        ses = motor.Ses()
        sahne = sahne_kur(no, tur, rng, ses, durum)
        klasor = CIKTI / f"Bolum_{no:03d}_{tur}"
        klasor.mkdir(parents=True, exist_ok=True)
        bilgi_yaz(klasor, tur, no, sahne)
        print("yenilendi:", klasor.name)


def yeniden_uret(bas, son):
    """Daha önce üretilmiş bölümleri (ör. motor güncellenince, henüz yüklenmemiş olanları) aynı içerikle yeniden üretir.
    Hayvan seçimi sırası bozulmasın diye 1. bölümden itibaren sahneler sırayla kurulur, sadece [bas, son] videoya dökülür."""
    durum = {"bolum": 0, "kullanilan_hayvanlar": []}
    for no in range(1, son + 1):
        tur = tur_bul(no)
        rng = np.random.default_rng(1000 + no)
        ses = motor.Ses()
        sahne = sahne_kur(no, tur, rng, ses, durum)
        if no < bas:
            continue
        klasor = CIKTI / f"Bolum_{no:03d}_{tur}"
        klasor.mkdir(parents=True, exist_ok=True)
        print(f"Bölüm {no} ({tur}) yeniden üretiliyor, süre {sahne.T:.1f} sn ...", flush=True)
        motor.video_yap(sahne, ses, 1000 + no, klasor / f"Bolum_{no:03d}.mp4")
        bilgi_yaz(klasor, tur, no, sahne)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--adet", type=int, default=1)
    ap.add_argument("--tur", choices=TURLER)
    ap.add_argument("--onizleme", action="store_true", help="yarım çözünürlük, sayaç ilerlemez")
    ap.add_argument("--bilgi-yenile", action="store_true", help="sadece yukleme_bilgisi.txt dosyalarını yeniden yaz")
    ap.add_argument("--yeniden", metavar="BAS-SON", help="bu aralıktaki bölümleri yeniden üret, ör. 6-10")
    a = ap.parse_args()
    if a.yeniden:
        bas, son = (int(x) for x in a.yeniden.split("-"))
        yeniden_uret(bas, son)
        raise SystemExit
    if a.bilgi_yenile:
        bilgileri_yenile()
        raise SystemExit
    for _ in range(a.adet):
        bolum_uret(a.tur, a.onizleme)
