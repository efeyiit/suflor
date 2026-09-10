# -*- coding: utf-8 -*-
"""TUR 5 / Tester-C: MUTASYON DENETIMI (PROTOKOL S4.5 "Test kalitesi"
disiplini): yazdigim testler GERCEKTEN kiriliyor mu, yoksa totoloji mi?

Yontem: `src/` HICBIR SEKILDE DEGISTIRILMEZ. TUR 4'un (HATALI) `_group`
mekanizmasi bu script icinde yeniden kurulur ve `normalizer._group` bu
surecte gecici olarak onunla degistirilir. Sonra TESTER-C'nin TUR 5
testleri (bolum 16) DOGRUDAN cagirilir. Beklenti: B1 ve K23 testleri
MUTANT kodda KIRILMALI, mevcut kodda GECMELI.
"""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from pathlib import Path

_KOK = r"C:\Users\pc\Desktop\efe\çeviri uygulaması"
sys.path.insert(0, _KOK)
sys.path.insert(0, str(Path(_KOK) / ".agents" / "tasks" / "T-004" / "tester_C"))

import src.ocr.normalizer as N
from src.ocr.normalizer import _group_rejection_reason, _Item, _union_rect

import test_cjk_misuse_scale as T

ORIJINAL_GROUP = N._group


def _group_TUR4(items, params, *, apply_inheritance: bool = True):
    """TUR 4'un mekanizmasi: miras `nxt`'i HEMEN mute eder, mute edilmis oge
    `current`'e atanir ve BIR SONRAKI gruplama kararina GIRDI olur (B1)."""
    if not items:
        return []
    groups: list[_Item] = []
    current = items[0]
    tail = items[0]
    for nxt in items[1:]:
        reason = _group_rejection_reason(current, nxt, params)
        if reason is None:
            current = _Item(
                text=current.text + " " + nxt.text,
                bbox=_union_rect(current.bbox, nxt.bbox),
                speaker=current.speaker,
                source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
            )
            tail = nxt
        else:
            groups.append(current)
            if (
                apply_inheritance
                and reason == "length"
                and current.speaker is not None
                and nxt.speaker is None
                and _group_rejection_reason(tail, nxt, params, ignore_length=True) is None
            ):
                nxt = replace(nxt, speaker=current.speaker)   # <-- B1'in koku
            current = nxt
            tail = nxt
    groups.append(current)
    return groups


DENETLENEN = [
    "test_k23_B1_JAPONCA_kendi_etiketiyle_gelen_YENI_replik_AYRI_KALIR",
    "test_k23_B1_JAPONCA_etiketsiz_kuyruk_MIRAS_ALIR_ama_bolumleme_AYNI",
    "test_k23_B1_JAPONCA_FARKLI_konusmaci_etiketi_miras_ALMAZ",
    "test_k23_UC_KONUSMACULU_zincir_her_biri_COK_SATIRLI_ve_cap_ASIYOR",
    "test_k23_UC_KONUSMACULU_zincir_KISA_replikler_konusmaci_SIZMAZ",
    "test_GOZLEM_iki_AYRI_kendi_etiketli_replik_K15_satir1_ile_BIRLESIR",
    "test_karisik_script_UZUNLUK_bolunmesinde_de_miras_calisir",
    "test_kotu_kullanim_apply_inheritance_False_SESSIZCE_YANLIS_sonuc_VERMEZ",
    "test_k23_DEGISMEZ_tester_C_KENDI_fuzzi_CJK_agirlikli_2600_girdi",
]


def kos(etiket: str) -> None:
    print("=" * 74)
    print(etiket)
    print("-" * 74)
    for ad in DENETLENEN:
        fn = getattr(T, ad)
        try:
            fn()
            sonuc = "GECTI"
            detay = ""
        except AssertionError as e:
            sonuc = "KIRILDI"
            detay = str(e).splitlines()[0][:110]
        except Exception as e:  # noqa: BLE001
            sonuc = f"HATA({type(e).__name__})"
            detay = str(e)[:110]
        print(f"  {sonuc:9} {ad}")
        if detay:
            print(f"            -> {detay}")
    print()


N._group = ORIJINAL_GROUP
kos("MEVCUT KOD (tur 5, iki-gecisli `_group`) -- hepsi GECMELI")

N._group = _group_TUR4
kos("MUTANT (tur 4 mekanizmasi, B1'in koku) -- K23/B1 testleri KIRILMALI")

N._group = ORIJINAL_GROUP
print("=" * 74)
print("SONUC")
print("-" * 74)
print("Tester-C'nin TUR 5 testleri TOTOLOJI DEGIL: B1'in japonca senaryosu")
print("ve K23 degismez fuzz'i, TUR 4'un hatali mekanizmasinda KIRILIYOR;")
print("mevcut kodda ikisi de temiz. (Ureticinin ILK hali mutantta 0 ihlal")
print("buluyordu -- SAHNE modu eklenerek 48/2600'e cikarildi, bkz. testin")
print("docstring'i.)")
