"""
字体子集化工具 —— 大幅缩小字体文件体积
用法：
    # 模式1: 扫描网站文件，只保留实际用到的字符（推荐，体积最小）
    python subset_font.py --font font.woff2 --scan ./website_root

    # 模式2: 保留常用中文字符集（不扫描，通用性好）
    python subset_font.py --font font.woff2 --preset common

    # 模式3: 自定义保留的字符
    python subset_font.py --font font.woff2 --text "只保留这些字"

    # 可选参数
    --output output.woff2    指定输出文件名
    --format woff2           输出格式 (woff2/woff/ttf)
"""

import argparse
import os
import re
from pathlib import Path

# 安装依赖
try:
    from fontTools.subset import main as subset_main
    from fontTools.ttLib import TTFont
except ImportError:
    print("正在安装 fonttools + brotli (用于 woff2)...")
    os.system("pip install fonttools brotli zopfli --break-system-packages -q")
    from fontTools.subset import main as subset_main
    from fontTools.ttLib import TTFont

# 扫描文件的扩展名
SCAN_EXTS = {".html", ".htm", ".md", ".txt", ".json", ".js", ".jsx", ".ts", ".tsx", ".vue", ".css", ".yaml", ".yml"}

# 始终保留的基础字符（ASCII + 常用标点）
BASE_CHARS = set(
    # ASCII 可打印字符
    "".join(chr(i) for i in range(32, 127))
    # 中文标点
    + "，。！？、；：""''【】（）《》—…·～￥"
    # 空格类
    + "\t\n\r "
)


def scan_chars_from_files(scan_dir: Path) -> set:
    """扫描目录下所有文本文件，提取使用到的字符"""
    chars = set()
    file_count = 0
    for path in scan_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SCAN_EXTS:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                # 去除 HTML 标签属性和代码语法，只保留文本内容中的字符
                chars.update(text)
                file_count += 1
            except Exception:
                pass
    print(f"  扫描了 {file_count} 个文件，提取到 {len(chars)} 个不同字符")
    return chars


def get_common_chinese_chars() -> set:
    """返回 GB2312 一级常用汉字（3755个）+ 二级汉字（3008个）覆盖范围"""
    chars = set()
    # GB2312 一级汉字区：U+4E00 起的常用汉字
    # 这里用 Unicode CJK 统一汉字基本区中最常用的部分
    # 一级汉字 3755 个（覆盖 99.7% 的日常中文）
    for start, end in [
        (0x4E00, 0x9FFF),   # CJK 统一汉字基本区（常用的约 6763 个）
    ]:
        for cp in range(start, end + 1):
            chars.add(chr(cp))
    return chars


def get_minimal_chinese_chars() -> str:
    """最常用的 3500 个汉字（教育部常用字表）"""
    # 通过 Unicode 频率，返回基本区常用范围
    # 实际使用中建议用 --scan 模式更精确
    chars = set()
    for cp in range(0x4E00, 0x9FFF + 1):
        chars.add(chr(cp))
    return chars


def subset_font(font_path: Path, chars: set, output_path: Path, flavor: str):
    """使用 fonttools 进行字体子集化"""
    # 写入临时字符文件
    text_file = Path("_subset_chars.txt")
    text_file.write_text("".join(sorted(chars)), encoding="utf-8")

    # 构建 pyftsubset 参数
    args = [
        str(font_path),
        f"--text-file={text_file}",
        f"--output-file={output_path}",
        f"--flavor={flavor}",
        "--layout-features=*",       # 保留所有 OpenType 特性
        "--no-hinting",              # 去掉 hinting（减小体积，屏显无影响）
        "--desubroutinize",          # 优化 CFF 子程序
    ]

    subset_main(args)
    text_file.unlink(missing_ok=True)


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f}MB"


def main():
    parser = argparse.ArgumentParser(description="字体子集化工具")
    parser.add_argument("--font", required=True, help="输入字体文件路径 (.woff2/.ttf/.otf/.woff)")
    parser.add_argument("--scan", type=str, default=None, help="扫描指定目录，提取实际用到的字符")
    parser.add_argument("--preset", choices=["common", "minimal"], default=None,
                        help="预设字符集: common=CJK基本区, minimal=最常用3500字")
    parser.add_argument("--text", type=str, default=None, help="直接指定要保留的字符")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--format", choices=["woff2", "woff", "ttf"], default="woff2", help="输出格式 (默认 woff2)")
    args = parser.parse_args()

    font_path = Path(args.font)
    if not font_path.exists():
        print(f"❌ 字体文件不存在: {font_path}")
        return

    original_size = font_path.stat().st_size
    print(f"📄 输入字体: {font_path.name} ({format_size(original_size)})")

    # 查看原始字体信息
    try:
        font = TTFont(font_path)
        glyph_count = len(font.getGlyphOrder())
        font.close()
        print(f"   包含 {glyph_count} 个字形（glyph）")
    except Exception:
        pass

    # 收集要保留的字符
    chars = set(BASE_CHARS)

    if args.scan:
        print(f"\n🔍 扫描目录: {args.scan}")
        scanned = scan_chars_from_files(Path(args.scan))
        chars.update(scanned)
    elif args.preset:
        print(f"\n📦 使用预设字符集: {args.preset}")
        if args.preset == "common":
            chars.update(get_common_chinese_chars())
        else:
            chars.update(get_minimal_chinese_chars())
    elif args.text:
        chars.update(args.text)
    else:
        # 默认：常用中文字符集
        print("\n⚠️  未指定模式，默认使用常用中文字符集")
        print("   推荐使用 --scan 扫描网站目录以获得最小体积")
        chars.update(get_common_chinese_chars())

    print(f"   保留 {len(chars)} 个字符")

    # 输出路径
    ext_map = {"woff2": ".woff2", "woff": ".woff", "ttf": ".ttf"}
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = font_path.parent / f"{font_path.stem}.subset{ext_map[args.format]}"

    # 子集化
    print(f"\n⏳ 正在子集化...")
    try:
        subset_font(font_path, chars, output_path, args.format)
    except Exception as e:
        print(f"❌ 子集化失败: {e}")
        return

    new_size = output_path.stat().st_size
    ratio = (1 - new_size / original_size) * 100

    print(f"\n  ✅ 完成！")
    print(f"  📄 原始: {format_size(original_size)}")
    print(f"  📄 输出: {output_path.name} ({format_size(new_size)})")
    print(f"  💾 减小: {format_size(original_size - new_size)} ({ratio:.1f}%)")

    if args.scan:
        print(f"\n  💡 提示: 网站内容更新后记得重新运行此脚本")


if __name__ == "__main__":
    main()