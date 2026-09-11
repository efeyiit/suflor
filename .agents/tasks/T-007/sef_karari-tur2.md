# Şef Kararı — T-007, Tur 2

Tester turu 1: **A onay · B ret.** İkisinin de bulguları şef tarafından üretildi (`sef_dogrulama/sonda_tester_{A,B}.txt`). Kod doğru; üç ölçü boşluğu var, ikisi ürün-görünür.

## T2-1 · K3 terminatör kümesi altı noktanın dördünde ölçülüyor (BLOKE, Tester-B)

**ŞEF ÜRETTİ:** `_TERMINATORLER`'den `?` (U+003F) çıkarılınca **beş kabul komutu da yeşil** (210 / real_check TEMİZ / 1314). Gerçek modelle: "Are you ready? The village elder…" 1 parça → çıktı 27 karakter, "hazır" **yok** — KRT-1 Y1'in düzelttiği cümle-kaybı sınıfı, bu kez tek karakterlik sabitte. `！` (U+FF01) için aynı.

**Neden kör:** teslim testlerinde `?`/`！` hiç **ayırt edici** konumda değil (`what?!` → `!` böler; `c! e?` sonda; `A。？！` süzgeç yutar). §4.6/7: ölçü parametre uzayının her noktasında koşmalı — burada uzay altı işaret.

**DEĞİŞMEZ (K3, değişmedi):** `.!?。！？` altısının **her biri tek başına** cümle sonudur.
**ÖLÇÜ:** parametrize test, **altı nokta**: `f"A{t} B{t}"` → 2 parça, her `t` için. Ayrıca her terminatör için "tek başına, diğerleri yokken" ayırt edici bir fixture: `"A? B"` → 2 (yalnız `?` böler). Tester-B'nin yamalı testleri: mutasyonsuz 220 passed, K3-03/K3-05 ✗→✓ (B ölçtü; şef tur sonunda doğrular).

## T2-2 · Yalnız yer tutucudan oluşan cümle modele gidiyor (Tester-A K-1, ürün-görünür)

**ŞEF ÜRETTİ (gerçek model):** `{PLAYER}!` → "- Hayır, hayır. {PLAYER}"; `{0}!` → "- Hayır, hayır! {0}"; `{0}。` → "{0}♪". Süzgeç (`modele_gider`) harf/rakam arıyor; `{PLAYER}` içinde harf var. Oyun metninde hitap kalıbı çok yaygın.

**DEĞİŞMEZ (K3 süzgeci, keskinleştirildi):** parça, `segment.placeholders`'daki dizeler **çıkarıldıktan sonra** harf/rakam içermiyorsa modele gitmez, aynen geçer.
**ÖLÇÜ:** sahte motorla `{PLAYER}!` (`placeholders=("{PLAYER}",)`) → motora giden 0, çıktı `"{PLAYER}!"` aynen; `{PLAYER} is here.` → gider (pozitif kontrol); `placeholders=()` iken `{PLAYER}!` → **gider** (yer tutucu bildirilmediyse metin). `real_check` #4c: gerçek model `{PLAYER}!` → çıktı `"{PLAYER}!"`. Bayatlayacak teslim testleri A'nın verdict'inde adlı; implementer yeniden nişanlar.

## T2-3 · Keskinlik (Tester-B, bloke etmez, aynı turda)

1. K10 hata mesajı nöbetçisi: yalnız kaynak metin ölçülüyor; **motor çıktısı** da mesaja sızmamalı — 2 parametre satırı.
2. 7 pozitif kontrol sahte sağlayıcıda `match=` yok — bugün doğru sebeple düşüyor (B ölçtü) ama gelecekte başka sebeple düşüp "ateşliyor" sanılabilir; `match=` eklenir.

## Kapsam dışı (kayıt)
`FileNotFoundError→ModelMissingError` eşlemesi paketin K6(b) lafzından sert (K6-06 birim kapısında düşüyor — ölçü var); K4-02 (KR→JP belirteci) real_check'e görünmez (içerik kontrolü zayıf, birim kapısı görüyor); `translate/` dizininden `pytest .` → `src` import edilemiyor (conftest kökü eklemiyor — T-004'ün conftest'i ekliyordu; **şef** tur sonrası ekler); `Handler.handle` doğrudan çağrısı kanal ölçüsünde kör (erişilemez).

## Neden karar kırmızı takımına gitmiyor
Yeni değişmez yok; üç ölçü de tester tarafından kuruldu ve ayırt etme gücü ölçüldü; `src` değişikliği T2-2'nin tek satırı (davranış: yalnız-yer-tutucu parçayı modele göndermemek — Y2'nin doğal uzantısı). §4.6/9.

## Kabul komutları (tur 2)
Beş komut aynı. Beklenen: birim **210 + eklenenler**, tam takım aynı artış, düşen yok. **Şef ayrıca koşar:** `python .agents/tasks/T-007/tester_B/mutant_kiti.py K3-01 K3-02 K3-03 K3-04 K3-05 K3-06` (altısı da yakalanmalı) ve gerçek modelle `{PLAYER}!`.

## Tur 2 sonrası
Tester-B yeniden nişan alır. A koşmaz; şef A'nın takımını regresyon olarak koşar (T2-2 A'nın testlerinden bazılarını **bayatlatır** — A verdict'te adlandırdı; şef o kırıkları bekler, dördüncüsü regresyondur).
