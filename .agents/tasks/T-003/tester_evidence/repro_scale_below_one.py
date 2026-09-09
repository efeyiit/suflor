"""Minimal, bagimsiz tekrar-uretim: round-trip iddiasi (dpi.py modul
docstring'i, "Round-trip kararliligi" basligi) dpi_scale in (0,1) icin
YANLIS. Kodun TEK validasyonu `dpi_scale <= 0` (dpi.py, logical_to_physical
ve physical_to_logical), yani 0 < dpi_scale < 1 GECERLI kabul ediliyor."""
from src.capture.dpi import logical_to_physical, physical_to_logical
from src.contracts.models import Rect

original = Rect(x=3, y=3, w=3, h=3, dpi_scale=0.5)
physical = logical_to_physical(original)   # ValueError firlatmiyor -- gecerli sayiliyor
recovered = physical_to_logical(physical)

print("orijinal :", original)
print("fiziksel :", physical)
print("geri-don :", recovered)
print("round-trip tutuyor mu:", recovered == original)
assert recovered != original, "beklenmedik: bu ornekte round-trip tuttu (bulgu revize edilmeli)"

# Sistematik olcum: (0,1) araligi genelinde basarisizlik orani
mismatches = 0
total = 0
for scale_hundredths in range(5, 100, 5):
    scale = scale_hundredths / 100.0
    for L in range(-50, 51):
        r = Rect(x=L, y=0, w=1, h=1, dpi_scale=scale)
        back = physical_to_logical(logical_to_physical(r))
        total += 1
        if back.x != L:
            mismatches += 1
print(f"\n(0,1) araliginda sistematik basarisizlik: {mismatches}/{total} ({100*mismatches/total:.1f}%)")
