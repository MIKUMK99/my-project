# -*- coding: utf-8 -*-
"""
用 SQL 验证首页三个数。

做法：把 CSV 读进内存里的 SQLite 表，执行 sql/metrics.sql，打印结果。
不需要安装任何数据库，Python 自带 sqlite3。

用法：
    python scripts/run_sql.py
    python scripts/run_sql.py "数据清洗表格/清洗过后.csv"
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql" / "metrics.sql"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "数据清洗表格" / "清洗过后.csv"
if not SRC.is_absolute():
    SRC = (Path.cwd() / SRC).resolve()


# 把各种导出表头映射成 sql/metrics.sql 认的 5 个标准列名
ALIAS = {
    "会员号": ["会员号", "会员编号", "归一编号", "归一化编号", "会员ID"],
    "手机号": ["手机号", "手机号码", "手机"],
    "近30日购买次数": ["近30日购买次数", "近30日购买数", "近30日次数"],
    "近7日购买次数": ["近7日购买次数", "近7日购买数", "近7日次数"],
    "历史是否买过": ["历史是否买过", "历史是否购买", "历史是否购买辅助列", "是否买过"],
}


def canon_header(header):
    """把原始表头换成标准列名，返回 (新表头, 各列下标)"""
    picked = {}
    for std, names in ALIAS.items():
        for n in names:
            if n in header:
                picked[std] = header.index(n)
                break
        else:
            raise SystemExit(
                f"缺少列「{std}」。\n你的表头是：{header}\n"
                f"这个脚本要的是清洗后的表：会员号 / 手机号 / 近30日购买次数 / 近7日购买次数 / 历史是否买过"
            )
    return list(picked.keys()), list(picked.values())


def main():
    if not SRC.exists():
        raise SystemExit(f"找不到数据文件：{SRC}")

    with SRC.open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    raw_header, data = rows[0], rows[1:]
    header, idx = canon_header(raw_header)
    data = [[r[i] if i < len(r) else "" for i in idx] for r in data]

    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cols = ", ".join(f'"{h}" TEXT' for h in header)
    cur.execute(f"CREATE TABLE members ({cols})")
    cur.executemany(
        "INSERT INTO members VALUES (%s)" % ",".join("?" * len(header)),
        data,
    )

    cur.execute(SQL.read_text(encoding="utf-8"))
    names = [d[0] for d in cur.description]
    values = cur.fetchone()

    print()
    print(f"  数据文件  {SRC.name}")
    print(f"  查询脚本  sql/metrics.sql")
    print()
    width = [max(len(str(n)), len(str(v)), 4) for n, v in zip(names, values)]
    print("  " + "  ".join(str(n).ljust(w) for n, w in zip(names, width)))
    print("  " + "  ".join("-" * w for w in width))
    print("  " + "  ".join(str(v).ljust(w) for v, w in zip(values, width)))
    print()

    got = dict(zip(names, values))
    ok = (
        got.get("会员总数") == 1000
        and got.get("沉睡客") == 420
        and got.get("今天将发送") == 334
    )
    print("  核对 1000 / 420 / 334 →", "一致 ✓" if ok else "不一致 ✗")
    print()


if __name__ == "__main__":
    main()
