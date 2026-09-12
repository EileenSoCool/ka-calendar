# t.cn 短链还原器：把月历里的 t.cn 短链批量解析回 weibo.com/{uid}/{idstr} 原链。
# 用途有二：
#   1) 产出 .resolved.txt 供 check_skeleton 核对（t.cn 无法直接匹配骨架 id）
#   2) 用户找不到原链时，可用 --write 直接把成品里的 t.cn 还原成原链
# 原理：t.cn 对目标地址返回 302，Location 即原链；无需登录。
# 用法: python -X utf8 resolve_tcn.py <calendar_txt> [--write] [--delay 0.4]
#   默认：生成 <同名>.resolved.txt，并打印映射表；不改原文件
#   --write：就地改写原文件（先备份为 <同名>.tcnbak.txt）
import re, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = sys.argv[1]
WRITE = '--write' in sys.argv
delay = 0.4
if '--delay' in sys.argv:
    delay = float(sys.argv[sys.argv.index('--delay') + 1])

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None

op = urllib.request.build_opener(NoRedirect)
op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')]

def resolve(u):
    for attempt in range(3):
        try:
            op.open(u, timeout=15)
            return None
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                return e.headers.get('Location')
            return None
        except Exception:
            time.sleep(2)
    return None

text = open(path, encoding='utf-8').read()
tcn_links = sorted(set(re.findall(r'https?://t\.cn/[A-Za-z0-9]+', text)))
print(f'发现 {len(tcn_links)} 个 t.cn 短链，开始解析…', flush=True)

mapping, failed = {}, []
for i, u in enumerate(tcn_links, 1):
    loc = resolve(u)
    if loc:
        mapping[u] = loc
        print(f'  [{i}/{len(tcn_links)}] {u} -> {loc}', flush=True)
    else:
        failed.append(u)
        print(f'  [{i}/{len(tcn_links)}] {u} -> 解析失败', flush=True)
    time.sleep(delay)

new_text = text
for short, long in mapping.items():
    new_text = new_text.replace(short, long)

if WRITE:
    import shutil, os
    bak = os.path.splitext(path)[0] + '.tcnbak.txt'
    shutil.copyfile(path, bak)
    open(path, 'w', encoding='utf-8').write(new_text)
    print(f'已就地改写 {path}（备份 {bak}）')
else:
    out = re.sub(r'\.txt$', '.resolved.txt', path)
    open(out, 'w', encoding='utf-8').write(new_text)
    print(f'已生成 {out}')

print(f'成功 {len(mapping)}，失败 {len(failed)}')
if failed:
    for u in failed:
        print('  失败:', u)
    sys.exit(1)
