"""Suflör — UI KABUĞU gösterimi (T-012): ürün kabuğu `src/ui` + gerçek bölge izleme bağlanır.

Çalıştır:  python demo/kabuk.py [sag|sol]

Sağ üstteki üç düğme (kullanıcı isteği, 11 Eylül 2026):
  ✕  Kapat        — uygulama tamamen kapanır (tepside kalıntı yok)
  ▾  Tepsiye al   — pencere gizlenir, uygulama sistem tepsisinde çalışır; tepsi ikonuna tık → geri gelir
  ◐  Kenara al    — masaüstünde pencere görünmez; ekran kenarında küçük YARIM DAİRE durur.
                    İmleç üstüne gelince açılır: "Anlık çeviri" ve "Bölge izle" seçenekleri.
                    Yarım daire dikeyde sürüklenebilir; sağ tık ya da paneldeki küçük düğme → ana pencere.

Kabuk (`src/ui`, T-012) pipeline bilmez; bu gösterim iki mod sinyalini bağlar:
  bolge_izle_istendi → T-005 seçim katmanı → IzlemePenceresi (canlı bölge görünümü, model yok)
  anlik_cevir_istendi → durum satırı (Snapshot modu sıradaki görev)
Hiçbir OCR/çeviri metni konsola yazılmaz.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets  # noqa: E402

from demo.bolge_izle import IzlemePenceresi, SecimKatmani  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.models import Rect  # noqa: E402
from src.ui.geometri import Kenar  # noqa: E402
from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.uygulama import calistir  # noqa: E402


def _bagla(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
    """`calistir`'ın çalıştırıcısı: kabuk sinyallerini gerçek bölge izlemeye bağlar, sonra `exec()`."""
    servis = CaptureService(MssBackend())
    pencereler: list[QtWidgets.QWidget] = []

    def bolge_izle() -> None:
        birlesim = union_bbox(servis.monitors)
        if birlesim is None:
            return
        katman = SecimKatmani(birlesim)

        def secildi(bolge: Rect) -> None:
            izleme = IzlemePenceresi(servis, bolge)
            izleme.resize(max(420, min(900, bolge.w)), max(220, min(560, bolge.h + 40)))
            izleme.show()
            pencereler.append(izleme)

        katman.secildi.connect(secildi)
        katman.show()
        katman.activateWindow()
        pencereler.append(katman)

    def anlik_cevir() -> None:
        pencere.goster()
        pencere.setWindowTitle("Suflör — Anlık çeviri (Snapshot modu) sıradaki görev")

    pencere.bolge_izle_istendi.connect(bolge_izle)
    pencere.anlik_cevir_istendi.connect(anlik_cevir)
    pencere.cikis_istendi.connect(lambda: [w.close() for w in pencereler])
    return app.exec()


def main() -> int:
    kenar = Kenar.SOL if (len(sys.argv) > 1 and sys.argv[1].lower() == "sol") else Kenar.SAG
    return calistir(sys.argv, kenar=kenar, calistirici=_bagla)


if __name__ == "__main__":
    raise SystemExit(main())
