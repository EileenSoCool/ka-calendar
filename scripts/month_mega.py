# 月抓取管线：同步博 + 直接源 + 机场 + 流水转发源，全部带 retweeted_status 溯源
# 用法: python -X utf8 month_mega.py <YYYY> <MM> <COOKIE_FILE> <OUTDIR>
# COOKIE_FILE: 单行 SUB=... 的文本（用户每次现场提供，绝不入库记忆）
# 后台运行（PowerShell run_in_background）。件间 9s、账号间 15s、报错退避 20s。
import json, time, urllib.request, http.cookiejar, re, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TY, TM = int(sys.argv[1]), int(sys.argv[2])
COOKIE_FILE, OUT = sys.argv[3], sys.argv[4]
os.makedirs(OUT, exist_ok=True)

SUB = open(COOKIE_FILE, encoding='utf-8').read().strip().lstrip('SUB=')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# 账号清单 —— 与 references/sources.md 保持一致，禁止脑补
SYNC = '7796348707'
DIRECT = ['1292500037','5934487143','7868703091','5691255041','2796315530','8454302872']
AIRPORT = ['7833056725','7914191225','3653524287','8001979691','7798345350']
SOURCES_RT = ['1805808602','7570474630','5284633100','7909783829','5955286705','7452679493','7276365067']

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
op.addheaders = [('User-Agent',UA),('Referer','https://weibo.com/'),('X-Requested-With','XMLHttpRequest'),('Accept','application/json')]

def fetch(url):
    for a in range(3):
        try:
            with op.open(url, timeout=25) as r: return json.loads(r.read().decode('utf-8','replace'))
        except Exception as e:
            print(f'    err {a+1}: {type(e).__name__}', flush=True); time.sleep(20)
    return None

def walk(uid, out, max_pages=60):
    results, page, past = [], 1, 0
    while page <= max_pages:
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
                rt = it.get('retweeted_status')
                results.append({'id': it.get('idstr') or str(it.get('id','')),
                    'dt': f'{mo:02d}-{d:02d} {tm}',
                    'text': clean(it.get('text_raw') or it.get('text'))[:180],
                    'rt': (lambda r: {'uid':str((r.get('user') or {}).get('id','')),
                        'uname':(r.get('user') or {}).get('screen_name',''),
                        'id':r.get('idstr') or str(r.get('id','')),
                        'text':clean(r.get('text_raw') or r.get('text'))[:100]} if r else None)(rt)})
            # 置顶帖不参与 earliest/past 统计（其旧日期会污染翻页终止判断）
            if it.get('isTop'): continue
            if (y==TY and mo<TM) or (y<TY): past += 1
            k = (y,mo,d)
            if not earliest or k < earliest: earliest = k
        print(f'  p{page}: hit={len(results)} earliest~{earliest}', flush=True)
        if earliest and (earliest[0]<TY or earliest[1]<TM) and past>40: break
        page += 1; time.sleep(9)
    json.dump(results, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)

print('== 同步博 ==', flush=True); walk(SYNC, os.path.join(OUT,'sync.json'), max_pages=20); time.sleep(15)
for uid in DIRECT:
    print(f'== 直接源 {uid} ==', flush=True); walk(uid, os.path.join(OUT,f'mat_{uid}.json'), max_pages=25); time.sleep(15)
for uid in AIRPORT:
    print(f'== 机场 {uid} ==', flush=True); walk(uid, os.path.join(OUT,f'air_{uid}.json'), max_pages=25); time.sleep(15)
for uid in SOURCES_RT:
    print(f'== 转发源 {uid} ==', flush=True); walk(uid, os.path.join(OUT,f'src_{uid}.json'), max_pages=60); time.sleep(15)
print('ALL DONE', flush=True)
