---
name: douyin-video-stats
description: 从抖音（Douyin）视频链接抓取互动数据（点赞/评论/收藏/转发）与评论内容。当用户提供抖音视频链接并要求"拿视频数据""看点赞收藏转发""拉评论区""抓评论""抓取前N条热门评论""输出为md"等时使用；也适用于批量处理多个抖音链接获取其互动数据。基于浏览器自动化（mac_computer_use_tool + seed_browser_use）执行，不依赖第三方 API。
---

# 抖音视频互动数据抓取

## 前置依赖（必读）

开始前先读取并遵循 `browser-use-automation-mac` 技能（`.skills/browser-use-automation-mac/SKILL.md`）的规则。页面操作一律通过 `mac_computer_use_tool` 的 `plane="bu"` + `import seed_browser_use as bu` 完成，禁止用 Bash/HTTP 客户端替代浏览器操作。

## 执行流程

### 1. 打开视频页面

```python
import seed_browser_use as bu

bu.navigate("<视频链接>")
bu.wait_for_load(timeout=20)
print(bu.page_info())  # 确认 title 含目标视频名，防止链接跳转到其他视频
```

- 支持链接形式：
  - 视频独立页：`https://www.douyin.com/video/<aweme_id>`（**评论抓取首选**）
  - 精选页：`https://www.douyin.com/jingxuan?modal_id=<id>`
  - 用户主页：`https://www.douyin.com/user/<uid>?modal_id=<id>`
- **用户主页链接的坑**：打开后 modal 弹窗可能不自动出现（URL 上的 modal_id 被剥离），检查 `document.querySelector('[data-e2e="modal-video-container"]')` 与 `[data-e2e="video-player-digg"]` 是否存在；不存在时重新导航原链接并多等 3~5 秒。
- **优先切换到视频独立页**：评论区遇到"登录后可看更多"截断（见第 4 节）时，从原链接的 `modal_id` 参数或页面快照中的 `/video/<id>` 链接提取 aweme_id，导航到 `https://www.douyin.com/video/<aweme_id>`——独立页评论通常不受该登录限制，可正常滚动加载。
- 若出现登录弹窗（"登录后免费畅享高清视频"等）：统计数据与热门评论在未登录状态通常仍可读，先直接继续；只有内容被登录墙完全阻断（读取为空或只有登录提示）时，才调用 `interaction.request_action`（type="browserControl"）交给用户登录后继续。

### 2. 提取互动数据（点赞/评论/收藏/转发）

用 `bu.js` 按 `data-e2e` 属性精确提取（抖音 Web 的语义化属性，最可靠）：

```python
js = r"""
JSON.stringify(['video-player-digg','feed-comment-icon','video-player-collect','video-player-share'].map(k => {
  const el = document.querySelector('[data-e2e="'+k+'"]');
  if (!el) return {key:k, found:false};
  return {key:k, found:true, text:(el.innerText||'').trim()};
}))
"""
print(bu.js(js))
```

键映射：

| data-e2e | 指标 |
|---|---|
| video-player-digg | 点赞 |
| feed-comment-icon | 评论 |
| video-player-collect | 收藏 |
| video-player-share | 转发 |

注意：
- 数字实时变化（评论数可能每次刷新略增），报告时注明"实时数据"。
- 万级数字页面以约数显示（如"11.8万"），原样报告并注明为页面显示值；如用户要精确值，说明页面仅展示约数。
- 页面含多条视频（feed 流）时 `querySelector` 取第一个匹配，即当前激活视频；可用 `document.querySelector('[data-e2e="feed-active-video"]')` 存在性确认目标视频激活。元数据（作者名等）要与统计数字落在同一视频信息容器内核对，避免拿错相邻视频的数据。

### 3. 提取视频元数据

- 标题：`bu.page_info()` 的 title 字段（去掉结尾 " - 抖音"）。
- 作者/发布时间/共创人数：用 `bu.get_page_text()` 定位 `@作者名` 及其后文本（"· N小时前 · N人共创"）。
- 时长：页面文本中 `00:00 / MM:SS` 格式。
- 合集/集数/作者声明（如"内容由 AI 生成"）：从视频信息区文本提取。
- 用户主页场景下还可提取账号信息：粉丝数/获赞数/IP属地/抖音号（页面文本中"粉丝 N / 获赞 N / 抖音号：xxx / IP属地：xx"）。

