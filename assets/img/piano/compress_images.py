"""
将文件夹下所有图片统一转换为 WebP 或 JPEG 格式
用法：
    python convert_images.py                    # 默认转 WebP
    python convert_images.py --format jpeg      # 转 JPEG
    python convert_images.py --quality 90       # 指定质量
    python convert_images.py --max-size 1920    # 限制最大边长
"""

import argparse
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("正在安装 Pillow 库...")
    os.system("pip install Pillow --break-system-packages -q")
    from PIL import Image

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


def convert_image(input_path: Path, output_path: Path, fmt: str, quality: int, max_size: int | None):
    """转换并压缩单张图片"""
    img = Image.open(input_path)
    original_size = input_path.stat().st_size

    # 等比缩放（按最大边长）
    if max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    # 处理透明通道
    if fmt == "jpeg" and img.mode in ("RGBA", "P", "LA", "PA"):
        # JPEG 不支持透明，用白色背景填充
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1])  # 用 alpha 通道做蒙版
        img = background
    elif fmt == "jpeg" and img.mode != "RGB":
        img = img.convert("RGB")
    elif fmt == "webp" and img.mode == "P":
        img = img.convert("RGBA")

    # 保存
    save_kwargs = {"quality": quality, "optimize": True}
    if fmt == "webp":
        save_kwargs["method"] = 6  # 最慢但压缩率最高

    img.save(output_path, **save_kwargs)
    compressed_size = output_path.stat().st_size
    ratio = (1 - compressed_size / original_size) * 100 if original_size else 0

    return original_size, compressed_size, ratio


def main():
    parser = argparse.ArgumentParser(description="批量转换图片格式")
    parser.add_argument("--format", choices=["webp", "jpeg"], default="webp", help="目标格式 (默认: webp)")
    parser.add_argument("--quality", type=int, default=80, help="压缩质量 1-95 (默认: 80)")
    parser.add_argument("--max-size", type=int, default=None, help="最大边长像素，等比缩放 (默认: 不限)")
    parser.add_argument("--dir", type=str, default=".", help="输入目录 (默认: 当前目录)")
    args = parser.parse_args()

    ext = ".webp" if args.format == "webp" else ".jpg"
    input_dir = Path(args.dir)
    output_dir = input_dir / f"converted_{args.format}"
    output_dir.mkdir(exist_ok=True)

    images = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
    ])

    if not images:
        print(f"在 {input_dir.resolve()} 下没有找到图片。")
        return

    fmt_label = args.format.upper()
    print(f"将 {len(images)} 张图片转为 {fmt_label}，质量={args.quality}")
    if args.max_size:
        print(f"最大边长限制: {args.max_size}px")
    print()
    print(f"  {'文件名':<45} {'原始':>9} {'转换后':>9} {'压缩率':>8}")
    print("  " + "-" * 75)

    total_orig = 0
    total_comp = 0
    fail_count = 0

    for img_path in images:
        output_path = output_dir / (img_path.stem + ext)
        try:
            orig, comp, ratio = convert_image(img_path, output_path, args.format, args.quality, args.max_size)
            total_orig += orig
            total_comp += comp
            print(f"  {img_path.name:<45} {orig/1024:>7.1f}KB {comp/1024:>7.1f}KB {ratio:>7.1f}%")
        except Exception as e:
            fail_count += 1
            print(f"  {img_path.name:<45} ❌ {e}")

    print("  " + "-" * 75)
    total_ratio = (1 - total_comp / total_orig) * 100 if total_orig else 0
    print(f"  {'合计':<45} {total_orig/1024:>7.1f}KB {total_comp/1024:>7.1f}KB {total_ratio:>7.1f}%")
    print(f"\n  ✅ 完成！{len(images) - fail_count} 张成功，{fail_count} 张失败")
    print(f"  📁 输出: {output_dir.resolve()}")
    if total_orig:
        print(f"  💾 总共节省: {(total_orig - total_comp) / 1024:.1f}KB ({total_ratio:.1f}%)")


if __name__ == "__main__":
    main()