"""YouTube kanal kapak görseli (2560x1440). Önemli kısım ortadaki 1546x423 alanda; telefonda sadece orası görünür."""
import pathlib

from PIL import Image, ImageDraw, ImageFilter

import motor

W, H = 2560, 1440
im = Image.new("RGBA", (W, H))
renkler = [r[2] for r in motor.RENKLER[:6]]
# yumuşak gökkuşağı şeritleri
bant = H / 6
for i, c in enumerate(renkler):
    ImageDraw.Draw(im).rectangle([0, i * bant, W, (i + 1) * bant + 2], fill=motor.acik(c, 0.62))
im = im.filter(ImageFilter.GaussianBlur(60))
d = ImageDraw.Draw(im)
# ortadaki beyaz pano (telefon güvenli alanı)
pano = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(pano).rounded_rectangle([470, 490, 2090, 950], 90, fill=(255, 255, 255, 235))
im.alpha_composite(pano.filter(ImageFilter.GaussianBlur(2)))

# kenarlarda farklı renklerde Boncuklar (masaüstünde görünür)
for x, y, c, s in [(250, 820, renkler[0], 0.9), (2310, 820, renkler[4], 0.9), (400, 1250, renkler[2], 0.7), (2160, 1250, renkler[3], 0.7)]:
    b = motor.boncuk(c, False, 0)
    b = b.resize((int(340 * s), int(400 * s)), Image.LANCZOS)
    im.paste(b, (int(x - b.width / 2), int(y - b.height / 2)), b)
# panonun solunda ana Boncuk
b = motor.boncuk(motor.BONCUK_RENK, False, 2).resize((238, 280), Image.LANCZOS)
im.paste(b, (560, 580), b)
# yazılar (telefon güvenli alanı: x 507-2053, y 508-931)
motor.yapistir(im, motor.gokkusagi_yazi("Boncuk Çocuk TV", 118), 1440, 640)
motor.yapistir(im, motor.yazi_sprite("Renkler • Hayvanlar • İngilizce", 62, motor.KOYU_YAZI, (255, 255, 255), 8), 1440, 765)
motor.yapistir(im, motor.yazi_sprite("Her gün yeni bir oyun!", 52, (255, 138, 28), (255, 255, 255), 8), 1440, 855)

hedef = pathlib.Path(__file__).parent.parent / "kanal_kapak.png"
im.convert("RGB").save(hedef)
print(hedef)
