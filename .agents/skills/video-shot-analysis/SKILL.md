***

name: video-shot-analysis

description: 对短视频（抖音 / 快手 / 视频号 / 小红书 / B 站爆款）做逐镜头拉片分析，最终交付两份产物 —— 自包含 HTML 拉片档案（含关键帧、ECharts 情绪能量曲线与镜头节奏图）和标准化 Markdown（YAML 字段头，便于多条拉片横向汇总）。当用户说 "拉片 / 拆片 / 逐镜头拆解 / 分析这条爆款 / 学习它的钩子、剪辑节奏、选题、分镜、转场、BGM、音效、字幕"，或要批量拉片、沉淀创作方法论时使用。覆盖情感剧情、悬疑反转、纪实等体裁，默认面向 AI 剧情短片创作。



***

# 短视频拉片分析

把一条爆款拆成 "可复算的证据 + 可复用的方法"。证据落到时间码，方法面向用户的账号定位。

## 交付物（固定两份）



1. **HTML 拉片档案**：自包含单文件，8 个章节（概览 / 情绪曲线 / 逐镜表 / 钩子 / 脚本 / 声音 / 字幕 / 方法论），ECharts 图表，关键帧内嵌。

2. **标准化 Markdown**：YAML 元数据头 + 固定章节 + 枚举口径，供多条汇总。

## 工作流程

### 1. 确认输入



* 取得视频文件路径；缺文件或链接打不开时用 `interaction.ask` 索取，不猜测内容。

* 明确四件事：**拉片目的、账号定位、关注重点、交付形式**。用户未说全时，默认按 "钩子 / 脚本 / 镜头转场 / BGM 音效 / 字幕" 五件套 + 面向其账号的方法论。

### 2. 抽取素材（确定性脚本，勿手写重推）



```
bash scripts/extract_media.sh <input_video> <out_dir>
# 可选对转场段加密抽帧： LAPIAN_DENSE="14:18 96:100" bash scripts/extract_media.sh ...
```

一次性产出：`probe.json`、切点（`scene_cuts*.txt`，阈值 0.30/0.12）、抽帧（全片 1fps、前 12s @4fps、前 2s @8fps）、联系表 `sheet_*.jpg`、压缩音频 `audio/asr_audio.mp3`、压缩视频 `ocr_small.mp4`、能量曲线 `rms_curve.txt`。

### 3. 云端识别（ASR + OCR）

大文件直接上传必超时，**只用脚本产出的压缩输入**：



* ASR：`audio/asr_audio.mp3`；OCR：`ocr_small.mp4`。

* 用 mediakit-cli：先 Read `byted-mediakit-shared` 与 `byted-mediakit-video` 的 SKILL.md，再跑 `video asr-subtitles` 与 `video video-ocr`（OCR 用 Detailed 模式取文字位置）。异步任务用 `shared query-task` 轮询终态。

* 产物存为 `asr_result.json`、`ocr_result.json`。

### 4. 通览分镜，建立镜头清单



* 逐张 Read `sheet_*.jpg`（含 `sheet_hook.jpg`）通览全片；**联系表单张必须 ≤ 约 980px 宽**，过大会被读图工具拒绝。

* 结合切点、ASR、OCR，归并出镜头清单（编号、时间码、景别运镜、画面、对白 / 侧字幕、声音、叙事功能）。蒙太奇段标注其内部切点。

* 识别统一的转场语法（如白闪）与色彩双轨（冷 = 现实 / 暖 = 回忆），记录转场精确时间码与音效。

### 5. 分析

按 `references/analysis-framework.md` 的框架产出结论：钩子公式、叙事结构与闭环、情绪工程、声音设计、字幕语法、选题公式、面向用户账号的工作流与避坑。所有结论回指时间码，不凭印象。

### 6. 准备关键帧

从 `frames/` 为每个镜头选代表帧，压到约 460px 宽放入报告 `assets/`，命名 `sXX.jpg`（蒙太奇可 sXXa/b/c），另选一张 `assets/hero.jpg`：



```
ffmpeg -i frames/f_001.jpg -vf scale=460:-2 -q:v 4 assets/s01.jpg
```

### 7. 产出 HTML



* 复制 `assets/html_template.html` 到报告目录，替换全部 `@@占位@@`；逐镜表逐行填，图片写 `src="assets/sXX.jpg"`（必须静态写在 src，勿用 JS 生成）。

* 填图表数据数组：`ENERGY_T/ENERGY_V/ACT_NAMES/ACT_SHOTS/ACT_CUTS/ACT_AREAS/FLASH_PTS`。幕数变化时同步改 head 中 `ACT_GRID`。

* 能量归一化：把 `rms_curve.txt` 的 dB 映射到 0–1（线性 min-max），保留实测 dB 在 MD。

### 8. 产出 Markdown

复制 `assets/md_template.md`，替换 `@@占位@@` 与 `<!-- FILL -->`；YAML 取值优先用文末枚举，保持字段名与章节顺序不变。

### 9. 校验



* 提取 HTML 内联 JS 跑 `node --check`（ECharts 配置花括号易错，须通过）。

* 核对每个 `src="assets/..."` 文件都存在、无遗漏。

* 内嵌关键帧产出自包含文件：



```
python3 scripts/embed_html.py <report.html>   # 须输出 remaining relative refs=0
```



* 页面自检 `shot.py` 若因浏览器自动化失败可跳过（规范允许）；需要肉眼确认时可用 headless Chrome：

  `--headless=new --virtual-time-budget=8000 --window-size=1440,900 --screenshot=...`（该方式可能受本机 Chrome 状态影响而超时，失败不阻塞）。

### 10. 交付与清理



* 用 `present_files` 分别交付 HTML 与 MD（两个不同产物，可同批）。

* 用户要求精简时，删除 frames/audio/ 压缩视频 / 日志等中间产物，只留两份成品；源视频在用户处，可随时重跑步骤 2–3。

## 关键经验（避坑）



* 大文件上传超时 → 永远用 16k 单声道 mp3 做 ASR、720p CRF26 做 OCR。

* 联系表 / 关键帧尺寸：联系表 ≤ 约 980px 宽；报告帧约 460px 宽。

* 转场与情绪点以 "画面帧 + 音频峰值" 双证据定位；同一音效多次出现看峰值是否逐级加码。

* HTML 图表 JS 花括号闭合是高频错误，`node --check` 必过再交付。

* 多条拉片严格统一字段口径与枚举（见 md 模板附录），同义词只保留一个写法。