# 王栎鑫当月帖 × 同步博配对：文本前20字归一匹配，产出 sync_map.json
# 用法: python -X utf8 match_sync.py <OUTDIR>   (读取 OUTDIR/mat_1292500037.json 和 sync.json)
import json, re, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = sys.argv[1]

def norm(t):
    t = re.sub(r'#([^#]+)#','',t or ''); t = re.sub(r'@\S+','',t); t = re.sub(r'\s+','',t)
    return t[:20]

wang = json.load(open(os.path.join(OUT,'mat_1292500037.json'), encoding='utf-8'))
sync = json.load(open(os.path.join(OUT,'sync.json'), encoding='utf-8'))

pairs = []
for w in sorted(wang, key=lambda x: x['dt']):
    wn = norm(w['text'])
    hit = next((s for s in sync if wn and wn in norm(s['text'])), None)
    pairs.append({'wang_id': w['id'], 'wang_dt': w['dt'], 'wang_text': w['text'][:60],
                  'sync_id': hit['id'] if hit else None})
    print(f"{w['dt']} | {w['id']} -> {hit['id'] if hit else 'NO MATCH'} | {w['text'][:36]}")

json.dump(pairs, open(os.path.join(OUT,'sync_map.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'matched {sum(1 for p in pairs if p["sync_id"])}/{len(pairs)}')
