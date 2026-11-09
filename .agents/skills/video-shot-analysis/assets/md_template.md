---
# ===== 标准化元数据（多条拉片汇总主键，字段名请勿改动；@@ 为待填占位）=====
id: @@ID@@                              # 英文短横线唯一标识
title: @@TITLE@@
source_platform: @@SOURCE_PLATFORM@@     # 抖音/快手/视频号/小红书/B站
content_type: @@CONTENT_TYPE@@          # 情感剧情短片/悬疑反转/搞笑段子/知识口播/纪实采访/混剪
account_positioning: @@ACCOUNT_POSITIONING@@   # 拉片者自己的账号定位
true_story: @@TRUE_STORY@@              # true/false
subject_person: @@SUBJECT_PERSON@@      # 真实人物姓名/称号，无则填 null
location: @@LOCATION@@
duration_sec: @@DURATION_SEC@@
resolution: @@RESOLUTION@@              # 形如 1920x1080
fps: @@FPS@@
shot_count: @@SHOT_COUNT@@
montage_count: @@MONTAGE_COUNT@@
theme_tags: [@@THEME_TAGS@@]
hook_type: [@@HOOK_TYPE@@]              # 取值见文末枚举，可多选
structure_type: @@STRUCTURE_TYPE@@
act_count: @@ACT_COUNT@@
act_boundaries_sec: [@@ACT_BOUNDARIES@@]
transition_signature: @@TRANSITION_SIGNATURE@@
flash_points_sec: [@@FLASH_POINTS@@]
color_system: @@COLOR_SYSTEM@@
dialogue_dialect: @@DIALECT@@           # 无方言填 普通话
subtitle_layers: @@SUBTITLE_LAYERS@@    # 整数 1–5
bgm_structure: @@BGM_STRUCTURE@@
end_song: @@END_SONG@@                  # 无则填 null
emotion_peak_sec: @@EMOTION_PEAK_SEC@@
emotion_valley_sec: @@EMOTION_VALLEY_SEC@@
analysis_date: @@ANALYSIS_DATE@@
analyst: @@ANALYST@@
---

# 拉片笔记 · @@TITLE@@

> **用途**：本文件为"标准化拉片模板"实例。多条拉片保持相同 YAML 字段、章节顺序与枚举口径即可横向对比。
> 配套产物：同目录 HTML 档案（含关键帧与图表，供人阅读）；本 MD 供机器汇总。

## 0. 标准化分析卡（横向对比用）

| 维度 | 本条取值 |
| --- | --- |
| 一句话选题 | @@FILL@@ |
| 开场前 3 秒 | @@FILL@@ |
| 钩子底层 | @@FILL（如：制造未完成的信息缺口）@@ |
| 叙事结构 | @@FILL@@ |
| 情绪策略 | @@FILL@@ |
| 转场 | @@FILL@@ |
| 声音 | @@FILL@@ |
| 字幕 | @@FILL@@ |
| 信任锚点 | @@FILL（真实素材段，无则填 无）@@ |
| 可传播符号 | @@FILL（落版词，无则填 无）@@ |

## 1. 全片概览
<!-- FILL: 2–4 段。人物、事件、时空结构；真实人物点名；结构亮点单独成段。 -->

### 五幕划分（幕数变化时表头相应增减）

| 幕 | 时间码 | 时长 | 名称 | 色调 | 内容要点 |
| --- | --- | --- | --- | --- | --- |
| 一 | @@FILL@@ | | | 冷/暖 | @@FILL@@ |
| 二 | @@FILL@@ | | | | @@FILL@@ |
| 三 | @@FILL@@ | | | | @@FILL@@ |
| 四 | @@FILL@@ | | | | @@FILL@@ |
| 五 | @@FILL@@ | | | | @@FILL@@ |

<!-- FILL: 视觉双轨/色彩体系说明。 -->

## 2. 情绪能量曲线（实测，可直接取数）

