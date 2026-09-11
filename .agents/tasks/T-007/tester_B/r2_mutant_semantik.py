"""TESTER-B tur 2 -- yeni mutantlarin SEMANTIK on-dogrulamasi (kit kosumundan once).

Her R2 mutanti ayna agacina uygulanir ve ayri surecte `cumlelere_bol` /
`modele_gider` sondalari kosulur: mutant gercekten amaclanan davranisi
uretiyor mu (ornegin `\\n` terminator oldu mu, `\\Z` dali gercekten dustu mu,
kontrol mutantlari gercekten ESDEGER mi)? Boylece kitte "kacti" gorunen bir
mutantin aslinda etkisiz (kit hatasi) olmadigi kanitlanir (tur 1 K3-07 dersi).

    TESTER_B_SCRATCH=<dizin> python .agents/tasks/T-007/tester_B/r2_mutant_semantik.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutant_kiti as MK  # noqa: E402

SONDA = r'''
import json, sys
sys.path.insert(0, ".")
from src.translate.local_nmt import cumlelere_bol, modele_gider
c = cumlelere_bol
out = {
  "A, B.": c("A, B."), "A; B.": c("A; B."), "A… B.": c("A… B."), "A， B.": c("A， B."), "A． B.": c("A． B."),
  "A\\nB.": c("A\nB."), "A": c("A"), "A。B": c("A。B"), "A\\n": c("A\n"), "A. B": c("A. B"),
  "Wait... what?!": c("Wait... what?!"), "A. 」 B.": c("A. 」 B."),
  "A.』 B.": c("A.』 B."), "A.） B.": c("A.） B."), "A.) B.": c("A.) B."), "A.\" B.": c("A.\" B."), "A.' B.": c("A.' B."),
  "A.” B.": c("A.” B."), "A.’ B.": c("A.’ B."), "A.» B.": c("A.» B."),
  "mg {PLAYER}! []": modele_gider("{PLAYER}!"), "mg {PLAYER}! [PLAYER]": modele_gider("{PLAYER}!", ("{PLAYER}",)),
  "mg {0} {1}! [0,1]": modele_gider("{0} {1}!", ("{0}", "{1}")), "mg {0}{0}! [0]": modele_gider("{0}{0}!", ("{0}",)),
  "mg %s! [%s]": modele_gider("%s!", ("%s",)), "mg <T0>! [<T0>]": modele_gider("<T0>!", ("<T0>",)),
  "mg {0}5! [0]": modele_gider("{0}5!", ("{0}",)), "mg {0} ç [0]": modele_gider("{0} ç", ("{0}",)),
  "mg {0}}! [0]": modele_gider("{0}}!", ("{0}",)), "mg {{0}! [0]": modele_gider("{{0}!", ("{0}",)),
  "mg {0} a {1} [0,1]": modele_gider("{0} a {1}", ("{0}", "{1}")), "mg ! ['']": modele_gider("!", ("",)),
  "mg 。。。": modele_gider("。。。"),
}
print(json.dumps(out, ensure_ascii=True))
'''

SECILEN = [m for m in MK.MUTANTLAR if m.mid.startswith("R2-") and m.dosya == MK.MOTOR]


def _sonda() -> dict[str, object]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", SONDA], cwd=str(MK.KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=120)
    if r.returncode != 0:
        return {"HATA": (r.stderr or "")[-400:]}
    return json.loads(r.stdout)  # type: ignore[no-any-return]


def main() -> None:
    MK._ayna_kur()
    taban = _sonda()
    print("TABAN (mutasyonsuz):")
    for k, v in taban.items():
        print(f"  {k!r:28s} -> {v!r}")
    print()
    for mut in SECILEN:
        MK._uygula(mut)
        try:
            son = _sonda()
        finally:
            MK._geri_al()
        fark = {k: (taban.get(k), son.get(k)) for k in set(taban) | set(son) if taban.get(k) != son.get(k)}
        etiket = "ESDEGER (sondada fark yok)" if not fark else f"{len(fark)} fark"
        if mut.kontrol and fark:
            etiket += "   *** KONTROL AMA FARK VAR ***"
        if not mut.kontrol and not fark:
            etiket += "   (sonda ayirt etmiyor -- kit sonucuna bak)"
        print(f"{mut.mid:10s} {etiket}")
        for k, (a, b) in sorted(fark.items()):
            print(f"    {k!r:28s} {a!r}  ->  {b!r}")


if __name__ == "__main__":
    main()
