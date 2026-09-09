"""Ajan raporu şema doğrulayıcı.

Orkestra şefi bir raporu OKUMADAN ÖNCE bunu çalıştırır. Geçmeyen rapor
teslim sayılmaz ve içeriğine bakılmaz. Amaç: biçimsel olarak bozuk veya
kanıtsız bir cevabın kapıdan geçememesi.

Kullanım:
    python .agents/validate.py .agents/tasks/T-001/delivery.md
    python .agents/validate.py .agents/tasks/T-001/verdict.md

Çıkış kodu 0 = kabul edilebilir, 1 = reddedildi.
"""
from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("HATA: PyYAML kurulu degil -> python -m pip install pyyaml")
    sys.exit(2)

REPO = Path(__file__).resolve().parent.parent

REQUIRED = {
    "implementer": ["task", "role", "round", "status", "files_written", "commands"],
    "tester": ["task", "role", "round", "decision", "checks"],
}
VALID_STATUS = {"tamamlandi", "kismi", "bloke"}
VALID_DECISION = {"onay", "ret"}


def fail(errors: list[str]) -> None:
    print("REDDEDILDI\n")
    for e in errors:
        print(f"  - {e}")
    print(f"\n{len(errors)} ihlal. Rapor okunmadan reddedildi.")
    sys.exit(1)


def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail([f"{path.name}: YAML on bilgi yok (dosya '---' ile baslamali)"])
    parts = text.split("---", 2)
    if len(parts) < 3:
        fail([f"{path.name}: YAML on bilgi kapatilmamis (ikinci '---' eksik)"])
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail([f"{path.name}: YAML ayristirilamadi -> {exc}"])
    if not isinstance(data, dict):
        fail([f"{path.name}: on bilgi bir sozluk degil"])
    return data


def load_owns(task_id: str) -> list[str]:
    packet = REPO / ".agents" / "tasks" / task_id / "packet.md"
    if not packet.exists():
        return []
    try:
        data = parse_front_matter(packet)
    except SystemExit:
        return []
    return data.get("owns") or []


def check_evidence(entries: list, kind: str, task_dir: Path, errors: list[str]) -> None:
    """Her komut/kontrol icin kanit dosyasi gercekten var ve dolu mu."""
    if not entries:
        errors.append(f"{kind} listesi bos - kanitsiz teslim kabul edilmez")
        return
    for i, item in enumerate(entries):
        tag = f"{kind}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{tag}: sozluk degil")
            continue
        if "cmd" not in item:
            errors.append(f"{tag}: 'cmd' alani yok")
        if "exit_code" not in item:
            errors.append(f"{tag}: 'exit_code' alani yok")
        ev = item.get("evidence")
        if not ev:
            errors.append(f"{tag}: 'evidence' alani yok - hangi dosyada kanit var?")
            continue
        ev_path = task_dir / ev if not Path(ev).is_absolute() else Path(ev)
        if not ev_path.exists():
            errors.append(f"{tag}: kanit dosyasi diskte YOK -> {ev}")
        elif ev_path.stat().st_size == 0:
            errors.append(f"{tag}: kanit dosyasi BOS -> {ev}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    path = Path(sys.argv[1]).resolve()
    if not path.exists():
        fail([f"dosya yok: {path}"])

    task_dir = path.parent
    data = parse_front_matter(path)
    errors: list[str] = []

    role = data.get("role")
    if role not in REQUIRED:
        fail([f"'role' gecersiz: {role!r} (implementer veya tester olmali)"])

    for field in REQUIRED[role]:
        if field not in data:
            errors.append(f"zorunlu alan eksik: '{field}'")

    if role == "implementer":
        if data.get("status") not in VALID_STATUS:
            errors.append(f"'status' gecersiz: {data.get('status')!r} -> {VALID_STATUS}")
        check_evidence(data.get("commands") or [], "commands", task_dir, errors)

        # Sahiplik ihlali: yazilan her dosya owns kapsaminda mi?
        owns = load_owns(str(data.get("task", "")))
        if owns:
            for f in data.get("files_written") or []:
                norm = str(f).replace("\\", "/")
                if not any(fnmatch.fnmatch(norm, pat.replace("\\", "/")) for pat in owns):
                    errors.append(f"SAHIPLIK IHLALI: '{f}' owns kapsaminda degil ({owns})")

    else:  # tester
        if data.get("decision") not in VALID_DECISION:
            errors.append(f"'decision' gecersiz: {data.get('decision')!r} -> {VALID_DECISION}")
        check_evidence(data.get("checks") or [], "checks", task_dir, errors)

        # Tester korlugu: delivery.md okunmus olamaz -> ret ise gerekce zorunlu
        if data.get("decision") == "ret" and not (data.get("blocking_issues") or []):
            errors.append("ret verildi ama 'blocking_issues' bos - gerekcesiz ret kabul edilmez")
        if data.get("decision") == "ret" and not (task_dir / "feedback.md").exists():
            errors.append("ret verildi ama feedback.md yazilmamis")

    if errors:
        fail(errors)

    print(f"KABUL EDILEBILIR  ({path.name}, rol={role}, tur={data.get('round')})")
    n = len(data.get("commands") or data.get("checks") or [])
    print(f"  {n} komut/kontrol, hepsinin kaniti diskte mevcut ve dolu")
    if role == "tester":
        print(f"  karar: {data.get('decision')}")
    else:
        print(f"  durum: {data.get('status')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
