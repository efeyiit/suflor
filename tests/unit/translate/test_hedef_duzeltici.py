"""T-015 -- HedefDuzeltici K1-K5."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.translate.hedef_duzeltici import HedefDuzeltici

KURALLAR = {"Elder": "İhtiyar", "Marks": "Marcus", "Markos": "Marcus", "Eira": "Ayla", "Village Elder": "Köy İhtiyarı"}


@pytest.fixture
def d() -> HedefDuzeltici:
    return HedefDuzeltici(KURALLAR)


# ---------------------------------------------------------------- K1 kelime siniri + katlama
@pytest.mark.parametrize("metin, beklenen", [
    ("Elder Marcus", "İhtiyar Marcus"),
    ("elder marcus", "İhtiyar marcus"),                 # buyuk/kucuk duyarsiz; ikame oldugu gibi
    ("ELDER!", "İhtiyar!"),
    ("Elderberry", "Elderberry"),                       # kelime icinde degismez
    ("elders", "elders"),
    ("Marks'ın kılıcı", "Marcus'ın kılıcı"),            # kesme sinir, Turkce ek korunur
    ("Marks, Markos ve Eira", "Marcus, Marcus ve Ayla"),
    ("(Marks)", "(Marcus)"),
    ("Marks", "Marcus"),
    ("", ""),
    ("hiç kural yok", "hiç kural yok"),
])
def test_k1_kelime_sinirli_ikame(d: HedefDuzeltici, metin: str, beklenen: str) -> None:
    assert d.duzelt(metin) == beklenen


def test_k1_turkce_katlama_i_ve_noktali_i() -> None:
    d = HedefDuzeltici({"Işık": "Nur", "İhtiyar": "Yaşlı"})
    assert d.duzelt("ışık") == "Nur" and d.duzelt("IŞIK") == "Nur"
    assert d.duzelt("ihtiyar") == "Yaşlı" and d.duzelt("İHTİYAR") == "Yaşlı"
    # I/ı ile İ/i ayri: 'İşık' (noktali) 'Işık' kuralina uymaz
    assert d.duzelt("İşık") == "İşık"


# ---------------------------------------------------------------- K2 en uzun once, zincirlenmez, tekrar reddi
def test_k2_en_uzun_once(d: HedefDuzeltici) -> None:
    assert d.duzelt("The Village Elder came") == "The Köy İhtiyarı came"


def test_k2_zincirlenmez() -> None:
    d = HedefDuzeltici({"Marks": "Marcus", "Marcus": "MARKUS"})
    assert d.duzelt("Marks ve Marcus") == "Marcus ve MARKUS"   # Marks -> Marcus, bir daha Marcus -> MARKUS olmaz


@pytest.mark.parametrize("kurallar", [{"Elder": "a", "elder": "b"}, [("Marks", "x"), ("MARKS", "y")]])
def test_k2_tekrar_eden_kaynak_reddedilir(kurallar: object) -> None:
    with pytest.raises(ValueError, match="tekrar"):
        HedefDuzeltici(kurallar)  # type: ignore[arg-type]


# ---------------------------------------------------------------- K3 yukleme
def test_k3_dosyadan_anahtar_varsa_yukler_yoksa_bos(tmp_path: Path) -> None:
    yol = tmp_path / "çeviri" / "s.json"
    yol.parent.mkdir()
    yol.write_text(json.dumps({"terimler": [], "hedef_duzeltmeler": [{"kaynak": "Elder", "hedef": "İhtiyar"}]}, ensure_ascii=False), encoding="utf-8")
    d = HedefDuzeltici.dosyadan(yol)
    assert len(d) == 1 and d.duzelt("Elder Marcus") == "İhtiyar Marcus"
    yol.write_text(json.dumps({"terimler": []}), encoding="utf-8")
    bos = HedefDuzeltici.dosyadan(yol)
    m = "Elder Marcus"
    assert len(bos) == 0 and bos.duzelt(m) is m


@pytest.mark.parametrize("veri, mesaj", [
    ({"hedef_duzeltmeler": "x"}, "liste"),
    ({"hedef_duzeltmeler": [{"kaynak": "a"}]}, "hedef"),
    ({"hedef_duzeltmeler": [{"kaynak": "", "hedef": "b"}]}, "bos"),
    ({"hedef_duzeltmeler": [{"kaynak": " a", "hedef": "b"}]}, "bos"),
    ({"hedef_duzeltmeler": [{"kaynak": "a", "hedef": 3}]}, "str"),
    ([], "nesne"),
])
def test_k3_sema_redleri(tmp_path: Path, veri: object, mesaj: str) -> None:
    yol = tmp_path / "s.json"
    yol.write_text(json.dumps(veri), encoding="utf-8")
    with pytest.raises(ValueError, match=mesaj):
        HedefDuzeltici.dosyadan(yol)


def test_k3_demo_sozlugu_yuklenir() -> None:
    d = HedefDuzeltici.dosyadan(Path("demo/sozluk_ornek.json"))
    assert d.duzelt("Elder Marcus") == "İhtiyar Marcus"


# ---------------------------------------------------------------- K4 saflik, K5 butce
def test_k4_bos_kural_kimlik_ve_kurallar_kopya(d: HedefDuzeltici) -> None:
    bos = HedefDuzeltici()
    m = "Elder"
    assert bos.duzelt(m) is m and len(bos) == 0
    k = d.kurallar
    assert isinstance(k, dict) and "elder" in k
    k["yeni"] = "x"   # kopya; ic tablo degismez
    assert "yeni" not in d.kurallar


def test_k4_hepsini_duzelt(d: HedefDuzeltici) -> None:
    assert d.hepsini_duzelt(["Elder", "x", "Marks'a"]) == ["İhtiyar", "x", "Marcus'a"]


def test_k5_butce_1000_ceviri_50_kural() -> None:
    d = HedefDuzeltici({f"Kelime{i}": f"Sozcuk{i}" for i in range(50)})
    metinler = [f"Burada Kelime{i % 50} ve baska seyler var, Kelime{(i + 7) % 50}'nin yanında." for i in range(1000)]
    sureler = []
    for _ in range(5):
        t0 = time.perf_counter(); d.hepsini_duzelt(metinler); sureler.append((time.perf_counter() - t0) * 1000)
    assert min(sureler) < 20, f"en kucuk {min(sureler):.1f} ms"
    assert d.duzelt("Kelime7'nin") == "Sozcuk7'nin"
