from fontTools.ttLib import TTFont

font = TTFont("E:\\Personal_Website\\huaidejiang.github.io\\assets\\fonts\\SourceHanSerifSC-VF.otf.woff2")

# 从 name 表获取字体族名和子族名（如 "Bold", "Italic"）
for record in font["name"].names:
    if record.nameID in (1, 2, 4, 16, 17):
        print(f"nameID={record.nameID}: {record.toUnicode()}")

# 从 OS/2 表获取 weight 和 italic 标志
os2 = font["OS/2"]
print(f"Weight class: {os2.usWeightClass}")   # 400=Regular, 700=Bold
print(f"fsSelection: {os2.fsSelection}")       # bit 0=Italic, bit 5=Bold

# 从 head 表获取 macStyle
head = font["head"]
print(f"macStyle: {head.macStyle}")            # bit 0=Bold, bit 1=Italic

if "fvar" in font:
    for axis in font["fvar"].axes:
        print(f"轴: {axis.axisTag}, 范围: {axis.minValue} - {axis.maxValue}")
    # 如果有 "wght" 轴，说明支持不同粗细
    # 如果有 "ital" 或 "slnt" 轴，说明支持斜体