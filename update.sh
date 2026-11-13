#!/usr/bin/env bash
# Hält das Spiel nach jeder neuen Folge aktuell:
#   RSS -> YouTube-Zuordnung/Untertitel -> Whisper für den Rest -> Claude-Pipeline (Batches) -> Kuratierung -> Deploy
# Voraussetzungen: python3, ffmpeg, pip install yt-dlp faster-whisper anthropic; ANTHROPIC_API_KEY gesetzt.
# Optional: DEPLOY_REMOTE (Standard: git@github.com:asator-git/emdw-spiel.git), SKIP_DEPLOY=1, SKIP_YOUTUBE=1
set -euo pipefail
cd "$(dirname "$0")"
step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

step "1/7 Folgenliste aus dem RSS-Feed"
python3 scripts/feed.py

step "2/7 YouTube: Kanalliste, Untertitel, Zuordnung"
if [ -z "${SKIP_YOUTUBE:-}" ]; then
  yt-dlp --flat-playlist --print "%(id)s	%(title)s	%(duration)s" \
    "https://www.youtube.com/channel/UC_LB0SQVBGlPufgEZMd_ryA/videos" > data/raw/yt_flat.tsv || echo "Kanalliste nicht erreichbar – weiter ohne"
  scripts/youtube_fetch.sh || echo "Untertitel teilweise nicht ladbar – Whisper übernimmt"
fi
python3 scripts/match_youtube.py
python3 scripts/yt_to_transcript.py

step "3/7 Whisper für Folgen ohne Untertitel"
python3 scripts/transcribe.py --model "${WHISPER_MODEL:-large-v3-turbo}"
python3 scripts/coverage.py

step "4/7 Stufe 1: Extraktion (Message Batches API)"
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "Kein ANTHROPIC_API_KEY. Ohne Schlüssel: Agent-Modus, siehe scripts/AGENT_WORKER.md"; exit 1
fi
python3 scripts/pipeline.py batch extract
python3 scripts/pipeline.py wait

step "5/7 Stufe 2: Prüfung (Message Batches API)"
python3 scripts/pipeline.py batch review
python3 scripts/pipeline.py wait

step "6/7 Stufe 3: Kuratierung + Tagesrunden"
python3 scripts/pipeline.py retime
python3 scripts/curate.py
python3 scripts/pipeline.py status

step "7/7 Deploy"
if [ -z "${SKIP_DEPLOY:-}" ]; then
  REMOTE="${DEPLOY_REMOTE:-git@github.com:asator-git/emdw-spiel.git}"
  TMP=$(mktemp -d); cp -r web/. "$TMP"; touch "$TMP/.nojekyll"
  ( cd "$TMP" && git init -q && git checkout -q -b gh-pages && git add -A && git commit -qm "Deploy $(date +%F)" && git push -qf "$REMOTE" gh-pages )
  rm -rf "$TMP"; echo "Deployt nach $REMOTE (Branch gh-pages)"
fi
