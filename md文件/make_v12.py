# -*- coding: utf-8 -*-
"""基于 作品集_邻里券.md 生成 v1.2：只加分页控制，不改任何文字内容。"""
import pathlib
import re

base = pathlib.Path(__file__).parent
src = base / "作品集_邻里券.md"
dst = base / "作品集_邻里券-v1.2.md"

text = src.read_text(encoding="utf-8")

style = """<style>
@media print {
  @page { size: A4; margin: 18mm 16mm; }
  h1, h2, h3 { page-break-after: avoid; break-after: avoid; }
  img { page-break-inside: avoid; break-inside: avoid; page-break-after: avoid; break-after: avoid; max-width: 100%; }
  table { page-break-inside: auto; }
  tr, td, th { page-break-inside: avoid; break-inside: avoid; }
  thead { display: table-header-group; }
  p, li, blockquote { orphans: 3; widows: 3; }
  pre, code { page-break-inside: avoid; break-inside: avoid; }
}
</style>

"""

BREAK = '\n<div style="page-break-before: always; break-before: page;"></div>\n\n'

lines = text.split("\n")
out = []
first_h2_done = False

for i, ln in enumerate(lines):
    # 一级大节另起一页（## 一、二、三…；包括「## 目录」）
    if re.match(r"^## ", ln):
        if first_h2_done:
            out.append(BREAK.rstrip("\n"))
        first_h2_done = True
    # 公式附录那张超大表单独起页，避免被拦腰切断
    if ln.startswith("### 五、计算公式与附录"):
        out.append(BREAK.rstrip("\n"))
    out.append(ln)

doc = style + "\n".join(out)

# 图片单独成块，避免图片和它下面的说明被拆到两页
doc = re.sub(
    r"(?m)^(!\[[^\]]*\]\([^)]+\))([ \t]*)$",
    r'<div style="page-break-inside: avoid; break-inside: avoid;">\1</div>\2',
    doc,
)

dst.write_text(doc, encoding="utf-8")
print("已生成", dst.name)
print("原文件行数", len(text.split("\n")), "→ 新文件行数", len(doc.split("\n")))
print("新增分页符", doc.count("page-break-before"), "处")
print("图片块", doc.count('<div style="page-break-inside: avoid; break-inside: avoid;">'), "处")
