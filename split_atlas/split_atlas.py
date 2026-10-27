#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Cocos Creator 2.x / cocos2d 的图集(.plist + .png)拆分为散图(.png)。

用法:
  python split_atlas.py [atlas_dir] [out_dir]

默认:
  atlas_dir = 脚本同目录的 atlas (或本机 G 盘路径)
  out_dir   = atlas_dir/split/<图集名>/<帧名>.png
"""
import os
import sys
import plistlib
from PIL import Image

DEFAULT_ATLAS = r"D:/NewCocos2dProject/assets/resources/atlas"


def parse_rect(s):
    """解析 '{{x,y},{w,h}}' 字符串 -> (x, y, w, h) 整数元组。"""
    nums = []
    for tok in s.replace("{", " ").replace("}", " ").split(","):
        tok = tok.strip()
        if tok:
            nums.append(int(round(float(tok))))
    return tuple(nums[:4])


def split_one(plist_path, png_path, out_dir):
    with open(plist_path, "rb") as f:
        data = plistlib.load(f)

    frames = data.get("frames", {})
    atlas = Image.open(png_path).convert("RGBA")
    os.makedirs(out_dir, exist_ok=True)

    count = 0
    for name, info in frames.items():
        x, y, w, h = parse_rect(info["frame"])            # 图集中位置/尺寸
        rotated = bool(info.get("rotated", False))

        # 完整画布尺寸 & 裁切内容在画布中的落点(sourceColorRect)
        sw, sh = parse_rect(info["sourceSize"]) if "sourceSize" in info else (w, h)
        ox, oy, cw, ch = parse_rect(info["sourceColorRect"]) if "sourceColorRect" in info else (0, 0, w, h)

        if rotated:
            # 关键点: 旋转帧在图集中实际占据 (h, w) 区域, frame 的 w/h 是"未旋转"尺寸。
            region = atlas.crop((x, y, x + h, y + w))
            # TexturePacker cocos2d 格式打包时顺时针 90°, 还原需逆时针 90° (ROTATE_90)。
            sprite = region.transpose(Image.ROTATE_90)
        else:
            region = atlas.crop((x, y, x + w, y + h))
            sprite = region

        # 贴回完整 sourceSize 画布, 保留原始几何/锚点 (零信息损失)。
        canvas = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        canvas.paste(sprite, (ox, oy))

        out_name = name if name.lower().endswith(".png") else name + ".png"
        out_path = os.path.join(out_dir, out_name)
        canvas.save(out_path, "PNG")
        count += 1

    return count, len(frames)


def main():
    atlas_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ATLAS
    out_root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(atlas_dir, "split")

    if not os.path.isdir(atlas_dir):
        print(f"[错误] 图集目录不存在: {atlas_dir}")
        sys.exit(1)

    total = 0
    for fname in sorted(os.listdir(atlas_dir)):
        if not (fname.endswith(".plist") and not fname.endswith(".meta")):
            continue
        base = fname[:-6]
        plist_path = os.path.join(atlas_dir, fname)
        png_path = os.path.join(atlas_dir, base + ".png")
        if not os.path.exists(png_path):
            print(f"[跳过] {base}: 找不到对应的 {base}.png")
            continue
        out_dir = os.path.join(out_root, base)
        n, expected = split_one(plist_path, png_path, out_dir)
        total += n
        print(f"[完成] {base}: 拆分 {n} 张 -> {out_dir}")

    print(f"\n全部完成，共拆分 {total} 张散图，输出根目录: {out_root}")


if __name__ == "__main__":
    main()
