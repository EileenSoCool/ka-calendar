# ka-calendar

王栎鑫行程月历（𝐊.𝐀月历）制作 skill。

## 目录结构说明

### 1) `SKILL.md`
Claude 的技能入口说明，定义触发场景、整体流程、溯源纪律与风控纪律。

### 2) `references/`
供使用者与模型共同参考的资料：

- `sources.md`：唯一可信的数据源清单（账号主体 / 机场与上下班来源 / 流水转发源 / 批准官方 / 粉丝账号 / 黑名单）
- `format-rules.md`：最终版式规则（💌、鑫室·、饭拍汇总、节目 cut 等）
- `cookie-guide.md`：如何从网页版微博获取 `SUB`
- `june_final.txt`：用户亲手改定的 6 月成品范例（黄金样本）

### 3) `scripts/`
可复用脚本：

- `month_mega.py`：单月全量抓取（同步博 / 直接源 / 汇总 / 机场 / 转发源）
- `month_fastjump.py`：老月份深跳探针 + 二分定位抓取（先探针再翻页）
- `match_sync.py`：王栎鑫当月微博 ↔ 同步博镜像配对
- `extract_candidates.py`：从转发源提取候选物料，并溯源到原博主
- `mid_lookup.py`：查 base62 微博短链（直接调用 `statuses/show?id=<mid>`）
- `collapse_single_link_items.py`：单链接小项折叠成一行（只接受单个文件参数，绝不批跑）
- `check_sync_links.py`：同步博链完整性自检
- `check_calendar.py`：成品格式 lint（半角日期/乱序/编号/断链/缺💌）
- `check_skeleton.py`：骨架完备性倒查（带排除规则层 + 跨月查找，四分类输出）
- `resolve_tcn.py`：t.cn 短链批量还原为 weibo.com 原链（骨架核对前先跑它）

## 与输出目录的关系

### 成品目录（如 `~/Desktop/KA-calendar/`）
这里存放最终成品（月历文本，如 `2026-06.txt`）和人工校对后的发布版本。

### 抓取产物目录（如 `~/{month}_out/`）
`sync.json` / `mat_*.json` / `air_*.json` / `src_*.json` / `candidates.txt` / `sync_map.json` 这类中间抓取数据，用于重做或修改某月时直接读取，避免重新抓微博。详细工作流见 `SKILL.md`「工作流与产物存放」。

### `KA-calendar/archive/`（成品目录下）
这里只保留少量通用工具或旧草稿；一次性抓取中间文件不建议长期堆在工作根目录。

## 分享给别人时应该打包什么

### 最小可用包（推荐）
直接打包整个 skill 目录（即 `~/.claude/skills/ka-calendar/`）：

zip 内包含：
- `SKILL.md`
- `README.md`
- `references\`
- `scripts\`

这样别人拿到后，放进自己的 `~/.claude/skills/` 下即可使用。

### 不建议打包的内容
- `KA-calendar/archive/` 里的中间过程文件
- 根目录 `{month}_out/` 抓取生成的临时 json / dump / candidates 文件
- `scripts/__pycache__/` 编译缓存
- 任意 cookie / 凭证文件

### 如果想附示例
`references/june_final.txt` 已经是最佳示例，一般不需要再额外打包桌面的成品月历。

## 最重要的两条纪律

1. 链接必须溯源到原博主，苦瓜等转发源只作为导航使用。
2. Cookie 不入库，每次现取、现用、现删。
