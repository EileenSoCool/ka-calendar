# base62 mid 解析：直接调 weibo.com/ajax/statuses/show?id=<mid>（接口原生支持 base62，无需自研转换）
# 用法: python -X utf8 mid_lookup.py <COOKIE_FILE> <mid1> [mid2 ...]
# 输出每条的 数字id / 时间 / 前60字正文。需要当季 SUB cookie（一次性，不入库）。
import json, urllib.request, http.cookiejar, re, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUB = open(sys.argv[1], encoding='utf-8').read().strip().lstrip('SUB=')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
cj = http.cookiejar.CookieJar()
cj.set_cookie(http.cookiejar.Cookie(0,'SUB',SUB,None,False,'.weibo.com',True,True,'/',True,False,None,False,None,None,None))
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent',UA),('Referer','https://weibo.com/')]

for mid in sys.argv[2:]:
    try:
        r = json.loads(op.open(f'https://weibo.com/ajax/statuses/show?id={mid}', timeout=20).read().decode('utf-8','replace'))
        txt = re.sub(r'<[^>]+>','', r.get('text_raw') or r.get('text') or '')
        print(f"{mid} -> id={r.get('idstr')} | {r.get('created_at')} | {txt[:60]}")
    except Exception as e:
        print(f"{mid} -> ERROR {type(e).__name__}")
    time.sleep(2)
