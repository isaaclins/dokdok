#!/bin/bash
# One agent run in full isolation. Args: <scenario-dir> <run-name> <engine> <model>
# engine = claude | codex.  Copies the scenario's dump/ into a fresh workspace, points the agent's
# home + skills at private copies, runs the prompt headless, collects every produced docx (+PDF),
# the doctype built, lint, and the answer into eval/results/<scenario>/<run>/.
set -u
SCEN=$1; RUN=$2; ENGINE=$3; MODEL=$4
REPO=/Users/isaaclins/Projects/dokdok
W=/tmp/eval2/$(basename "$SCEN")/$RUN
OUT=$REPO/eval/results/$(basename "$SCEN")/$RUN
rm -rf "$W" "$OUT"; mkdir -p "$W/schule" "$W/home" "$OUT"
cp -r "$SCEN/dump/." "$W/schule/"
PROMPT=$(cat "$SCEN/_source/prompt.txt")
cd "$W"
start=$(date +%s)
if [ "$ENGINE" = claude ]; then
  DOKDOK_HOME="$W/home" claude -p --model "$MODEL" --plugin-dir "$REPO" --dangerously-skip-permissions --output-format text \
    "$PROMPT Alles liegt im Ordner schule/." < /dev/null > "$OUT/antwort.txt" 2>&1
else
  cp -r "$REPO/skills/dokdok" "$HOME/.codex/skills/dokdok" 2>/dev/null
  MODELFLAG=""; [ "$MODEL" != "default" ] && MODELFLAG="-m $MODEL"
  DOKDOK_HOME="$W/home" codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
    -c model_reasoning_effort=high -C "$W" $MODELFLAG \
    "$PROMPT Alles liegt im Ordner schule/. Read the dokdok skill at ~/.codex/skills/dokdok/SKILL.md and use the dokdok CLI to do this." < /dev/null > "$OUT/antwort.txt" 2>&1
fi
echo "exit=$? engine=$ENGINE model=$MODEL seconds=$(( $(date +%s) - start ))" >> "$OUT/antwort.txt"
# collect
find "$W" -path '*/out/*.docx' -not -name '.*' | while IFS= read -r f; do
  cp "$f" "$OUT/"; DOKDOK_HOME="$W/home" "$REPO/.venv/bin/python" -c "from pathlib import Path;from dokdok.render import docx_to_pdf;docx_to_pdf(Path('$OUT/$(basename "$f")'))" 2>>"$OUT/antwort.txt" || true
done
find "$W" -name doctype.yaml | head -1 | while IFS= read -r f; do
  d=$(dirname "$f"); mkdir -p "$OUT/doctype"; cp -r "$d/." "$OUT/doctype/" 2>/dev/null
  DOKDOK_HOME="$W/home" dokdok types lint "$d" > "$OUT/lint.txt" 2>&1
done
echo "done $RUN"
