# 骨架完备性倒查：成品月历 vs 抓取产物（{month}_out/）。
# 交付前必跑。核心思想：机械倒查必须带"排除规则层"，否则合法不收的帖子全变假警报。
# 四分类输出：❌疑似真漏（必须补）/ ⚠️待人工判断 / 🔀跨月或他月归档 / ⚪合法未收。
# 覆盖链路：本人(sync.json + mat_1292500037)、工作室、汇总号、栎迷会、栎亮鑫球、机场(air_*.json)。
# 汇总号滞后/机场考古帖会自动去成品目录其他月份里找归属。
# 用法: python -X utf8 check_skeleton.py <month_out_dir> <calendar_txt> [成品目录]
# 退出码：有 ❌ 疑似真漏则 1。
import json, re, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT, CAL = sys.argv[1], sys.argv[2]
CALDIR = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.expanduser('~'), 'Desktop', 'KA-calendar')

def ids_in(path):
    return set(re.findall(r'weibo\.com/\d+/(\w+)', open(path, encoding='utf-8').read()))

cal_ids = ids_in(CAL)
other = {}
for f in glob.glob(os.path.join(CALDIR, '2026-*.txt')):
    if os.path.abspath(f) == os.path.abspath(CAL):
        continue
    for iid in ids_in(f):
        other.setdefault(iid, os.path.basename(f))

m = re.search(r'2026-(\d{2})', os.path.basename(CAL))
TM = int(m.group(1)) if m else 0

def load(name):
    p = os.path.join(OUT, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

RE_ZHINAN = re.compile(r'赏栎指南')
RE_BANG = re.compile(r'向全世界安利|打call|签到|排名|投票|🧱🍎👍|升Key|打榜|助力')
RE_HUODONG = re.compile(r'转发评论此条微博|随机抽取|号外号外|专场|抽奖')
RE_EVENTDATE = re.compile(r'(\d{2})//(\d{2})//(\d{2})|(20\d{2})(\d{2})(\d{2})')
# 评论区回复/语音回复/翻牌类素材：format-rules 特殊处理规定走「我要抱着月亮睡觉」整理贴，
# 同步博自己的对应存档帖不必再挂，属合法未收
RE_COMMENT = re.compile(r'语音回复|语音翻牌|评论区|翻牌存档|空降')

buckets = {'miss': [], 'judge': [], 'cross': [], 'legit': []}

def cls(src, it, must=False):
    iid = it.get('id', '')
    if not iid or iid in cal_ids:
        return
    if iid in other:
        buckets['cross'].append((src, iid, it, f'已在他月成品 {other[iid]}'))
        return
    text = (it.get('text') or '')
    rt = it.get('rt') or {}
    if RE_COMMENT.search(text):
        buckets['legit'].append((src, iid, it, '评论区/翻牌类，走月亮整理贴')); return
    if must:
        buckets['miss'].append((src, iid, it, ''))
        return
    if RE_ZHINAN.search(text):
        buckets['legit'].append((src, iid, it, '赏栎指南（规则不收）')); return
    # 打榜/安利排除只适用于栎迷会、栎亮鑫球——汇总号/机场帖的话题头（#向全世界安利王栎鑫#）是固定格式，不能据此排除
    if src in ('栎迷会', '栎亮鑫球') and RE_BANG.search(text):
        buckets['legit'].append((src, iid, it, '打榜/安利类（规则不收）')); return
    if RE_HUODONG.search(text):
        buckets['judge'].append((src, iid, it, '活动/抽奖类')); return
    rttext = rt.get('text') or ''
    if rttext and '不可见' in rttext and len(text) <= 15:
        buckets['legit'].append((src, iid, it, '转发隐藏博，内容归💌链')); return
    em = RE_EVENTDATE.search(text)
    if em:
        if em.group(2):
            mm = int(em.group(2))
        else:
            mm = int(em.group(5))
        if TM and mm != TM:
            buckets['cross'].append((src, iid, it, f'考古帖（事件日属 {mm:02d} 月）')); return
    buckets['judge'].append((src, iid, it, ''))

# 本人：近月份读 mat_1292500037，半年可见期外读 sync.json，两者都是必收
for it in load('mat_1292500037.json'):
    cls('本人(1292500037)', it, must=True)
for it in load('sync.json'):
    cls('本人(同步博)', it, must=True)
# 工作室：必收（预告类漏了就是缺漏）
for it in load('mat_5934487143.json'):
    cls('工作室', it, must=True)
# 汇总号：滞后发帖属他月，先查他月成品；都查不到落"待人工判断"
for it in load('mat_7868703091.json'):
    cls('汇总号', it)
# 栎迷会 / 栎亮鑫球：大量合法排除，走分类
for it in load('mat_5691255041.json'):
    cls('栎迷会', it)
for it in load('mat_2796315530.json'):
    cls('栎亮鑫球', it)
# 机场：出发/到达/上下班该收，考古帖归他月，转发隐藏博归💌链
for f in sorted(glob.glob(os.path.join(OUT, 'air_*.json'))):
    for it in json.load(open(f, encoding='utf-8')):
        cls('机场', it)

def show(bucket, lines=200):
    for src, iid, it, note in buckets[bucket][:lines]:
        dt = it.get('dt', '?')
        text = (it.get('text') or '').replace('\n', ' ')[:45]
        suffix = f'  [{note}]' if note else ''
        print(f'   {src} | {iid} | {dt} | {text}{suffix}')

print(f'== 骨架倒查：{OUT} vs {os.path.basename(CAL)} ==')
print(f'❌ 疑似真漏（本人/工作室必收项缺失，必须补）: {len(buckets["miss"])}')
show('miss')
print(f'⚠️ 待人工判断: {len(buckets["judge"])}')
show('judge', 60)
print(f'🔀 跨月/他月归档（不用补）: {len(buckets["cross"])}')
show('cross', 40)
print(f'⚪ 合法未收（规则排除）: {len(buckets["legit"])}')
sys.exit(1 if buckets['miss'] else 0)