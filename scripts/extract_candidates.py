# 转发源月物料提取：关键词过滤 + 转发全量溯源到原博主，按日分组
# 用法: python -X utf8 extract_candidates.py <OUTDIR>  (读取 OUTDIR/src_*.json，产出 candidates.txt)
import json, re, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = sys.argv[1]
SOURCES = {'1805808602':'苦瓜','7570474630':'大佬的走姿','5284633100':'猪oo猪zzz',
           '7909783829':'我到底睡不睡啊','5955286705':'我要抱着月亮睡觉',
           '7452679493':'吃水果捞大赛第一名','7276365067':'caesocute'}

KW = re.compile(r'(王栎鑫|天赐|快乐老友记|你好星期六|我不哭|傻鱼|傻女|第三人称|势界|珠江|citylive|暴走|Flowers|董事长|法老|生于未来|郑州|广州|南京|生日会|鑫想室成|国乐无双|大眼音乐节|春晚|🌻)')

out = {}
for f in glob.glob(os.path.join(OUT, 'src_*.json')):
    uid = os.path.basename(f)[4:-5]
    tag = SOURCES.get(uid, uid)
    for p in json.load(open(f, encoding='utf-8')):
        t = p['text'] or ''
        rttext = (p.get('rt') or {}).get('text','')
        if not (KW.search(t) or KW.search(rttext)): continue
        rt = p.get('rt')
        if rt and rt.get('uid') and rt['uid'] != '0':
            link = f"https://weibo.com/{rt['uid']}/{rt['id']}"; src = f"{rt['uname']}(原)"
        else:
            link = f"https://weibo.com/{uid}/{p['id']}"; src = f"{tag}(原)"
        out.setdefault(p['dt'][:5], []).append((src, link, (rttext if rt else t)[:70]))

with open(os.path.join(OUT,'candidates.txt'),'w',encoding='utf-8') as f:
    for d in sorted(out):
        f.write(f'## {d}\n')
        seen=set()
        for src, link, show in out[d]:
            if link in seen: continue
            seen.add(link)
            f.write(f'- [{src}] {show}\n  {link}\n')
        f.write('\n')
print('days:', len(out))
