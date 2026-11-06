# 渲染配置与命令

脚本把关节人偶绘制为透明图层，再与场景像素合成。它不推断图像语义，使用 skill 的 Codex 必须先查看图片，将站位转换为配置。人偶采用简化投影和明暗，适合空间示意。

本文仅对应原图合成。要把已有站位图变成偏俯视／顶视空间示意，读取 [overhead-config.md](overhead-config.md)，使用 `render_overhead.py` 与三维位置配置；两种模式的脚位和工具目标坐标不能混用。

## 调用

```sh
python .agents/skills/scene-mannequin-blocking/scripts/render_mannequins.py \
  --config /path/to/project/blocking.json
```

在项目根目录执行，`python` 替换为含 Pillow、numpy 的解释器。需要时在独立虚拟环境执行 `python -m pip install pillow numpy`。无需 API 密钥、Blender 或外部图片服务。

可选：`--output-prefix /path/to/new-prefix` 临时更换输出前缀；`--clean-only` 只生成无字图。默认遇到已有输出会停止；只有明确要替换时才使用 `--overwrite`。

## 最小配置

```json
{
  "scene": "../assets/scene.png",
  "output_prefix": "../assets/scene-blocking-v1",
  "supersample": 2,
  "people": [
    {
      "id": "a",
      "name": "角色甲",
      "color": "#b24b40",
      "foot": [0.38, 0.83],
      "height_ratio": 0.55,
      "pose": "stir",
      "facing": "left",
      "label": "前景操作台外侧",
      "label_xy": [0.30, 0.22]
    },
    {
      "id": "b",
      "name": "角色乙",
      "color": "#d3a740",
      "foot": [0.55, 0.62],
      "height_ratio": 0.38,
      "pose": "place",
      "facing": "left",
      "hat": true,
      "label": "后方桌边"
    }
  ]
}
```

路径默认相对配置文件所在目录解析，绝对路径也支持；`--output-prefix` 相对执行命令的当前目录解析。输出为 `<前缀>_无字.png`、`<前缀>_标注.png`，保持场景原图尺寸，不自动改画幅。

| 字段 | 含义 |
| --- | --- |
| `scene`、`output_prefix` | 必填，干净底图路径和输出前缀 |
| `supersample` | 1、2 或 3，默认 2；大图内存紧张时用 1 |
| `people` | 非空人物数组，人数不固定 |
| `id` | 必填，唯一标识，不依赖真实人物姓名 |
| `foot` | 必填，脚下中心 `[u,v]`；左上 `[0,0]`、右下 `[1,1]`。从地面估计，不直接照搬台面圆圈 |
| `height_ratio` | 必填，约等于投影身高像素 ÷ 图高；用于匹配透视 |
| `color` | CSS 十六进制或英文颜色名，默认红色；多人应主动分配不同颜色 |
| `pose` | `stand` 自然垂手、`talk` 抬手交谈、`stir` 搅拌、`place` 伸手放物、`wash` 前倾清洗；默认 `stand` |
| `facing` | `left` 或 `right`，将身体轮廓和动作水平翻转，默认向左 |
| `head_yaw_degrees` | 镜像前的头部朝向，0 向画右、-90 向镜头、±180 向画左；默认 -150。朝右镜像同时镜像此方向 |
| `hat` | 可选黑帽，默认 false |
| `seated`、`bag` | 可选坐姿、绿色菜袋示意，默认 false；坐姿同时降低躯干、头与手臂并弯腿 |
| `name`、`label` | 姓名与简短站位说明，仅出现在标注图；name 默认 id |
| `label_xy` | 标签左上角 `[u,v]`，可选；默认落在人物右上方，须看图调整重叠 |
| `font` | 顶层可选，中日韩字体路径；自动寻找 macOS 黑体、Linux Noto CJK、Windows 微软雅黑；无可用字体时需指定或用 `--clean-only` |
| `foreground_mask` | 顶层可选，与场景同尺寸的灰度图；白色区域恢复原场景、黑色保留合成，用于台沿、门框等遮住人偶。透明度应先转为灰度遮罩 |

## 调整手臂和腿部

人物的可选 `arms`、`legs` 均为两个肢体，每个包含三个三维坐标：手臂为“肩、肘、手”，腿为“髋、膝、踝”，形状为 `[2,3,3]`。相邻关节不能是同一点。

局部坐标为近似米制：x 朝画右，y 朝远处，z 向上；站位锚点在脚下。标准模型头顶约 1.8，髋约 0.94，肩约 1.38。先按向左模型调整，再由 `facing=right` 镜像。脚位和投影比例仍由 `foot`、`height_ratio` 控制。

```json
"arms": [
  [[-0.13,0.13,1.38],[-0.40,0.18,1.15],[-0.62,0.22,1.02]],
  [[0.12,-0.13,1.38],[-0.09,-0.22,1.17],[-0.44,-0.13,1.14]]
]
```

关节点的图像位置约为：`u_px=foot_x+scale*x`、`v_px=foot_y-scale*(z+0.22*y)`，其中 `scale=height_ratio*图高/1.8`，可反推手的落点。`seated=true` 时，髋、躯干、头部及arms的z整体降低0.43；默认腿改为坐姿，自定义legs则直接以地面为基准填写。先对齐座面高度，不能只弯腿而让躯干仍立着。复杂坐姿仍需针对性建模。

## 简单手持工具

顶层可选 `tools` 为手到目标点的细杆示意，适用于勺柄；不会移开锅盖、修改原物体或生成油桶菜袋：

```json
"tools": [
  {"person":"a","hand":0,"target":[0.25,0.515],"width_px":4,"color":"#76736a","bowl":true}
]
```

`hand` 为该人物 arms 中的第 0 或第 1 只手，`target` 是归一化图像坐标，`bowl` 增加小勺头。工具绘于人偶之上，复杂前后遮挡应使用遮罩或另行精确绘制。

先检查脚与台面，再调投影高度、动作接触点，最后排标签。必须打开输出图片，不依赖脚本的成功返回判断视觉正确。