### 4. 打开评论区

```python
bu.js(r"""(() => { const el = document.querySelector('[data-e2e="feed-comment-icon"]'); if (!el) return 'not found'; el.click(); return 'clicked'; })()""")
bu.wait_for_load(timeout=5)
import time; time.sleep(2)
```

- 评论区主容器 class 包含 `comment-mainContent`，顶部显示 `全部评论(N)`——N 即评论总数。
- **登录墙差异（重要）**：部分页面（如用户主页弹窗场景）评论区只加载约 10 条后出现"登录后可看更多"，滚动无效。此时按第 1 节规则切换到视频独立页 `/video/<aweme_id>` 再打开评论区，通常可继续加载。
- **主页弹窗滚动切换风险（重要）**：在用户主页弹窗（modal）场景滚动评论区时，feed 可能自动切换视频，`location.href` 中的 `modal_id` 会变成其他视频的 id，评论区面板随之错位到错误视频。**滚动前先记录目标 aweme_id**，滚动过程中若发现 URL 的 modal_id ≠ 目标 id，立即导航到 `https://www.douyin.com/video/<目标id>` 独立页重新打开评论区（独立页滚动加载稳定，不会切换）。
- 若点击无效（弹窗遮挡），先读取当前快照判断是否有遮罩层，再处理。

### 5. 滚动加载更多评论（含抓取前 N 条）

```python
# 抓取前 N 条：循环滚动 + 实时计数，达标即停；默认 N=100
for i in range(60):
    cnt = bu.js(r"""
    (() => {
      const main = document.querySelector('[class*="comment-mainContent"]');
      if (!main) return -1;
      const kids = Array.from(main.children);
      let count = 0;
      for (const k of kids) {
        const t = (k.innerText || '').trim();
        if (t && !t.startsWith('加载中') && !t.startsWith('登录后可看更多')) count++;
      }
      return count;
    })()
    """)
    if int(cnt) >= N:   # N 为目标条数，默认 100
        break
    bu.scroll(500, 300, "down", amount=8)
    time.sleep(1.2)
```

- 计数排除两个非评论元素："加载中"、"登录后可看更多"。
- **滚动前记录目标 aweme_id**（从 URL 的 modal_id 或 /video/ 路径提取）；每次滚动后可用 `bu.js("location.href")` 检查 URL 是否变化，一旦 modal_id 与目标不符说明弹窗切到了其他视频，立即切回独立页重新开始。
- 评论总量大（数千条）时通常按需抓取前 100 条热门评论即可（默认值，用户另有指定时按指定数量），报告中注明"已抓取 N 条可见评论（总数 N 条）"。

### 6. 提取评论内容

**6a. 快速浏览（少量评论时）**：直接取 `comment-mainContent` 的 innerText（见下），按文本结构肉眼解析。

**6b. 结构化批量提取（推荐，抓取大量评论时）**：`comment-mainContent` 的**直接子元素即每条评论的完整容器**，逐条解析：

```python
js = r"""
(() => {
  const main = document.querySelector('[class*="comment-mainContent"]');
  if (!main) return 'no main';
  const kids = Array.from(main.children);
  const out = [];
  for (const k of kids) {
    const text = (k.innerText || '').trim();
    if (!text || text.startsWith('加载中') || text.startsWith('登录后可看更多')) continue;
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
    if (lines.length < 3) continue;
    const user = lines[0];
    let timeIdx = -1;
    for (let i = 1; i < lines.length; i++) {
      if (/^\d+[分钟小时天月年]前·/.test(lines[i])) { timeIdx = i; break; }
    }
    if (timeIdx < 0) continue;
    const contentLines = [];
    let authorLiked = false, isAuthor = false;
    for (let i = 1; i < timeIdx; i++) {
      if (lines[i] === '...') continue;
      if (lines[i] === '作者赞过') { authorLiked = true; continue; }
      if (lines[i] === '作者') { isAuthor = true; continue; }
      contentLines.push(lines[i]);
    }
    const tl = lines[timeIdx];
    const m = tl.match(/^(\d+[分钟小时天月年]前)·(.+)$/);
    let likes = 0;
    for (let i = timeIdx + 1; i < lines.length; i++) {
      if (/^[\d.]+万?$/.test(lines[i])) { likes = lines[i]; break; }
    }
    let replies = 0;
    for (let i = timeIdx + 1; i < lines.length; i++) {
      const rm = lines[i].match(/^展开(\d+)条回复$/);
      if (rm) { replies = parseInt(rm[1]); break; }
    }
    out.push({user, content: contentLines.join(' '), time: m?m[1]:tl,
              location: m?m[2]:'', likes: String(likes), replies, authorLiked, isAuthor});
  }
  return JSON.stringify(out);
})()
"""
import json
data = json.loads(bu.js(js))
```

