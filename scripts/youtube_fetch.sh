#!/usr/bin/env bash
# Stufe 1a: Alle Videos des EMDW-Kanals auflisten und Metadaten + deutsche Untertitel (nur Text) laden.
set -u
cd "$(dirname "$0")/../data/raw/yt"
CH="https://www.youtube.com/channel/UC_LB0SQVBGlPufgEZMd_ryA/videos"
yt-dlp --flat-playlist --print "%(id)s" "$CH" > ../yt_ids.txt
echo "$(wc -l < ../yt_ids.txt) Videos im Kanal"
while read -r id; do
  [ -f "$id.info.json" ] && { ls "$id".de*.json3 >/dev/null 2>&1 || [ -f "$id.nosubs" ]; } && continue
  yt-dlp --skip-download --write-info-json --no-write-playlist-metafiles \
    --write-subs --write-auto-subs --sub-langs "de-orig,de-DE,de" --sub-format json3 \
    --sleep-subtitles 1 -o "%(id)s.%(ext)s" "https://www.youtube.com/watch?v=$id" >/dev/null 2>>../yt_errors.log
  ls "$id".de*.json3 >/dev/null 2>&1 || touch "$id.nosubs"
  # trim info.json (Formate brauchen wir nicht)
  python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));json.dump({k:d.get(k) for k in ('id','title','upload_date','duration','description','chapters')},open(p,'w'),ensure_ascii=False)" "$id.info.json" 2>/dev/null
  sleep 1
done < ../yt_ids.txt
echo fertig
