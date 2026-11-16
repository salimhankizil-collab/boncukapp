"""Google hesabını bir kez bağlar (tarayıcıda izin sayfası açılır)."""
import youtube_api

yt = youtube_api.servis(etkilesimli=True)
k = youtube_api.kanal_bilgisi(yt)
print(f"BAĞLANDI: {k['ad']} | abone: {k['abone']} | video: {k['video']}")
