"""Buluttaki (GitHub Release) bölüm videolarını bilgisayardaki bölüm klasörlerine indirir.

Her bölüm videolar/Bolum_NNN_tur/ klasörüne gider (Bolum_NNN.mp4 + yukleme_bilgisi.txt).
Bilgisayarda zaten olan bölümler atlanır. Bilgisayari_Guncelle.bat bu dosyayı çalıştırır.
"""
import json
import pathlib
import shutil
import subprocess
import tempfile

PROJE = pathlib.Path(__file__).parent.parent
VIDEOLAR = PROJE / "videolar"
REPO = "salimhankizil-collab/boncukapp"


def main():
    bolumler = json.loads((PROJE / "veri" / "bolumler.json").read_text(encoding="utf-8"))
    indirilen = 0
    for no, b in sorted(bolumler.items(), key=lambda kv: int(kv[0])):
        no = int(no)
        if not b.get("release"):
            continue
        klasor = VIDEOLAR / f"Bolum_{no:03d}_{b['tur']}"
        mp4 = klasor / f"Bolum_{no:03d}.mp4"
        if mp4.exists() and mp4.stat().st_size > 0:
            continue
        klasor.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as gecici:
            subprocess.run(["gh", "release", "download", b["release"], "--repo", REPO,
                            "-p", f"Bolum_{no:03d}.mp4", "-p", f"Bolum_{no:03d}_yukleme_bilgisi.txt", "-D", gecici], check=True)
            shutil.move(str(pathlib.Path(gecici) / mp4.name), mp4)
            txt = pathlib.Path(gecici) / f"Bolum_{no:03d}_yukleme_bilgisi.txt"
            if txt.exists():
                shutil.move(str(txt), klasor / "yukleme_bilgisi.txt")
        print(f"indirildi: {klasor.name}")
        indirilen += 1
    print(f"Tamam: {indirilen} yeni bölüm indirildi." if indirilen else "Bütün bölümler zaten bilgisayarda.")


if __name__ == "__main__":
    main()
