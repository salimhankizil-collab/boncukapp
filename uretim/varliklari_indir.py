"""Gerekli görselleri (Microsoft Fluent Emoji 3D, MIT lisansı) ve yazı tipini (Baloo 2, OFL) bir kez indirir."""
import pathlib
import urllib.parse
import urllib.request

KOK = pathlib.Path(__file__).parent / "varliklar"
EMOJI = KOK / "emoji"
EMOJI.mkdir(parents=True, exist_ok=True)

FLUENT = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/{}/3D/{}_3d.png"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/baloo2/Baloo2%5Bwght%5D.ttf"

# emoji kodu -> Fluent klasör adı
ADLAR = {
    "1f981": "Lion", "1f418": "Elephant", "1f992": "Giraffe", "1f407": "Rabbit", "1f408": "Cat",
    "1f415": "Dog", "1f40e": "Horse", "1f404": "Cow", "1f411": "Ewe", "1f413": "Rooster",
    "1f986": "Duck", "1f989": "Owl", "1f427": "Penguin", "1f422": "Turtle", "1f40c": "Snail",
    "1f98b": "Butterfly", "1f980": "Crab", "1f419": "Octopus", "1f42c": "Dolphin", "1f40b": "Whale",
    "1f988": "Shark", "1f42b": "Two-hump camel", "1f993": "Zebra", "1f998": "Kangaroo",
    "1f994": "Hedgehog", "1f43f": "Chipmunk", "1f99c": "Parrot", "1f9a9": "Flamingo",
    "1f41d": "Honeybee", "1f41e": "Lady beetle", "1f996": "T-rex", "1f412": "Monkey",
    "1f405": "Tiger", "1f98c": "Deer", "1f98f": "Rhinoceros", "1f99b": "Hippopotamus",
    "1f40a": "Crocodile", "1f985": "Eagle", "1f9a2": "Swan", "1f99a": "Peacock", "1f9a5": "Sloth",
    "1f9a6": "Otter", "1f401": "Mouse", "1f987": "Bat", "1f41c": "Ant", "1f98d": "Gorilla",
    "1f406": "Leopard", "1f40d": "Snake",
}

# Hikâye bölümlerinin eşyaları (Boncuk ve Arkadaşları)
ESYALAR = {
    "1faa5": "Toothbrush", "1f9e6": "Socks", "2602": "Umbrella", "1f34e": "Red apple", "1f319": "Crescent moon",
    "1f388": "Balloon", "1f9f8": "Teddy bear", "1f9fc": "Soap", "1f95b": "Glass of milk", "1f36a": "Cookie",
    "1fa81": "Kite", "1f382": "Birthday cake", "1f58d": "Crayon", "1f955": "Carrot", "2b50": "Star",
    "1f45f": "Running shoe", "1f381": "Wrapped gift", "1f9e9": "Puzzle piece", "1f353": "Strawberry",
    "1f366": "Soft ice cream", "1fae7": "Bubbles", "1f4d8": "Blue book", "1f9fa": "Basket", "1f308": "Rainbow",
    "1f34c": "Banana", "1f4a7": "Droplet", "1f9e2": "Billed cap", "2600": "Sun", "2764": "Red heart",
    "1f6cf": "Bed", "1f5d1": "Wastebasket", "1f33b": "Sunflower", "1f333": "Deciduous tree", "1f337": "Tulip",
}
ADLAR.update(ESYALAR)


def indir(url, hedef):
    if hedef.exists() and hedef.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            hedef.write_bytes(r.read())
        return True
    except Exception as e:  # noqa: BLE001
        print("HATA:", hedef.name, url, e)
        return False


if __name__ == "__main__":
    for kod, ad in ADLAR.items():
        dosya = ad.lower().replace(" ", "_")
        indir(FLUENT.format(urllib.parse.quote(ad), dosya), EMOJI / f"{kod}.png")
    indir(FONT_URL, KOK / "Baloo2.ttf")
    print("tamam:", len(list(EMOJI.glob("*.png"))), "görsel")
