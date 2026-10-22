# -*- coding: utf-8 -*-
"""跑 sql/member_list.sql，输出每个会员一行，并核对分类分布。

用法：
    python scripts/run_list.py
    python scripts/run_list.py "数据清洗表格/清洗过后.csv"
"""
import csv
import sqlite3
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql" / "member_list.sql"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "数据清洗表格" / "清洗过后.csv"
if not SRC.is_absolute():
    SRC = (Path.cwd() / SRC).resolve()

ALIAS = {
    "会员号": ["会员号", "会员编号", "归一编号"],
    "手机号": ["手机号", "手机号码"],
    "近30日购买次数": ["近30日购买次数"],
    "近7日购买次数": ["近7日购买次数"],
    "历史是否买过": ["历史是否买过", "历史是否购买", "历史是否购买辅助列"],
}


def main():
    rows = list(csv.reader(SRC.open(encoding="utf-8-sig")))
    header, data = rows[0], rows[1:]

    idx = []
    for std, names in ALIAS.items():
        for n in names:
            if n in header:
                idx.append(header.index(n))
                break
        else:
            raise SystemExit(f"缺列「{std}」，你的表头是 {header}")
    data = [[r[i] if i < len(r) else "" for i in idx] for r in data]

    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute(
        'CREATE TABLE members ("会员号" TEXT, "手机号" TEXT, '
        '"近30日购买次数" TEXT, "近7日购买次数" TEXT, "历史是否买过" TEXT)'
    )
    cur.executemany("INSERT INTO members VALUES (?,?,?,?,?)", data)
    cur.execute(SQL.read_text(encoding="utf-8"))

    cols = [d[0] for d in cur.description]
    result = cur.fetchall()
    ci, si = cols.index("分类"), cols.index("今天可发")

    print(f"\n  数据文件  {SRC.name}")
    print(f"  查询脚本  sql/member_list.sql")
    print(f"  输出列    {' / '.join(cols)}")
    print(f"  行数      {len(result)}\n")

    for r in result[:5]:
        print("   ", r)
    print("    ...")

    dist = Counter(r[ci] for r in result)
    order = ["沉睡客", "常购客", "本周到店客", "低频未到店", "从未购买", "数据对不上"]
    print()
    for k in order:
        print(f"    {k:<8} {dist.get(k, 0)}")
    total_send = sum(r[si] for r in result)
    print(f"    {'可发合计':<8} {total_send}")

    ok = (
        len(result) == 1000
        and dist.get("沉睡客") == 380
        and dist.get("常购客") == 300
        and dist.get("本周到店客") == 120
        and dist.get("低频未到店") == 80
        and dist.get("从未购买") == 80
        and dist.get("数据对不上") == 40
        and total_send == 334
    )
    print("\n  核对 1000 / 380+40 / 334 →", "一致 ✓" if ok else "不一致 ✗", "\n")


if __name__ == "__main__":
    main()
