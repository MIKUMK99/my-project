# -*- coding: utf-8 -*-
"""
把清洗后的会员表转成原型用的 data.js。

为什么需要这一步：浏览器不允许本地 HTML 直接读本地 CSV/XLSX（file:// 协议的安全限制），
所以数据要「冻」成一个 js 文件，相当于把接口响应静态化。

用法：
    python scripts/csv_to_data_js.py                    # 读 数据清洗表格/清洗过后.csv
    python scripts/csv_to_data_js.py 我的数据.csv        # 读指定文件
输出：
    原型/data.js
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
STAT_DATE = "2026-10-20"
for a in sys.argv[1:]:
    if a.startswith("--date="):
        STAT_DATE = a.split("=", 1)[1]
SRC = Path(ARGS[0]) if ARGS else ROOT / "数据清洗表格" / "清洗过后.csv"
if not SRC.is_absolute():
    SRC = (Path.cwd() / SRC).resolve()
OUT = ROOT / "原型" / "data.js"

# 允许列名有几种写法，方便直接用自己导出的表
ALIAS = {
    "id": ["会员号", "会员编号", "归一编号", "归一化编号", "会员ID"],
    "phone": ["手机号", "手机号码", "手机"],
    "c30": ["近30日购买次数", "近30日购买数", "近30日次数"],
    "c7": ["近7日购买次数", "近7日购买数", "近7日次数"],
    "ever": ["历史是否买过", "历史是否购买", "历史是否购买辅助列", "是否买过"],
}


def pick(header, names):
    for n in names:
        if n in header:
            return n
    raise SystemExit(
        f"找不到列「{names[0]}」。\n"
        f"这个脚本要的是【清洗后】的表，5 列：\n"
        f"  会员号 / 手机号 / 近30日购买次数 / 近7日购买次数 / 历史是否买过\n"
        f"你给的表头是：{header}\n"
        f"如果给的是原始导出（含下单数、取消数），先按教程 4.3 减掉取消数，再导出成 5 列。"
    )


def to_half(s):
    return "".join(chr(ord(c) - 0xFEE0) if 0xFF01 <= ord(c) <= 0xFF5E else c for c in s)


def num(s):
    s = to_half(str(s)).strip().replace("次", "")
    return 0 if s == "" else int(float(s))


def flag(s):
    return to_half(str(s)).strip().upper() in ("是", "Y", "YES", "1", "TRUE")


def mask(p):
    p = to_half(str(p)).strip().replace(" ", "").replace("-", "")
    if p.startswith("+86"):
        p = p[3:]
    return p[:3] + "****" + p[-4:] if len(p) >= 7 else ""


def main():
    with SRC.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        cols = {k: pick(header, v) for k, v in ALIAS.items()}
        rows = list(reader)

    out = []
    for r in rows:
        mid = to_half(r[cols["id"]]).strip().upper().replace("-", "").replace(" ", "")
        if not mid:
            continue
        out.append({
            "id": mid,
            "p": mask(r[cols["phone"]]),
            "c30": num(r[cols["c30"]]),
            "c7": num(r[cols["c7"]]),
            "e": flag(r[cols["ever"]]),
        })

    ids = [m["id"] for m in out]
    if len(set(ids)) != len(ids):
        print(f"⚠ 会员号有重复：{len(ids)} 行只有 {len(set(ids))} 个唯一编号，先去重再生成")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = (
        'window.STAT_DATE = "' + STAT_DATE + '";\n'
        + "window.MEMBERS = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
        + """
document.addEventListener("DOMContentLoaded", function () {
  var els = document.querySelectorAll("[data-stat-date]");
  for (var i = 0; i < els.length; i++) els[i].textContent = window.STAT_DATE;
});
"""
    )
    OUT.write_text(body, encoding="utf-8")

    sleep = [m for m in out if m["e"] and m["c30"] == 0]
    send = [m for m in sleep if m["p"] and m["c7"] == 0]
    print(f"读取 {SRC.name}：{len(out)} 人")
    print(f"沉睡客 {len(sleep)}，可发送 {len(send)}")
    print(f"统计日 {STAT_DATE}")
    print(f"已写入 {OUT}")
    if len(out) != 1000 or len(sleep) != 420 or len(send) != 334:
        print("⚠ 与预期（1000 / 420 / 334）不一致，页面上的数字会和 04_页面数字 对不上")


if __name__ == "__main__":
    main()
