-- 邻里券：一条查询产出「每个会员一行」的明细
-- 页面上的会员列表、沉睡客明细、发送名单，都是这条查询的结果
--
-- 输入：members（会员号 / 手机号 / 近30日购买次数 / 近7日购买次数 / 历史是否买过）
-- 输出：每个会员一行，带互斥分类、是否可发、不发原因
--
-- 与 metrics.sql 的关系：
--   metrics.sql 只算首页三个数
--   本文件算到人，三个数可以从本文件再聚合出来（见文件末尾的核对查询）

WITH base AS (
    SELECT
        "会员号"                                    AS member_id,
        TRIM(COALESCE("手机号", ''))                 AS phone,
        CAST("近30日购买次数" AS INTEGER)            AS cnt_30d,
        CAST("近7日购买次数"  AS INTEGER)            AS cnt_7d,
        CASE WHEN "历史是否买过" = '是' THEN 1 ELSE 0 END AS ever_bought
    FROM members
),
flagged AS (
    SELECT
        *,
        -- 7 天包含在 30 天里，近 7 日不可能大于近 30 日
        CASE WHEN cnt_7d > cnt_30d THEN 1 ELSE 0 END AS is_conflict,
        CASE WHEN ever_bought = 1 AND cnt_30d = 0 THEN 1 ELSE 0 END AS is_sleeper
    FROM base
),
labeled AS (
    SELECT
        *,
        -- 互斥分类，顺序不能换：先命中先算
        CASE
            WHEN is_conflict = 1 THEN '数据对不上'
            WHEN ever_bought = 0 THEN '从未购买'
            WHEN cnt_30d >= 2    THEN '常购客'
            WHEN cnt_7d  >= 1    THEN '本周到店客'
            WHEN cnt_30d = 1     THEN '低频未到店'
            ELSE '沉睡客'
        END AS category,
        -- 发送名单：沉睡客 + 有手机号 + 近 7 日没来过
        -- 数据矛盾记录近 7 日必然 ≥ 1，会被 cnt_7d = 0 天然挡住
        CASE
            WHEN ever_bought = 1 AND cnt_30d = 0 AND cnt_7d = 0 AND phone <> ''
            THEN 1 ELSE 0
        END AS can_send
    FROM flagged
)
SELECT
    member_id     AS "会员号",
    phone         AS "手机号",
    cnt_30d       AS "近30日购买次数",
    cnt_7d        AS "近7日购买次数",
    ever_bought   AS "历史买过",
    category      AS "分类",
    can_send      AS "今天可发",
    CASE
        WHEN can_send = 1 THEN '—'
        WHEN is_conflict = 1 AND phone = '' THEN '没有手机号，且两个次数对不上'
        WHEN is_conflict = 1 THEN '近 7 日次数大于近 30 日，数据对不上'
        WHEN phone = '' THEN '没有手机号，短信发不出去'
        ELSE category
    END           AS "不发原因"
FROM labeled
ORDER BY member_id;

-- 核对查询：三个数应该和 metrics.sql 完全一致（1000 / 420 / 334）
-- SELECT
--     COUNT(*)                                                        AS "会员总数",
--     SUM(is_sleeper)                                                 AS "沉睡客",
--     SUM(can_send)                                                   AS "今天将发送"
-- FROM labeled;
