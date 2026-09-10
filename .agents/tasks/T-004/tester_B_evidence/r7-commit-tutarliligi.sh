#!/bin/sh
# Kararin kabul satiri: "python -m pytest tests -q -> 822 passed, dusen yok".
# Bu, HEAD commit'inin TEMIZ bir checkout'unda dogru mu? Calisma agacinda
# T-005'in TAKIPSIZ src dosyalari VAR, bu yuzden yerelde gorunmuyor.
set -e
WT="$1"
rm -rf "$WT"
git worktree add --detach "$WT" HEAD >/dev/null 2>&1
echo "### commit: $(git rev-parse --short HEAD)  (TEMIZ CHECKOUT: $WT)"
echo
echo "### HEAD'de takipli mi?"
for f in src/capture/service.py src/capture/monitors.py \
         tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py; do
  if git cat-file -e "HEAD:$f" 2>/dev/null; then s="TAKIPLI"; else s="commit'te YOK"; fi
  printf '  %-42s %s\n' "$f" "$s"
done
echo
echo "### TEMIZ checkout'ta: python -m pytest tests -q"
( cd "$WT" && python -m pytest tests -q 2>&1 | tail -8 ) || true
echo
echo "### TEMIZ checkout'ta: T-004'un DARALTILMIS kapsami"
( cd "$WT" && python -m pytest tests/unit/ocr tests/unit/contracts \
    tests/unit/capture/test_dpi.py tests/unit/capture/test_change_detector.py -q 2>&1 | tail -2 ) || true
git worktree remove --force "$WT" >/dev/null 2>&1
git worktree prune
echo
echo "### worktree temizlendi; calisma agaci degistirilmedi."
