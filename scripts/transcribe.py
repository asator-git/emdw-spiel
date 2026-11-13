#!/usr/bin/env python3
"""Stufe 1c: Folgen ohne YouTube-Untertitel lokal transkribieren (faster-whisper).
Aufruf:  transcribe.py [--shard K/N] [--model large-v3-turbo] [--push] [IDs...]
Schreibt data/transcripts/<id>.json  {id, source, model, segments:[{s,e,t}]}"""
import json, sys, os, subprocess, pathlib, time, argparse, tempfile, urllib.request
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data/transcripts'; OUT.mkdir(parents=True, exist_ok=True)

def todo(ids=None):
    E = json.loads((ROOT / 'data/episodes.json').read_text())
    # Folgen, die schon Kandidaten haben, brauchen kein Transkript mehr (öffentliches Repo enthält keine Transkripte)
    E = [e for e in E if e['in_game'] and not (ROOT / f"data/candidates/{e['id']}.json").exists()]
    if ids: E = [e for e in E if e['id'] in ids]
    return sorted(E, key=lambda e: e['date'])

def decode(url):
    with tempfile.TemporaryDirectory() as d:
        mp3 = os.path.join(d, 'a.mp3')
        req = urllib.request.Request(url, headers={'User-Agent': 'emdw-spiel-transcriber'})
        with urllib.request.urlopen(req, timeout=600) as r, open(mp3, 'wb') as f:
            while chunk := r.read(1 << 20): f.write(chunk)
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', mp3, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                             capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768

def git_push(msg):
    for i in range(6):
        subprocess.run(['git', 'add', str(OUT)], cwd=ROOT)
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0: return
        subprocess.run(['git', 'commit', '-qm', msg], cwd=ROOT)
        br = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        subprocess.run(['git', 'pull', '-q', '--rebase', '--autostash', 'origin', br], cwd=ROOT)
        if subprocess.run(['git', 'push', '-q', 'origin', br], cwd=ROOT).returncode == 0: return
        time.sleep(2 ** (i + 1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--shard', default='0/1'); ap.add_argument('--model', default='large-v3-turbo')
    ap.add_argument('--push', action='store_true'); ap.add_argument('ids', nargs='*')
    a = ap.parse_args()
    k, n = map(int, a.shard.split('/'))
    eps = [e for i, e in enumerate(todo(set(a.ids) or None)) if i % n == k and not (OUT / f"{e['id']}.json").exists()]
    print(f'{len(eps)} Folgen in Shard {a.shard}', flush=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=os.cpu_count())
    for e in eps:
        if (OUT / f"{e['id']}.json").exists(): continue
        t = time.time()
        try:
            audio = decode(e['audio'])
            segs, info = model.transcribe(audio, language='de', beam_size=1, vad_filter=True,
                                          initial_prompt='Erklär mir die Welt, ein Podcast von Andreas Sator. Gast: ' + ', '.join(e['guests']))
            seg = [{'s': round(s.start, 1), 'e': round(s.end, 1), 't': s.text.strip()} for s in segs]
        except Exception as ex:
            print('FEHLER', e['id'], ex, flush=True); continue
        (OUT / f"{e['id']}.json").write_text(json.dumps({'id': e['id'], 'source': 'whisper', 'model': a.model, 'segments': seg}, ensure_ascii=False, separators=(',', ':')))
        print(f"{e['id']}  {e['duration']/60:.0f} min Audio in {(time.time()-t)/60:.1f} min", flush=True)
        if a.push: git_push(f"Transkript {e['id']} (whisper)")
