#!/usr/bin/env bash
# extract_media.sh — 拉片前置：一次性产出元数据/切点/抽帧/联系表/压缩音视频/能量曲线
# Usage: extract_media.sh <input_video> [out_dir]
# 依赖: ffmpeg ffprobe（含 libx264）
set -euo pipefail

IN="$1"
OUT="${2:-./lapian_work}"
FR="$OUT/frames"; AU="$OUT/audio"; AS="$OUT/assets"
mkdir -p "$FR" "$AU" "$AS"

echo "==> [1/8] ffprobe 元数据"
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json "$IN" > "$OUT/probe.json"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
echo "    duration=${DUR}s"

echo "==> [2/8] 场景切点检测（阈值 0.30 / 0.12）"
ffmpeg -hide_banner -i "$IN" -filter:v "select='gt(scene,0.30)',showinfo" -f null - 2> "$OUT/scene_log.txt"  || true
ffmpeg -hide_banner -i "$IN" -filter:v "select='gt(scene,0.12)',showinfo" -f null - 2> "$OUT/scene_log2.txt" || true
grep -oE 'pts_time:[0-9.]+' "$OUT/scene_log.txt"  | cut -d: -f2 > "$OUT/scene_cuts.txt"  || true
grep -oE 'pts_time:[0-9.]+' "$OUT/scene_log2.txt" | cut -d: -f2 > "$OUT/scene_cuts2.txt" || true
echo "    cuts(0.30)=$(wc -l < "$OUT/scene_cuts.txt" | tr -d ' ')  cuts(0.12)=$(wc -l < "$OUT/scene_cuts2.txt" | tr -d ' ')"

echo "==> [3/8] 抽帧：全片 1fps"
ffmpeg -hide_banner -loglevel error -i "$IN" -vf fps=1 -q:v 3 "$FR/f_%03d.jpg"
echo "    frames=$(ls "$FR"/f_*.jpg | wc -l | tr -d ' ')"

echo "==> [4/8] 加密抽帧：前12s @4fps，前2s @8fps"
ffmpeg -hide_banner -loglevel error -t 12 -i "$IN" -vf fps=4 -q:v 3 "$FR/hook_%03d.jpg"
ffmpeg -hide_banner -loglevel error -t 2  -i "$IN" -vf fps=8 -q:v 3 "$FR/open_%03d.jpg"
# 可选：对指定转场段加密，环境变量 LAPIAN_DENSE="14:18 96:100"（空格分隔 起:止）
if [[ -n "${LAPIAN_DENSE:-}" ]]; then
  for seg in ${LAPIAN_DENSE}; do
    s="${seg%%:*}"; e="${seg##*:}"
    ffmpeg -hide_banner -loglevel error -ss "$s" -to "$e" -i "$IN" -vf fps=4 -q:v 3 "$FR/t${s}_%03d.jpg"
  done
fi

echo "==> [5/8] 联系表（单张控制在约 970px 宽，便于读图工具打开）"
# 全片：6列x5行，单元格 160 宽
ffmpeg -hide_banner -loglevel error -framerate 1 -i "$FR/f_%03d.jpg" -vf "scale=160:-1,tile=6x5:margin=2:padding=2" "$OUT/sheet_%02d.jpg"
# 开头钩子：8列x6行，单元格 120 宽
ffmpeg -hide_banner -loglevel error -framerate 1 -i "$FR/hook_%03d.jpg" -vf "scale=120:-1,tile=8x6:margin=2:padding=2" "$OUT/sheet_hook.jpg"

echo "==> [6/8] 音频：完整 wav + 16k 单声道 64k mp3（供 ASR，避免大文件上传超时）"
ffmpeg -hide_banner -loglevel error -i "$IN" -vn "$AU/full_audio.wav"
ffmpeg -hide_banner -loglevel error -i "$IN" -vn -ac 1 -ar 16000 -b:a 64k "$AU/asr_audio.mp3"

echo "==> [7/8] 压制 720p 视频（供 OCR）"
ffmpeg -hide_banner -loglevel error -i "$IN" -vf "scale=-2:720" -c:v libx264 -crf 26 -preset veryfast -an "$OUT/ocr_small.mp4"

echo "==> [8/8] 音量能量曲线：每 5s 窗口 mean_volume(dB)"
: > "$OUT/rms_curve.txt"
n=$(python3 -c "print(int(float('$DUR')//5)+1)")
for ((i=0;i<n;i++)); do
  t=$((i*5))
  db=$(ffmpeg -hide_banner -ss "$t" -t 5 -i "$IN" -af volumedetect -f null - 2>&1 | grep -oE 'mean_volume: -?[0-9.]+ dB' | grep -oE '\-?[0-9.]+ dB' | cut -d' ' -f1 || echo "NA")
  echo "$t $db" >> "$OUT/rms_curve.txt"
done

echo "==> 完成。产物目录：$OUT"
echo "    下一步：用 asr_audio.mp3 跑 ASR、ocr_small.mp4 跑 OCR（见 SKILL.md），再读 sheet_*.jpg 通览分镜。"