```text
时间窗起点(s) : @@FILL（逗号/空格分隔）@@
RMS(dB)       : @@FILL，与上行等长@@

归一化能量(0-1): [@@FILL@@]
对应时间(s)    : [@@FILL，与上行等长@@]
```

**节奏特征**：<!-- FILL: 压抑区、假高潮、总爆发各一句。 -->

### 各幕镜头/切点数量

| 幕 | 一 | 二 | 三 | 四 | 五 |
| --- | --- | --- | --- | --- | --- |
| 段落镜头数 | @@FILL@@ | | | | |
| 含蒙太奇切点（估算） | @@FILL@@ | | | | |

```text
段落镜头数        = [@@FILL@@]
含蒙太奇切点估算  = [@@FILL@@]
```

## 3. 逐镜头拆解表

> 标记约定：`〔〕`= 画面左侧括号式内心/旁白；`「」`= 年份标签；`<br>`= 同镜换行。

### @@第一幕名（时间码）@@

| # | 时间码 | 景别·运镜 | 画面内容 | 对白·旁白 | 声音·音效 | 叙事功能 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | @@FILL@@ | | | | | @@FILL@@ |

<!-- FILL: 逐幕重复上表，把全部镜头列完；每幕前用 ### 幕名。 -->

## 4. 开头钩子拆解
<!-- FILL: 钩子公式（各要素）；0–1s / 1–3s 分段；记忆碎片手法；2–3 个钩子点；核心原则。 -->

## 5. 脚本框架还原
<!-- FILL: 结构类型与闭环；叙事骨架（编号各拍）；关键转折点节拍表（时间码→事件）；首尾呼应/动作闭环。 -->

## 6. 声音设计
<!-- FILL: BGM 结构（时间段→配器/电平）；音效点位（时间码→音效/峰值）；人声分层；峰值管理；选曲逻辑。 -->

## 7. 字幕呈现系统
<!-- FILL: 用表格列出实际出现的字幕类型（类型|位置/样式|示例|功能），缺失类型删除；补设计原因与零配音落地提示。 -->

## 8. 可复用方法论
<!-- FILL: ① 选题公式＋可平移题材 ② 结构模板（分段骨架，注明最低配置与伸缩）③ 制作工作流（编号各步）④ 情绪口诀 ⑤ 避坑清单 ⑥ 底层逻辑一句话。 -->

---

## 附录：字段口径与枚举表（多片统一填写）

> 取值优先用下列枚举，新增需登记；同义词统一（"闪白/过曝"统一记 `白闪`）。

| 字段 | 枚举值 |
| --- | --- |
| source_platform | 抖音 / 快手 / 视频号 / 小红书 / B站 |
| content_type | 情感剧情短片 / 悬疑反转 / 搞笑段子 / 知识口播 / 纪实采访 / 混剪 |
| true_story | true / false |
| hook_type | 反常识数字 / 物件特写快切 / 强冲突台词 / 一镜到底 / 记忆碎片对白 / 直接提问 / 结果前置 / 反差身份 |
| structure_type | 现实钩子-年代闪回-重逢-真实佐证（环形报恩）/ 单线顺叙 / 倒叙 / 多线交织 / 三幕反转 / 闯关升级 |
| transition_signature | 白闪+whoosh / 硬切 / 叠化 / 匹配剪辑 / 遮挡转场 / 运镜转场 |
| color_system | 冷暖双轨 / 单色调 / 高饱和 / 黑白+点缀色 |
| bgm_structure | 三段式（压-假高潮-爆发）/ 单曲贯穿 / 静默为主 / 节奏卡点 |
| subtitle_layers | 整数 1–5 |

**汇总建议**：同类对比优先看 hook_type、structure_type、transition_signature、爆发点占比（peak/duration）；多条情绪数组按 t/duration 归一到统一时间轴叠加；镜头节奏同时记"段落镜头数"与"含蒙太奇切点数"。

---

*本笔记基于逐帧、ASR、OCR 与音频 RMS 实测整理；画面版权归原作者，仅作创作学习用途。*
