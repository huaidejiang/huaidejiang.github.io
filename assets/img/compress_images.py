"""
压缩当前文件夹下的所有图片（改进版）
- 如果压缩后反而变大，保留原文件
- PNG 支持有损压缩（量化颜色数）以获得更好的压缩率
- 支持格式：JPG, JPEG, PNG, BMP, TIFF, WEBP
"""

import os
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("正在安装 Pillow 库...")
    os.system("pip install Pillow --break-system-packages -q")
    from PIL import Image

# ========== 配置参数 ==========
QUALITY = 75              # JPEG/WEBP 压缩质量 (1-95)
MAX_WIDTH = 1920          # 最大宽度，设为 None 不限制
MAX_HEIGHT = 1080         # 最大高度，设为 None 不限制
PNG_COLORS = 0          # PNG 量化颜色数 (0=不量化保持无损, 64/128/256=有损但更小)
KEEP_ORIGINAL_IF_LARGER = True  # 压缩后变大则保留原文件
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def compress_image(input_path: Path, output_path: Path):
    """压缩单张图片，返回 (原始大小, 压缩后大小, 是否跳过)"""
    img = Image.open(input_path)
    original_size = input_path.stat().st_size

    # 保留 EXIF
    exif = img.info.get("exif")

    # 等比缩放
    if MAX_WIDTH and MAX_HEIGHT:
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

    is_png = output_path.suffix.lower() == ".png"

    if is_png:
        # PNG 处理：尽量保留原始模式，避免不必要的转换
        if PNG_COLORS > 0 and img.mode in ("RGB", "RGBA"):
            # 有损量化：减少颜色数，大幅缩小 PNG 体积
            img = img.quantize(colors=PNG_COLORS, method=Image.MEDIANCUT)
    else:
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

    # 保存
    save_kwargs = {"optimize": True}
    if not is_png and output_path.suffix.lower() in (".jpg", ".jpeg", ".webp"):
        save_kwargs["quality"] = QUALITY
    if is_png:
        save_kwargs["compress_level"] = 9  # 最大 PNG 压缩级别
    if exif and not is_png:
        save_kwargs["exif"] = exif

    img.save(output_path, **save_kwargs)
    compressed_size = output_path.stat().st_size

    # 如果压缩后反而变大，用原文件替换
    skipped = False
    if KEEP_ORIGINAL_IF_LARGER and compressed_size >= original_size:
        shutil.copy2(input_path, output_path)
        compressed_size = original_size
        skipped = True

    ratio = (1 - compressed_size / original_size) * 100 if original_size else 0
    return original_size, compressed_size, ratio, skipped


def main():
    current_dir = Path(".")
    output_dir = current_dir / "compressed"
    output_dir.mkdir(exist_ok=True)

    images = [f for f in current_dir.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]

    if not images:
        print("当前文件夹下没有找到图片文件。")
        return

    print(f"找到 {len(images)} 张图片，开始压缩...\n")
    print(f"  {'文件名':<40} {'原始大小':>10} {'压缩后':>10} {'压缩率':>8}  备注")
    print("  " + "-" * 85)

    total_original = 0
    total_compressed = 0
    skipped_count = 0

    for img_path in sorted(images):
        output_path = output_dir / img_path.name
        try:
            orig, comp, ratio, skipped = compress_image(img_path, output_path)
            total_original += orig
            total_compressed += comp
            if skipped:
                skipped_count += 1
            note = "⏭ 保留原图" if skipped else ""
            print(f"  {img_path.name:<40} {orig/1024:>8.1f}KB {comp/1024:>8.1f}KB {ratio:>7.1f}%  {note}")
        except Exception as e:
            print(f"  {img_path.name:<40} ❌ 失败: {e}")

    print("  " + "-" * 85)
    total_ratio = (1 - total_compressed / total_original) * 100 if total_original else 0
    print(f"  {'合计':<40} {total_original/1024:>8.1f}KB {total_compressed/1024:>8.1f}KB {total_ratio:>7.1f}%")
    print(f"\n  ✅ 压缩完成！{len(images)} 张图片已处理，{skipped_count} 张保留原图")
    print(f"  📁 输出目录: ./compressed/")


if __name__ == "__main__":
    main()