每条评论的 innerText 结构：用户名 → "..."（更多按钮）→（"作者"标签，如有）→ 评论正文 →（"作者赞过"，如有）→ 时间·地区 → 点赞数 → 分享/回复 →（"展开N条回复"，如有）。

### 7. 整理输出（含 MD 文件规范）

用户要求输出 md 文件时，生成到**主项目目录**，文件名用"作者名_视频关键词_视频数据.md"：

```bash
# 用 Python 脚本生成：读取评论 JSON → 按点赞数降序排序 → 输出 Markdown
```

MD 文件结构（三部分 + 说明）：
1. **一、视频基本信息表**：标题/作者（含粉丝数等账号信息）/发布时间/时长/位置/备注（AI 声明）/视频链接。
2. **二、互动数据表**：点赞/评论/收藏/转发，注明"页面显示约数，实时增长中"。
3. **三、热门评论 TOP 100 表**：# / 评论者 / 评论内容（超长截断加"…"，截断阈值100字）/ 点赞 / 时间 / 地区 / 回复数 / 备注（作者、作者赞过），**按点赞数降序**（"万"需转数值比较：`float(x)*10000 if 含"万" else int(x)`）。默认输出 TOP 100，用户明确指定其他数量时按用户要求。
4. **抓取说明**：数据来源链接、抓取时间、评论总数、可见评论条数、口径说明。

纯聊天交付时同样按三部分表格呈现（基本信息 + 互动数据 + 热门评论 TOP 100 表 + 氛围概述）。

## 关键技术细节（踩坑记录，务必遵守）

- **`bu.js` 只接受表达式或 IIFE**：传 `() => {...}`（箭头函数定义）会返回空字典 `{}`；必须传立即执行形式 `(() => {...})()` 或直接表达式（如 `"document.title"`）。返回值可直接用。
- **不要用 `bu.cdp` 执行 JS**：当前环境报 "Session with id not found"，不可用。
- **`bu.http_get` 只能拿到 JS 壳 HTML**（无统计数据，数据在渲染后的 DOM 中），必须先 `wait_for_load` 并从 DOM 提取。
- **`bu.read_all` 的 fields 白名单有限**（tag/text/title 等，不支持 class），提取复杂嵌套结构优先用 `bu.js`。
- **评论项容器**：`comment-mainContent` 的直接子元素即评论块（DIV）；尾部可能有"加载中""登录后可看更多"占位元素，需排除。
- **时间·地区正则**：`^\d+[分钟小时天月年]前·`，地区是"·"后的文本；个别评论无地区或时间格式不同，解析失败就跳过该条并计数。
- **URL 校验（防视频切换错位）**：用户主页弹窗场景下滚动评论区可能触发 feed 自动切换，导致 URL 的 `modal_id` 变化、评论面板对应到错误视频。以 `location.href` 中的 modal_id 是否等于目标 aweme_id 为准判断；不等就切回 `/video/<目标id>` 独立页重来。
- **点赞排序**：页面值可能是"7.2万"或"984"，排序前统一转数值。
- 若后续抖音改版导致 `data-e2e` 失效：先用 `bu.js("JSON.stringify(Array.from(document.querySelectorAll('[data-e2e]')).map(el => el.getAttribute('data-e2e')).filter(Boolean).slice(0,150))")` 枚举新键名，再调整映射。
