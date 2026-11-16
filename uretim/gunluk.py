"""Her gün otomatik çalışan iş (GitHub Actions'ta bulutta ya da elle bilgisayarda):
  1) Yüklenmemiş video sayısı azaldıysa yeni bölümler üretir.
  2) YouTube incelemesi onaylıysa sıradakileri yükleyip 18:00'e planlar; onaylı değilse yeni bölümleri
     GitHub "Release" olarak koyar ve rapora "bunları yükle" görevi yazar.
  3) Kanal istatistiklerini toplar.
  4) Web sitesi verisini (site/veri/videolar.json) ve raporu (site/rapor/rapor.json) yazar.

Elle çalıştırmak için:  python uretim/gunluk.py
Yüklemeden denemek için: python uretim/gunluk.py --yukleme-yok
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import traceback

KOK = pathlib.Path(__file__).parent
PROJE = KOK.parent
VERI = PROJE / "veri"
VERI.mkdir(exist_ok=True)
VIDEOLAR = PROJE / "videolar"
SITE = PROJE / "site"
AYARLAR = VERI / "ayarlar.json"
ESLEME = VERI / "yuklemeler.json"   # bölüm no -> YouTube video id
GECMIS = VERI / "gecmis.json"       # günlük kanal anlık görüntüleri (YouTube kuralı: en fazla 30 gün saklanır)
SAKLAMA_GUN = 30
BOLUMLER = VERI / "bolumler.json"   # bölüm içerikleri (uret.py yazar)
RAPOR = VERI / "rapor.json"
LOG = VERI / "gunluk.log"
TR = dt.timezone(dt.timedelta(hours=3))  # Türkiye saati
BULUT = os.environ.get("GITHUB_ACTIONS") == "true"
REPO = os.environ.get("GITHUB_REPOSITORY", "salimhankizil-collab/boncukapp")

VARSAYILAN = {
    "yayin_saati": "18:00",
    "denetim_onayli": False,   # YouTube API incelemesi onaylanınca true yap: videolar otomatik yüklenip planlanır
    "tampon_gun": 7,           # elde en az bu kadar yüklenmemiş bölüm tutulur
    "gunluk_en_fazla_yukleme": 2,
}
TUR_ADI = {"toplar": "Renkli toplar", "golge": "Gölge bilmecesi", "kule": "Renkli kule", "hikaye": "Boncuk ve Arkadaşları"}


def oku(yol, varsayilan):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return varsayilan


def yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")


def log(mesaj):
    satir = f"{dt.datetime.now(TR):%Y-%m-%d %H:%M} {mesaj}"
    print(satir, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(satir + "\n")


def mp4_yolu(no, b):
    return VIDEOLAR / f"Bolum_{int(no):03d}_{b['tur']}" / f"Bolum_{int(no):03d}.mp4"


def oyun_linki(b):
    if b["tur"] == "hikaye":
        return "oyunlar/kelime.html?esya=" + b.get("esya", "")
    if b["tur"] == "golge":
        return "oyunlar/golge.html?hayvanlar=" + ",".join(b["hayvanlar"])
    return f"oyunlar/{b['tur']}.html?renkler=" + ",".join(b["renkler"])


def esle(bol, videolar, esleme):
    """Kanaldaki videoları bölümlerle eşleştir (elle yüklenenler dahil): açıklamadaki 'Bu bölümdeki ...' satırı her bölümde farklıdır."""
    idler = {v["id"] for v in videolar}
    esleme = {no: vid for no, vid in esleme.items() if vid in idler}
    bilinen = set(esleme.values())
    for v in videolar:
        if v["id"] in bilinen:
            continue
        for no, b in bol.items():
            if no not in esleme and b.get("imza") and b["imza"] in v["aciklama"]:
                esleme[no] = v["id"]
                break
    return esleme


def yayin_zamani(v):
    t = v["plan"] if (v["gorunurluk"] == "private" and v["plan"]) else (v["yayin"] if v["gorunurluk"] == "public" else None)
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None


def release_olustur(nolar, bol):
    """Bulutta üretilen bölümleri indirilebilir bir GitHub Release olarak koyar (elle yükleme dönemi için)."""
    etiket = f"bolum-{min(nolar):03d}-{max(nolar):03d}"
    dosyalar = []
    for no in nolar:
        mp4 = mp4_yolu(no, bol[str(no)])
        txt = mp4.parent / "yukleme_bilgisi.txt"
        hedef_txt = mp4.parent / f"Bolum_{no:03d}_yukleme_bilgisi.txt"
        shutil.copy(txt, hedef_txt)
        dosyalar += [str(mp4), str(hedef_txt)]
    notlar = ("Bu bölümleri YouTube Studio'dan yükle ve her gün 18:00'e birer tane planla. "
              "Başlık ve açıklama her bölümün yukleme_bilgisi.txt dosyasında. Kitle: 'Evet, çocuklara özel'.")
    subprocess.run(["gh", "release", "create", etiket, *dosyalar, "--repo", REPO, "--title", f"Bölüm {min(nolar)}–{max(nolar)}",
                    "--notes", notlar], check=True)
    return etiket


def release_indir(no, b):
    mp4 = mp4_yolu(no, b)
    mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "release", "download", b["release"], "--repo", REPO, "-p", mp4.name, "-D", str(mp4.parent), "--clobber"], check=True)
    return mp4


def calistir(yukleme_yok=False):
    ayar = {**VARSAYILAN, **oku(AYARLAR, {})}
    yaz(AYARLAR, ayar)
    esleme = oku(ESLEME, {})
    gecmis = oku(GECMIS, {})
    simdi = dt.datetime.now(TR)
    bugun = simdi.date().isoformat()
    gorevler, uyarilar = [], []
    kanal, videolar, yt = None, [], None

    # 1) YouTube bağlantısı
    try:
        import youtube_api
        yt = youtube_api.servis()
        kanal = youtube_api.kanal_bilgisi(yt)
        videolar = youtube_api.kanal_videolari(yt, kanal["yuklemeler_listesi"])
    except Exception as e:  # noqa: BLE001
        yt = None
        uyarilar.append(f"YouTube'a bağlanılamadı: {e}")
        gorevler.append({"gorev": "YouTube bağlantısını yenile: Claude'a 'YouTube bağlantısı koptu' yaz, birlikte yenileyelim.", "link": ""})
        log(f"BAĞLANTI HATASI: {e}")

    bol = oku(BOLUMLER, {})
    if yt:
        esleme = esle(bol, videolar, esleme)
        yaz(ESLEME, esleme)

    # 2) Üretim: yüklenmemiş bölüm sayısı tampondan azsa yenilerini üret
    bekleyen = [int(no) for no in sorted(bol, key=int) if no not in esleme]
    eksik = ayar["tampon_gun"] - len(bekleyen)
    yeni = []
    if eksik > 0 and (yt or not BULUT):
        import uret
        log(f"Sırada {len(bekleyen)} bölüm var, {eksik} yeni bölüm üretiliyor.")
        for _ in range(min(eksik, 7)):
            try:
                klasor = uret.bolum_uret()
                yeni.append(int(klasor.name.split("_")[1]))
            except Exception as e:  # noqa: BLE001
                uyarilar.append(f"Video üretilemedi: {e}")
                log("ÜRETİM HATASI: " + traceback.format_exc())
                break
        bol = oku(BOLUMLER, {})
        if BULUT and yeni and not ayar["denetim_onayli"]:
            try:
                etiket = release_olustur(yeni, bol)
                for no in yeni:
                    bol[str(no)]["release"] = etiket
                yaz(BOLUMLER, bol)
                log(f"Bölüm {min(yeni)}-{max(yeni)} indirilebilir olarak konuldu: {etiket}")
            except Exception as e:  # noqa: BLE001
                uyarilar.append(f"Yeni bölümler GitHub'a konulamadı: {e}")
                log("RELEASE HATASI: " + traceback.format_exc())
        bekleyen = [int(no) for no in sorted(bol, key=int) if no not in esleme]

    # 3) Otomatik yükleme (yalnızca YouTube incelemesi onaylıysa; onaysız yüklemeler kalıcı olarak gizli kilitlenir)
    yuklenen_bugun = []
    if yt and not yukleme_yok and bekleyen and ayar["denetim_onayli"]:
        saat, dakika = map(int, ayar["yayin_saati"].split(":"))
        try:
            tarihler = [t for t in (yayin_zamani(v) for v in videolar) if t]
            son = max(tarihler) if tarihler else None
            yarin = (simdi + dt.timedelta(days=1)).replace(hour=saat, minute=dakika, second=0, microsecond=0)
            while bekleyen and len(yuklenen_bugun) < ayar["gunluk_en_fazla_yukleme"] and (son is None or son < simdi + dt.timedelta(days=2)):
                slot = max(yarin, (son.astimezone(TR) + dt.timedelta(days=1)).replace(hour=saat, minute=dakika, second=0, microsecond=0)) if son else yarin
                no = bekleyen.pop(0)
                b = bol[str(no)]
                mp4 = mp4_yolu(no, b)
                if not mp4.exists() and b.get("release"):
                    mp4 = release_indir(no, b)
                if not mp4.exists():
                    log(f"Bölüm {no} dosyası bulunamadı, atlandı.")
                    continue
                utc = slot.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                vid = youtube_api.video_yukle(yt, mp4, b["baslik"], b["aciklama"], utc)
                esleme[str(no)] = vid
                yuklenen_bugun.append(no)
                son = slot
                log(f"Bölüm {no} yüklendi, {slot:%d.%m %H:%M}'de yayınlanacak ({vid}).")
            yaz(ESLEME, esleme)
            if yuklenen_bugun:
                videolar = youtube_api.kanal_videolari(yt, kanal["yuklemeler_listesi"])
        except Exception as e:  # noqa: BLE001
            uyarilar.append(f"Yükleme hatası: {e}")
            log("YÜKLEME HATASI: " + traceback.format_exc())

    # 4) İstatistikler
    vid_bol = {vid: int(no) for no, vid in esleme.items()}
    if kanal:
        gecmis[bugun] = {"abone": kanal["abone"], "izlenme": sum(v["izlenme"] for v in videolar) or kanal["izlenme"], "video": len(videolar)}
    # YouTube API kuralı: istatistikler 30 günden uzun saklanmaz, eskiler silinir
    sinir = (simdi.date() - dt.timedelta(days=SAKLAMA_GUN)).isoformat()
    gecmis = {g: v for g, v in gecmis.items() if g >= sinir}
    # Gizlilik politikası sözü: YouTube'a 7 gündür bağlanılamıyorsa (izin geri alınmış olabilir)
    # saklanan istatistikler ve video listesi silinir.
    if not kanal and gecmis and max(gecmis) < (simdi.date() - dt.timedelta(days=7)).isoformat():
        gecmis = {}
        (SITE / "veri" / "videolar.json").unlink(missing_ok=True)
        uyarilar.append("7 gündür YouTube'a bağlanılamadı; saklanan istatistikler silindi.")
    yaz(GECMIS, gecmis)
    gunler = sorted(gecmis)
    gunluk = []
    for i, g in enumerate(gunler):
        onceki = gecmis[gunler[i - 1]]["izlenme"] if i else None
        gunluk.append({"tarih": g, "toplam_izlenme": gecmis[g]["izlenme"], "abone": gecmis[g]["abone"],
                       "gunluk_izlenme": (gecmis[g]["izlenme"] - onceki) if onceki is not None else None})

    def toplam_once(gun):
        hedef = (simdi.date() - dt.timedelta(days=gun)).isoformat()
        eski = [g for g in gunler if g <= hedef]
        return gecmis[eski[-1]]["izlenme"] if eski else (gecmis[gunler[0]]["izlenme"] if gunler else 0)

    son_toplam = gecmis[gunler[-1]]["izlenme"] if gunler else 0
    video_satirlari, site_videolari = [], []
    for v in videolar:
        no = vid_bol.get(v["id"])
        b = bol.get(str(no)) if no else None
        tur = b["tur"] if b else ("golge" if "Gölgesi" in v["baslik"] else "kule" if "Kule" in v["baslik"]
                                  else "hikaye" if "Pamuk" in v["baslik"] else "toplar")
        if v["gorunurluk"] == "public":
            durum = "Yayında"
        elif v["gorunurluk"] == "private" and v["plan"]:
            durum = "Planlandı"
        else:
            durum = "Gizli"
            gorevler.append({"gorev": f"Bölüm {no or '?'} gizli duruyor: Studio'da aç ve 'Herkese açık' yap ya da 18:00'e planla.",
                             "link": f"https://studio.youtube.com/video/{v['id']}/edit"})
        if v["cocuk"] is False:
            gorevler.append({"gorev": f"Bölüm {no or '?'} 'çocuklara özel' işaretli değil: Studio'da kitleyi 'Evet, çocuklara özel' yap.",
                             "link": f"https://studio.youtube.com/video/{v['id']}/edit"})
        zaman = yayin_zamani(v)
        tarih = zaman.astimezone(TR).strftime("%Y-%m-%d %H:%M") if zaman else ""
        video_satirlari.append({"bolum": no, "tur": TUR_ADI.get(tur, tur), "durum": durum, "tarih": tarih,
                                "izlenme": v["izlenme"], "begeni": v["begeni"], "link": f"https://youtube.com/shorts/{v['id']}"})
        if durum == "Yayında":
            site_videolari.append({"id": v["id"], "bolum": no, "tur": tur, "baslik": v["baslik"], "tarih": tarih,
                                   "oyun": oyun_linki(b) if b else f"oyunlar/{tur}.html"})
    video_satirlari.sort(key=lambda r: (r["bolum"] is None, -(r["bolum"] or 0)))
    site_videolari.sort(key=lambda r: r["tarih"], reverse=True)

    turler = []
    for tur, ad in TUR_ADI.items():
        yay = [r for r in video_satirlari if r["tur"] == ad and r["durum"] == "Yayında"]
        turler.append({"tur": ad, "video": len(yay), "ortalama_izlenme": round(sum(r["izlenme"] for r in yay) / len(yay)) if yay else 0})

    planli = [r for r in video_satirlari if r["durum"] == "Planlandı"]
    if yt and not ayar["denetim_onayli"] and bekleyen and len(planli) < 3:
        sec = bekleyen[:7]
        rel = sorted({bol[str(n)].get("release") for n in sec if bol[str(n)].get("release")})
        nerede = (f"İndir: GitHub'daki '{', '.join(rel)}' sayfası." if rel else
                  "Dosyalar bilgisayardaki 'videolar' klasöründe.")
        gorevler.insert(0, {
            "gorev": (f"Planlı videon {len(planli)} gün sonra bitiyor. Bölüm {sec[0]}–{sec[-1]}'i YouTube Studio'dan yükle ve her gün "
                      f"18:00'e birer tane planla. {nerede} Başlık ve açıklama her bölümün yukleme_bilgisi.txt dosyasında."),
            "link": f"https://github.com/{REPO}/releases/tag/{rel[0]}" if rel else "https://studio.youtube.com/"})

    ozet = {
        "guncelleme": simdi.strftime("%Y-%m-%d %H:%M"),
        "baglanti": "Bağlı" if yt else "Bağlantı yok",
        "otomatik_yayin": "Açık" if ayar["denetim_onayli"] else "YouTube onayı bekleniyor",
        "abone": kanal["abone"] if kanal else (gecmis[gunler[-1]]["abone"] if gunler else 0),
        "toplam_izlenme": son_toplam,
        "dun_izlenme": gunluk[-1]["gunluk_izlenme"] if gunluk and gunluk[-1]["gunluk_izlenme"] is not None else 0,
        "son7_izlenme": son_toplam - toplam_once(7),
        "son30_izlenme": son_toplam - toplam_once(30),
        "yayinda": sum(r["durum"] == "Yayında" for r in video_satirlari),
        "planli": len(planli),
        "hazir_bekleyen": len(bekleyen),
        "bugun_yuklenen": len(yuklenen_bugun),
        "uyari": " · ".join(uyarilar),
    }
    if not gorevler:
        gorevler.append({"gorev": "Bugün senin yapman gereken bir şey yok.", "link": ""})
    rapor = {"ozet": [ozet], "gunluk": gunluk, "videolar": video_satirlari, "turler": turler, "gorevler": gorevler}
    yaz(RAPOR, rapor)
    yaz(SITE / "rapor" / "rapor.json", rapor)
    if yt:  # bağlantı yoksa sitedeki son video listesini koru
        yaz(SITE / "veri" / "videolar.json", site_videolari)
    log(f"Rapor yazıldı: abone {ozet['abone']}, toplam izlenme {ozet['toplam_izlenme']}, sırada {len(bekleyen)} bölüm.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yukleme-yok", action="store_true")
    a = ap.parse_args()
    try:
        calistir(a.yukleme_yok)
    except Exception:  # noqa: BLE001
        log("GENEL HATA: " + traceback.format_exc())
        raise
