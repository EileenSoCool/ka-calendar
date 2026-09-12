# 同步博链完整性自检：折叠/改写月历后必跑
# 用法: python -X utf8 check_sync_links.py <calendar_txt> <sync_map.json>
# 原理：sync_map.json 里每条 wang_id 都应有对应 sync_id；
#       检查 wang 链在而 sync 链丢的条目（折叠脚本曾吞过这种链接）。
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cal_path, map_path = sys.argv[1], sys.argv[2]
text = open(cal_path, encoding='utf-8').read()
pairs = json.load(open(map_path, encoding='utf-8'))

missing = 0
for p in pairs:
    w, s = p.get('wang_id'), p.get('sync_id')
    if not s:
        continue
    if f'1292500037/{w}' in text and f'7796348707/{s}' not in text:
        print(f'缺同步博链: wang {w} 在, sync {s} 丢了')
        missing += 1

if missing == 0:
    print(f'OK: {cal_path} 同步博链完整（{sum(1 for p in pairs if p.get("sync_id"))} 对）')
else:
    print(f'共缺 {missing} 条同步博链，需人工补回')
    sys.exit(1)
