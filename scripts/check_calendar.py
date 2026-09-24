# 月历成品格式自检（lint）：交付前必跑。
# 抓这周真实翻过的车：半角日期、日期乱序、编号断裂/缺失、链接被空格切断、
# 链接格式异常、同步博缺💌、标题与链接粘连。
# 用法: python -X utf8 check_calendar.py <calendar_txt>
# 退出码：有 ❌ 错误则 1，仅警告则 0。
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FW = '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗'
fw2int = {c: i for i, c in enumerate(FW)}

path = sys.argv[1]
lines = open(path, encoding='utf-8').read().splitlines()

errors, warnings = [], []

date_re = re.compile(r'^([𝟎-𝟗]{4})(?=\s|$)')  # 日期行允许带注释后缀（如 "𝟎𝟐𝟏𝟔 除夕""𝟎𝟑𝟎𝟑 元宵节"）
item_re = re.compile(r'^([0-9])️⃣')
url_re = re.compile(r'https?://\S+')

prev_mmdd = 0
cur_date = None
block_items = []

def flush_block():
    global block_items
    if cur_date is None:
        return
    if not block_items:
        warnings.append(f'{cur_date} 空日期块（无条目，确认是否应删或待补）')
    else:
        expect = 1
        for ln_no, n in block_items:
            if n != expect:
                errors.append(f'L{ln_no} {cur_date} 编号断裂：期望 {expect}️⃣ 实际 {n}️⃣')
                expect = n
            expect += 1
    block_items = []

for i, raw in enumerate(lines, 1):
    s = raw.strip()
    # 半角日期（如 0109）：致命
    if re.match(r'^0[0-9]{3}$', s) or re.match(r'^[0-9]{4}$', s):
        errors.append(f'L{i} 半角日期：{s!r}（应为全角粗体 𝟎𝐗𝐗𝐗）')
        continue
    dm = date_re.match(s)
    if dm:
        flush_block()
        dstr = dm.group(1)
        mm = fw2int[dstr[0]] * 10 + fw2int[dstr[1]]
        dd = fw2int[dstr[2]] * 10 + fw2int[dstr[3]]
        if not (1 <= mm <= 12 and 1 <= dd <= 31):
            errors.append(f'L{i} 非法日期：{s}')
        mmdd = mm * 100 + dd
        if prev_mmdd and mmdd < prev_mmdd:
            errors.append(f'L{i} 日期乱序：{s} 排在前一个日期之后')
        prev_mmdd = mmdd
        cur_date = s
        continue
    m = item_re.match(s)
    if m:
        block_items.append((i, int(m.group(1))))
    elif cur_date and s and re.match(r'^[0-9][、．. ]', s):
        warnings.append(f'L{i} 疑似缺编号 emoji（如 "4 长沙出发"）：{s[:40]}')
    # 链接被空格切断（...3864940 3）：致命
    if re.search(r'weibo\.com/\d+/\d+ \d', raw):
        errors.append(f'L{i} 链接疑似被空格切断：{s[:60]}')
    # 链接格式校验（weibo.com 数字/base62 原链、t.cn 短链、v.douyin.com/小红书 用户贴的站外链均合法；
    # 链接允许带 ?query 和 #fragment 后缀）
    for u in url_re.findall(raw):
        core = u.split('?')[0].split('#')[0]
        if not (re.match(r'^https://weibo\.com/\d+/[A-Za-z0-9]+$', core)
                or re.match(r'^https?://t\.cn/[A-Za-z0-9]+$', core)
                or re.match(r'^https://v\.douyin\.com/[A-Za-z0-9_\-]+/?$', core)
                or re.match(r'^https?://(www\.)?(xiaohongshu|xhslink)\.com/\S+$', core)):
            errors.append(f'L{i} 链接格式异常：{u}')
    # 同步博缺💌：致命（裸链接行紧跟💌行是合法备份链，放行）
    if '7796348707' in raw and '💌' not in raw and not s.startswith('http'):
        errors.append(f'L{i} 同步博行缺 💌：{s[:50]}')
    # 本人链缺💌：警告（近月份本人原博行规范同💌）
    if '1292500037' in raw and '💌' not in raw and not s.startswith('http'):
        warnings.append(f'L{i} 本人原博行缺 💌：{s[:50]}')
    # 标题紧贴链接 / 链接粘后续标题：警告
    if re.search(r'[一-鿿）》」]https?://', raw):
        warnings.append(f'L{i} 标题与链接间缺空格：{s[:50]}')
    if re.search(r'weibo\.com/\d+/[A-Za-z0-9]+[一-鿿]', raw):
        warnings.append(f'L{i} 链接与后续标题粘连：{s[:50]}')

flush_block()

print(f'== {path} 格式自检 ==')
for e in errors:
    print(' ❌', e)
for w in warnings:
    print(' ⚠️', w)
print(f'错误 {len(errors)}，警告 {len(warnings)}')
sys.exit(1 if errors else 0)