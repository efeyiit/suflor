# Şef Kararı — T-008, Tur 2

Tester A **ret** · Tester B **ret** (aynı sınıf, bağımsız — sentetik OCR'sız). Şef gerçek OCR'la üretti: iki satırı kaplayan büyük etiket kutusu (konuşmacı portresi / 2× başlık) satır bölümlemesini kandırıyor — 11 kutu → **1 blok**, iki satırın kelimeleri iç içe → kelime-kelime çeviri geri geliyor (S3).

**Şefin hatası:** KRT-1 O2 bu sınıfı adlandırmıştı; paket `[ÖLÇÜLMÜYOR] (fixture yok)` bıraktı. Fixture 10 dakikalık işti; Tester-A üretti. "Ölçülmüyor" damgası, **ölçülebilir** bir sınıfı örtmek için kullanılamaz — §4.6/10'un öteki yüzü.

## T2-1 · Satır referansı = satırın EN KISA bloğu (BLOKE)

**DEĞİŞMEZ (K2 adım 3, düzeltildi):** Satır bölümlemede dikey örtüşme, satırın **ilk** bloğuyla değil, satırdaki **en kısa** blokla (bağ: ilk) ölçülür. Neden: uzun bir kutu (2× etiket) iki satıra sarkar; referans o olursa iki satır tek satır sayılır. En kısa blok gerçek satır yüksekliğini temsil eder.

**ÖLÇÜ:** (1) A'nın 6 ret testi (`tester_A/test_ret_a_uzun_kutu_koprusu.py`, gerçek geometri gömülü) — geçer; etiketsiz 3 pozitif kontrol geçer. (2) Aynı geometri **implementer'ın** test dosyasına da girer (A'nın dizinine yaslanılmaz). (3) `real_check` #1c: `tester_A/fixtures/kr_etiket_ortali_60_45_10.png` → şef `T-008/fixtures/etiket_kopru_KR.png` olarak alır; gerçek OCR 11 kutu → **2** blok, hiçbir blok `line_boxes` > 6. (4) Mevcut: 68/68, `real_check` diğer kontroller, tam takım.

**Şef kum havuzunda doğruladı (A'nın E prototipi):** mypy 0 · 68/68 · ret 6/6 · real_check TEMİZ · köprü 11 → 2 `[6,5]`.

**Bayatlayacaklar:** A'nın `_SINIF` etiketli 2 testi (mevcut bozuk davranışı sabitliyordu) — A yeniden nişanlar. Implementer'ın 68'inde bayatlayan **yok** (A ölçtü).

## T2-2 · K6 aynı-x çifti (Tester-B M41, küçük)
Satır içi sıralamada `(x, y, idx)` yerine `(x, idx)` kullanan mutant hiçbir fixture'da ayrışmıyor — aynı `x`'li iki kutu yok. Bir fixture: aynı satırda `x` eşit, `y` farklı iki kutu → çıktı sırası `y`'ye göre. B'nin hazır testi `tester_B/`de; implementer kendi dosyasına eşdeğerini yazar. Ayrıca teslimdeki `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla` uzun kutuyu ortaya koyuyor (erişilebilir geometriyi kaçırıyor) — sola alınır.

## T2-3 · Belge
Docstring K2 adım 3 metni; `[ÖLÇÜLMÜYOR] (fixture yok)` damgası **kaldırılır** (artık ölçülüyor); K6 cümlesi daraltılır (A: bağ çıktı anahtarında da doğuyor, ürün etkisi yok).

## Neden KRT yok
Yeni değişmez yok; K2 adım 3'ün referans seçimi değişiyor; ölçüyü A kurdu ve ayırt etme gücünü ölçtü, şef doğruladı. §4.6/9.

## Kabul
Beş komut aynı + `real_check` #1c. Tester-A yeniden nişan alır; B'nin tur 1 sonucu (gelince) T2 koduyla regresyon.
