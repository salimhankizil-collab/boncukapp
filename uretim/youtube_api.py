"""YouTube Data API v3 bağlantısı: giriş, video yükleme, istatistik okuma.

Gizli dosyalar (kimseyle paylaşma):
  gizli/client_secret.json : Google Cloud'dan indirilen masaüstü istemci dosyası
  gizli/token.json         : ilk girişten sonra otomatik oluşur
"""
from __future__ import annotations

import pathlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GIZLI = pathlib.Path(__file__).parent.parent / "gizli"
ISTEMCI = GIZLI / "client_secret.json"
TOKEN = GIZLI / "token.json"
KAPSAMLAR = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class BaglantiYok(Exception):
    pass


def kimlik(etkilesimli=False):
    kim = None
    if TOKEN.exists():
        kim = Credentials.from_authorized_user_file(str(TOKEN), KAPSAMLAR)
    if kim and kim.valid:
        return kim
    if kim and kim.expired and kim.refresh_token:
        try:
            kim.refresh(Request())
            TOKEN.write_text(kim.to_json(), encoding="utf-8")
            return kim
        except Exception:  # noqa: BLE001
            kim = None
    if not etkilesimli:
        raise BaglantiYok("Google bağlantısı yok ya da süresi dolmuş. 'python baglan.py' çalıştırılmalı.")
    if not ISTEMCI.exists():
        raise BaglantiYok(f"{ISTEMCI} bulunamadı.")
    akis = InstalledAppFlow.from_client_secrets_file(str(ISTEMCI), KAPSAMLAR)
    kim = akis.run_local_server(port=0, prompt="consent", open_browser=True,
                                success_message="Bağlantı tamam! Bu sekmeyi kapatabilirsin.")
    TOKEN.write_text(kim.to_json(), encoding="utf-8")
    return kim


def servis(etkilesimli=False):
    return build("youtube", "v3", credentials=kimlik(etkilesimli), cache_discovery=False)


def kanal_bilgisi(yt):
    r = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
    if not r.get("items"):
        raise BaglantiYok("Bu Google hesabında YouTube kanalı bulunamadı.")
    k = r["items"][0]
    s = k["statistics"]
    return {
        "id": k["id"],
        "ad": k["snippet"]["title"],
        "abone": int(s.get("subscriberCount", 0)),
        "izlenme": int(s.get("viewCount", 0)),
        "video": int(s.get("videoCount", 0)),
        "yuklemeler_listesi": k["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def kanal_videolari(yt, yuklemeler_listesi):
    """Kanaldaki tüm videolar (gizli ve planlanmış olanlar dahil) + istatistikleri."""
    idler, sayfa = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=yuklemeler_listesi, maxResults=50, pageToken=sayfa).execute()
        idler += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        sayfa = r.get("nextPageToken")
        if not sayfa:
            break
    videolar = []
    for i in range(0, len(idler), 50):
        r = yt.videos().list(part="snippet,statistics,status", id=",".join(idler[i:i + 50])).execute()
        for v in r.get("items", []):
            st = v.get("statistics", {})
            videolar.append({
                "id": v["id"],
                "baslik": v["snippet"]["title"],
                "aciklama": v["snippet"].get("description", ""),
                "yayin": v["snippet"].get("publishedAt"),
                "gorunurluk": v["status"].get("privacyStatus"),
                "plan": v["status"].get("publishAt"),
                "cocuk": v["status"].get("madeForKids"),
                "izlenme": int(st.get("viewCount", 0)),
                "begeni": int(st.get("likeCount", 0)),
            })
    return videolar


def video_yukle(yt, dosya, baslik, aciklama, yayin_zamani_utc=None):
    """yayin_zamani_utc verilirse video gizli yüklenir ve o saatte otomatik yayınlanır (RFC3339, ör. 2026-11-20T15:00:00Z)."""
    govde = {
        "snippet": {
            "title": baslik[:100],
            "description": aciklama[:5000],
            "categoryId": "27",  # Eğitim
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "tr",
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": True,  # yasal zorunluluk: çocuklara özel
            "containsSyntheticMedia": False,
            "embeddable": True,
        },
    }
    if yayin_zamani_utc:
        govde["status"]["publishAt"] = yayin_zamani_utc
    medya = MediaFileUpload(str(dosya), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    istek = yt.videos().insert(part="snippet,status", body=govde, media_body=medya)
    cevap = None
    while cevap is None:
        _, cevap = istek.next_chunk()
    return cevap["id"]
