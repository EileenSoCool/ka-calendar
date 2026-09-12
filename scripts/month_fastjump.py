# 老月份（3 个月前）全量抓取：先深跳探针（p40/p80/p120）看最早日期，再二分定位到目标月起始页，
# 从该页往下翻，避免从 page1 慢翻几十页。账号清单与 month_mega.py / references/sources.md 完全一致。
# 产物文件名与 month_mega.py 完全一致（sync.json / mat_*.json / air_*.json / src_*.json），
# 下游 match_sync.py、extract_candidates.py、"读产物重做"流程可直接复用。
# 用法: python -X utf8 month_fastjump.py <YYYY> <MM> <COOKIE_FILE> <OUTDIR>
# COOKIE_FILE: 单行 SUB=... 的文本（用户每次现场提供，绝不入库记忆）。后台运行。
import json, time, urllib.request, http.cookiejar, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TY, TM = int(sys.argv[1]), int(sys.argv[2])
SUB = open(sys.argv[3], encoding='utf-8').read().strip().lstrip('SUB=')
OUT = sys.argv[4]; os.makedirs(OUT, exist_ok=True)

# 账号清单 —— 与 month_mega.py / references/sources.md 保持一致，禁止脑补
SYNC = '7796348707'
DIRECT = ['1292500037','5934487143','7868703091','5691255041','2796315530']
AIRPORT = ['7833056725','7914191225','3653524287','8001979691','7798345350']
SOURCES_RT = ['1805808602','7570474630','5284633100','7909783829','5955286705','7452679493','7276365067']

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def parse_created(s):
    m = re.match(r'\w+\s+(\w+)\s+(\d+)\s+([\d:]+)\s+\+\d+\s+(\d+)', s)
    if not m: return None
    mon = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    return (int(m.group(4)), mon.get(m.group(1),0), int(m.group(2)), m.group(3))

def clean(t):
    if not t: return ''
    t = re.sub(r'<[^>]+>','',t); t = re.sub(r'https?://\S+','',t)
    return t.replace('\n',' ').strip()

cj = http.cookiejar.CookieJar()
cj.set_cookie(http.cookiejar.Cookie(0,'SUB',SUB,None,False,'.weibo.com',True,True,'/',True,False,None,False,None,None,None))
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent',UA),('Referer','https://weibo.com/'),('X-Requested-With','XMLHttpRequest')]

def fetch(url):
    for a in range(3):
        try:
            with op.open(url, timeout=25) as r: return json.loads(r.read().decode('utf-8','replace'))
        except Exception as e:
            print(f'    err {a+1}: {type(e).__name__}', flush=True); time.sleep(20)
    return None

def page_earliest(uid, page):
    # 探针只看"最早日期"，必须跳过置顶帖（isTop），否则 2025 年的置顶会把最早日期拉飞
    j = fetch(f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0')
    if not j or j.get('ok')!=1: return None, None
    lst = j.get('data',{}).get('list',[]) or []
    earliest = None
    for it in lst:
        if it.get('isTop'): continue
        c = parse_created(it.get('created_at',''))
        if c:
            k=(c[0],c[1],c[2])
            if not earliest or k<earliest: earliest=k
    return earliest, lst

NEXT = (TY+1, 1, 1) if TM == 12 else (TY, TM+1, 1)

def find_start_page(uid):
    anchors = [40, 80, 120]
    lo = 1; hi = None
    for a in anchors:
        e, lst = page_earliest(uid, a)
        print(f'  probe p{a}: earliest~{e}', flush=True); time.sleep(9)
        if not lst: hi = a; break
        if e and e < NEXT: hi = a; break
        lo = a
    if hi is None: hi = 160
    while hi - lo > 1:
        mid = (lo+hi)//2
        e2, lst2 = page_earliest(uid, mid)
        print(f'  bin p{mid}: earliest~{e2}', flush=True)
        if (not lst2) or (e2 and e2 < NEXT): hi = mid
        else: lo = mid
        time.sleep(9)
    return hi

def collect(it):
    # 与 month_mega.py 完全一致的字段结构，保证下游脚本兼容
    rt = it.get('retweeted_status')
    return {'id': it.get('idstr') or str(it.get('id','')),
        'dt': None,  # 由调用处填
        'text': clean(it.get('text_raw') or it.get('text'))[:180],
        'rt': (lambda r: {'uid':str((r.get('user') or {}).get('id','')),
            'uname':(r.get('user') or {}).get('screen_name',''),
            'id':r.get('idstr') or str(r.get('id','')),
            'text':clean(r.get('text_raw') or r.get('text'))[:100]} if r else None)(rt)}

def walk(uid, out):
    start = find_start_page(uid)
    print(f'  {uid} -> walk from p{start}', flush=True)
    results, page, past = [], start, 0
    while page <= start + 75:
        j = fetch(f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0')
        if not j or j.get('ok')!=1: print(f'  p{page} stop', flush=True); break
        lst = j.get('data',{}).get('list',[]) or []
        if not lst: break
        earliest = None
        for it in lst:
            c = parse_created(it.get('created_at',''))
            if not c: continue
            y,mo,d,tm = c
            if y==TY and mo==TM:
                rec = collect(it); rec['dt'] = f'{mo:02d}-{d:02d} {tm}'
                results.append(rec)
            # 置顶帖不参与 earliest/past 统计（其旧日期会污染翻页终止判断）
            if it.get('isTop'): continue
            if (y==TY and mo<TM) or (y<TY): past += 1
            k = (y,mo,d)
            if not earliest or k < earliest: earliest = k
        print(f'  {uid} p{page}: hit={len(results)} earliest~{earliest}', flush=True)
        if earliest and (earliest[0]<TY or earliest[1]<TM) and past>40: break
        page += 1; time.sleep(9)
    json.dump(results, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'saved {out}: {len(results)}', flush=True)

walk(SYNC, os.path.join(OUT,'sync.json')); time.sleep(15)
for uid in DIRECT:
    walk(uid, os.path.join(OUT,f'mat_{uid}.json')); time.sleep(15)
for uid in AIRPORT:
    walk(uid, os.path.join(OUT,f'air_{uid}.json')); time.sleep(15)
for uid in SOURCES_RT:
    walk(uid, os.path.join(OUT,f'src_{uid}.json')); time.sleep(15)
print('ALL DONE', flush=True)