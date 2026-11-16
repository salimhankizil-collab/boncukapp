"""Boncuk ve Arkadaşları hikâyeleri. Her hikâye 30-45 sn: küçük bir sorun, çözüm, bir kelime (TR + EN), minik bir ders.

Vuruş alanları (hepsi isteğe bağlı):
  kim / soz   : konuşan karakter (boncuk, pamuk, minik) ve cümlesi
  zipla       : zıplayan karakterler
  ifade       : {"minik": "uzgun"}  (normal / mutlu / uzgun)
  yuru        : (karakter, hedef_x, süre)
  kos         : (karakter, [duraklar], adım süresi, topu_taşır)  kovalamaca
  dus         : karakter tökezleyip düşer
  yakin       : kamera bu karaktere yaklaşır (o vuruş boyunca)
  at          : (kimden, kime, yükseklik)  top bir karakterden diğerine uçar
  kart        : (Türkçe, İngilizce, renk)  ekranda büyük kelime kartı, Boncuk TR, arkadaşı EN söyler
  konfeti     : True
  ara         : konuşmadan sonra bekleme (sn)
"""

HIKAYELER = [
    {
        "kod": "top-kimin",
        "baslik": "Top Kimin?",
        "ders": "paylaşmak ve sırayla oynamak",
        "kelime": ("Top", "Ball"),
        "top": {"renk": (236, 58, 62), "yer": (360, 1392)},
        "baslangic": {"boncuk": {"x": 1260}},
        "vuruslar": [
            {"kim": "pamuk", "soz": "Ooo! Kocaman bir top!", "zipla": ["pamuk"]},
            {"kim": "minik", "soz": "Top! Benim!", "at": ("yer", "minik", 60), "ifade": {"minik": "mutlu"}},
            {"kim": "pamuk", "soz": "Hayır, benim! Yakala beni! Miyav!", "at": ("minik", "pamuk", 140),
             "kos": ("pamuk", [860, 560, 870, 500], 0.5, True), "ifade": {"minik": "normal", "pamuk": "mutlu"}},
            {"kim": "minik", "soz": "Dur! Dur!", "yuru": ("minik", 290, 0.5)},
            {"kim": "minik", "soz": "Ühü! Ühü! Topum!", "dus": "minik", "yakin": "minik",
             "ifade": {"minik": "uzgun", "pamuk": "normal"}, "ara": 0.2},
            {"kim": "boncuk", "soz": "Durun durun! Ağlamak yok!", "yuru": ("boncuk", 800, 0.55)},
            {"kim": "boncuk", "soz": "Hadi sırayla oynayalım!", "zipla": ["boncuk"]},
            {"kart": ("Top", "Ball", (236, 58, 62))},
            {"kim": "pamuk", "soz": "Al Minik, sıra sende!", "at": ("pamuk", "minik", 260), "ifade": {"minik": "mutlu"}},
            {"kim": "minik", "soz": "Agu! Daha!", "at": ("minik", "boncuk", 300)},
            {"kim": "boncuk", "soz": "Yakaladım! Hop, Pamuk'a!", "at": ("boncuk", "pamuk", 280), "ifade": {"pamuk": "mutlu"}},
            {"kim": "pamuk", "soz": "Paylaşınca daha eğlenceli!", "konfeti": True,
             "ifade": {"boncuk": "mutlu", "minik": "mutlu"}},
            {"kim": "minik", "soz": "Yaşasın!", "zipla": ["minik"], "ara": 0.5},
        ],
    },
]
