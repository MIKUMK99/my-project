-- 邻里券：用一段 SQL 复现首页三个数
-- 统计日 2026-10-20。members 表由 scripts/run_sql.py 从 数据清洗表格/清洗过后.csv 载入。
--
-- 口径：
--   常购客     = 近30日购买次数 >= 2
--   沉睡客     = 历史买过 且 近30日购买次数 = 0
--   本周到店客 = 近7日购买次数 >= 1
--   发送名单   = 沉睡客 且 有手机号 且 近7日 = 0 且 无数据矛盾
--   数据矛盾   = 近7日购买次数 > 近30日购买次数（7 天包含在 30 天里，不可能成立）

WITH base AS (
    SELECT
        "会员号"                                   AS member_id,
        TRIM(COALESCE("手机号", ''))                AS phone,
        CAST("近30日购买次数" AS INTEGER)           AS cnt_30d,
        CAST("近7日购买次数"  AS INTEGER)           AS cnt_7d,
        CASE WHEN "历史是否买过" = '是' THEN 1 ELSE 0 END AS ever_bought
    FROM members
),
flagged AS (
    SELECT
        *,
        CASE WHEN cnt_7d > cnt_30d THEN 1 ELSE 0 END AS is_conflict,
        CASE WHEN ever_bought = 1 AND cnt_30d = 0 THEN 1 ELSE 0 END AS is_sleeper
    FROM base
)
SELECT
    COUNT(*)                                                        AS "会员总数",
    SUM(is_sleeper)                                                 AS "沉睡客",
    SUM(CASE WHEN is_sleeper = 1
              AND is_conflict = 0
              AND phone <> ''
              AND cnt_7d = 0
             THEN 1 ELSE 0 END)                                     AS "今天将发送",
    -- 下面三个是核对用的中间数，不出现在页面上
    SUM(CASE WHEN is_sleeper = 1 AND phone = '' THEN 1 ELSE 0 END)   AS "沉睡客无手机号",
    SUM(is_conflict)                                                AS "数据矛盾",
    SUM(CASE WHEN is_sleeper = 1 AND is_conflict = 1 AND phone = '' THEN 1 ELSE 0 END)
                                                                    AS "重复扣减"
FROM flagged;
