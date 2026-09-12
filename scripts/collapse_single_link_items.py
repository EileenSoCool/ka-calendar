import re, sys
from pathlib import Path

# 用法: python -X utf8 collapse_single_link_items.py <单个成品txt路径>
# 一次只处理一个文件。绝不整目录批跑——批跑会把用户已手改好的其他月份一并重排，
# 这是明确禁止的行为（2026-09-12 用户点名修正）。
if len(sys.argv) < 2:
    print('用法: python -X utf8 collapse_single_link_items.py <单个成品txt路径>')
    sys.exit(2)
path = Path(sys.argv[1])
if not path.is_file():
    print(f'文件不存在: {path}')
    sys.exit(2)

item_re = re.compile(r'^[0-9]️⃣')
date_re = re.compile(r'^[𝟎-𝟗]{4}$')  # 全角粗体日期（𝟎𝟏~𝟏𝟐月都要认）
url_re = re.compile(r'https?://\S+')

def transform(text: str) -> str:
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if item_re.match(line):
            item = line.rstrip()
            j = i + 1
            payload = []
            while j < len(lines) and not item_re.match(lines[j]) and not date_re.match(lines[j]):
                if lines[j].strip() == '':
                    break
                payload.append(lines[j].rstrip())
                j += 1
            if len(payload) == 1:
                p = payload[0].strip()
                if url_re.search(item):
                    # 条目行本身已含链接（如 💌标题+本人链，payload 是同步博链）：
                    # 保持两行结构，不折叠（否则两个链接会挤在一行）
                    out.append(item)
                    out.append(p)
                else:
                    # 标题不含链接：折叠成一行，保留 payload 里的全部链接
                    urls = url_re.findall(p)
                    out.append(item + ' '.join(urls) if urls else item + p)
            else:
                out.append(item)
                out.extend(payload)
            i = j
            continue
        out.append(line.rstrip())
        i += 1
    return '\n'.join(out) + '\n'

original = path.read_text(encoding='utf-8')
new = transform(original)
path.write_text(new, encoding='utf-8')
print(f'updated {path.name}')