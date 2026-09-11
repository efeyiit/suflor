"""Çeviri katmanı (`TranslationProvider` uygulamaları).

Katman 1 (yerel NMT): `local_nmt.LocalNmtProvider` (T-007). Paket başlatıcısı
bilinçli olarak boştur: alt modüller doğrudan içe aktarılır
(`from src.translate.local_nmt import LocalNmtProvider`), böylece paketin
içe aktarılması hiçbir çeviri kütüphanesine dokunmaz.
"""
