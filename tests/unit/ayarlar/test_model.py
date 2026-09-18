"""T-016 -- Ayarlar modeli ve deposu K1-K5."""
from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

import pytest

from src.ayarlar import Ayarlar, AyarlarDeposu, varsayilan_ayar_yolu


# ---------------------------------------------------------------- K1 model
def test_k1_varsayilanlar_ve_dondurulmus() -> None:
    a = Ayarlar()
    assert (a.dil, a.kisayol_anlik, a.kisayol_bolge, a.sozluk_yolu, a.kenar, a.baslangic, a.surum) == \
        ("auto", "Ctrl+Alt+D", "Ctrl+Alt+R", None, "sag", "gorunur", 1)   # T-018: varsayilan dil = algila
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.dil = "japan"  # type: ignore[misc]
    assert a.ile(dil="japan").dil == "japan" and a.dil == "auto"
    assert Ayarlar(dil="korean").dogrula() == [] and Ayarlar(dil="auto").dogrula() == []
    assert a.dogrula() == []


# ---------------------------------------------------------------- K2 dogrulama
@pytest.mark.parametrize("degisiklik, alan", [
    ({"dil": "klingon"}, "dil"),
    ({"kisayol_anlik": "T"}, "kisayol_anlik"),
    ({"kisayol_bolge": "Win+R"}, "kisayol_bolge"),
    ({"kisayol_bolge": "ctrl+alt+d"}, "kisayol_bolge"),          # ikisi ayni (buyuk/kucuk duyarsiz)
    ({"kenar": "ust"}, "kenar"),
    ({"baslangic": "gizli"}, "baslangic"),
    ({"sozluk_yolu": "  "}, "sozluk_yolu"),
])
def test_k2_dogrulama_alan_adiyla(degisiklik: dict[str, object], alan: str) -> None:
    sorunlar = Ayarlar().ile(**degisiklik).dogrula()
    assert sorunlar and all(s.startswith(alan + ":") for s in sorunlar), sorunlar


def test_k2_dogrulama_dosya_acmaz(tmp_path: Path) -> None:
    a = Ayarlar(sozluk_yolu=str(tmp_path / "yok.json"))
    assert a.dogrula() == []   # varlik calisma zamaninda denetlenir


# ---------------------------------------------------------------- K3 yukleme
def test_k3_dosya_yoksa_varsayilan(tmp_path: Path) -> None:
    s = AyarlarDeposu(tmp_path / "yok" / "ayarlar.json").yukle()
    assert s.ayarlar == Ayarlar() and s.sorunlar == []


@pytest.mark.parametrize("icerik", ["{bozuk", "[1,2]", "42", ""])
def test_k3_bozuk_json_varsayilan_ve_sorun(tmp_path: Path, icerik: str) -> None:
    yol = tmp_path / "a.json"; yol.write_text(icerik, encoding="utf-8")
    s = AyarlarDeposu(yol).yukle()
    assert s.ayarlar == Ayarlar() and s.sorunlar == ["json"]


def test_k3_bilinmeyen_alan_yok_sayilir_bilinen_hatali_alan_varsayilana(tmp_path: Path) -> None:
    yol = tmp_path / "a.json"
    yol.write_text(json.dumps({"dil": "japan", "kenar": "ust", "kisayol_anlik": 5, "gelecek_alan": True, "surum": 3}), encoding="utf-8")
    s = AyarlarDeposu(yol).yukle()
    assert s.ayarlar.dil == "japan" and s.ayarlar.kenar == "sag" and s.ayarlar.kisayol_anlik == "Ctrl+Alt+D" and s.ayarlar.surum == 3
    assert sorted(s.sorunlar) == ["kenar", "kisayol_anlik", "surum"]


def test_k3_ayni_iki_kisayol_ikincisi_varsayilana(tmp_path: Path) -> None:
    yol = tmp_path / "a.json"
    yol.write_text(json.dumps({"kisayol_anlik": "Ctrl+Alt+X", "kisayol_bolge": "ctrl+alt+x"}), encoding="utf-8")
    s = AyarlarDeposu(yol).yukle()
    assert (s.ayarlar.kisayol_anlik, s.ayarlar.kisayol_bolge) == ("Ctrl+Alt+X", "Ctrl+Alt+R") and "kisayol_bolge" in s.sorunlar


def test_k3_sozluk_yolu_null_ve_str(tmp_path: Path) -> None:
    yol = tmp_path / "a.json"
    yol.write_text(json.dumps({"sozluk_yolu": None}), encoding="utf-8")
    assert AyarlarDeposu(yol).yukle().ayarlar.sozluk_yolu is None
    yol.write_text(json.dumps({"sozluk_yolu": "C:/x/sözlük.json"}), encoding="utf-8")
    assert AyarlarDeposu(yol).yukle().ayarlar.sozluk_yolu == "C:/x/sözlük.json"
    yol.write_text(json.dumps({"sozluk_yolu": 7}), encoding="utf-8")
    s = AyarlarDeposu(yol).yukle()
    assert s.ayarlar.sozluk_yolu is None and s.sorunlar == ["sozluk_yolu"]


# ---------------------------------------------------------------- K4 kaydetme
def test_k4_kaydet_yukle_gidis_donus_dizin_yaratir_utf8(tmp_path: Path) -> None:
    yol = tmp_path / "çeviri" / "Suflor" / "ayarlar.json"
    depo = AyarlarDeposu(yol)
    a = Ayarlar(dil="japan", kisayol_anlik="Ctrl+Shift+F5", sozluk_yolu="D:/oyun/sözlük.json", kenar="sol", baslangic="tepsi")
    depo.kaydet(a)
    assert depo.yukle().ayarlar == a and depo.yukle().sorunlar == []
    ham = yol.read_text(encoding="utf-8")
    assert "sözlük" in ham and "\\u00" not in ham   # ensure_ascii=False (kacis yok)
    assert not yol.with_suffix(".json.tmp").exists()


def test_k4_gecersiz_ayar_kaydedilmez(tmp_path: Path) -> None:
    depo = AyarlarDeposu(tmp_path / "a.json")
    depo.kaydet(Ayarlar())
    with pytest.raises(ValueError, match="dil"):
        depo.kaydet(Ayarlar(dil="klingon"))
    assert depo.yukle().ayarlar == Ayarlar()   # eski dosya duruyor


def test_k4_atomik_yazma_yarim_dosya_birakmaz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    depo = AyarlarDeposu(tmp_path / "a.json")
    depo.kaydet(Ayarlar(dil="english"))

    def patlayan_replace(*_: object) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(os, "replace", patlayan_replace)
    with pytest.raises(OSError):
        depo.kaydet(Ayarlar(dil="japan"))
    assert depo.yukle().ayarlar.dil == "english"   # hedef dosya bozulmadi


# ---------------------------------------------------------------- yol
def test_varsayilan_yol_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert varsayilan_ayar_yolu() == tmp_path / "Suflor" / "ayarlar.json"
    monkeypatch.delenv("APPDATA")
    assert varsayilan_ayar_yolu().name == "ayarlar.json" and ".suflor" in str(varsayilan_ayar_yolu())
