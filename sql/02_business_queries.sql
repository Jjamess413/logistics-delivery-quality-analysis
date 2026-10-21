-- 1. Control totals and explicit eligible-delivered denominator.
SELECT COUNT(*) AS cohort_orders, SUM(eligible_flag) AS eligible_orders,
       SUM(late_flag) AS late_orders, SUM(eligible_flag-late_flag) AS on_time_orders,
       ROUND(100.0*SUM(eligible_flag-late_flag)/NULLIF(SUM(eligible_flag),0),2) AS on_time_pct,
       ROUND(100.0*SUM(eligible_flag)/NULLIF(COUNT(*),0),2) AS eligibility_pct
FROM fact_delivery;

-- 2. Monthly service change is percentage points, not percentage growth.
WITH monthly AS (
 SELECT purchase_month, COUNT(*) AS orders, SUM(eligible_flag) AS eligible,
        100.0*SUM(eligible_flag-late_flag)/NULLIF(SUM(eligible_flag),0) AS on_time_pct
 FROM fact_delivery GROUP BY purchase_month
), compared AS (
 SELECT *, LAG(on_time_pct) OVER(ORDER BY purchase_month) AS previous_month_otd_pct FROM monthly
)
SELECT purchase_month, orders, eligible, ROUND(on_time_pct,2) AS on_time_pct,
       ROUND(previous_month_otd_pct,2) AS previous_month_otd_pct,
       ROUND(on_time_pct-previous_month_otd_pct,2) AS change_pp FROM compared ORDER BY purchase_month;

-- 3. Prioritise review by late-order volume and show its denominator.
SELECT customer_state, SUM(eligible_flag) AS eligible_orders, SUM(late_flag) AS late_orders,
       ROUND(100.0*SUM(late_flag)/NULLIF(SUM(eligible_flag),0),2) AS late_pct,
       SUM(severe_late_flag) AS over_seven_days_late
FROM fact_delivery GROUP BY customer_state HAVING SUM(eligible_flag)>=100
ORDER BY late_orders DESC,customer_state;

-- 4. Order-level timestamps cannot attribute a multi-seller order to one seller.
SELECT origin_state, customer_state, COUNT(*) AS orders, SUM(eligible_flag) AS eligible_orders,
       SUM(late_flag) AS late_orders,
       ROUND(100.0*SUM(late_flag)/NULLIF(SUM(eligible_flag),0),2) AS late_pct
FROM fact_delivery WHERE seller_count=1
GROUP BY origin_state,customer_state HAVING SUM(eligible_flag)>=100
ORDER BY late_orders DESC,origin_state,customer_state LIMIT 15;

-- 5. Compare stages on the SAME complete, valid timestamp cohort.
SELECT late_band, COUNT(*) AS complete_stage_orders,
       ROUND(AVG(processing_seconds)/86400.0,2) AS mean_purchase_to_handover_days,
       ROUND(AVG(post_handover_seconds)/86400.0,2) AS mean_handover_to_delivery_days,
       ROUND(AVG(delivery_seconds)/86400.0,2) AS mean_total_days
FROM fact_delivery WHERE stage_valid_flag=1 GROUP BY late_band;

-- 6. Association with low scores, with reviewed-order coverage shown.
SELECT late_band, SUM(eligible_flag) AS eligible_orders,
       SUM(reviewed_eligible_flag) AS reviewed_orders, SUM(poor_review_flag) AS low_score_orders,
       ROUND(100.0*SUM(poor_review_flag)/NULLIF(SUM(reviewed_eligible_flag),0),2) AS low_score_pct,
       ROUND(100.0*SUM(reviewed_eligible_flag)/NULLIF(SUM(eligible_flag),0),2) AS review_coverage_pct
FROM fact_delivery GROUP BY late_band;

-- 7. Keep exclusions visible; cancelled/unavailable do not mean lost parcels.
SELECT order_status, eligibility_reason, COUNT(*) AS orders
FROM fact_delivery GROUP BY order_status,eligibility_reason ORDER BY orders DESC;

-- 8. Historical investigation sample, not a live unresolved backlog.
SELECT case_code,purchase_date,customer_state,category,review_priority,late_days,review_score
FROM fact_delivery WHERE priority_rank<=5
ORDER BY priority_rank,late_days DESC,case_code LIMIT 20;

-- 9. Demonstrate the fan-out avoided by pre-aggregating both child tables.
SELECT 'naive_orders_items_reviews_join' AS method, COUNT(*) AS joined_rows,
       COUNT(DISTINCT o.case_code) AS distinct_orders
FROM stg_orders o LEFT JOIN stg_items i USING(case_code) LEFT JOIN stg_reviews r USING(case_code)
UNION ALL
SELECT 'one_row_per_order_model',COUNT(*),COUNT(DISTINCT case_code) FROM fact_delivery;

-- 10. Calendar-date versus literal midnight-deadline sensitivity.
SELECT SUM(eligible_flag) AS eligible_orders,SUM(late_flag) AS calendar_late_orders,
       SUM(CASE WHEN eligible_flag=1 AND delivered_timestamp>estimated_timestamp THEN 1 ELSE 0 END) AS literal_timestamp_late_orders,
       SUM(CASE WHEN eligible_flag=1 AND DATE(delivered_timestamp)=DATE(estimated_timestamp)
                AND delivered_timestamp>estimated_timestamp THEN 1 ELSE 0 END) AS same_day_after_midnight
FROM v_delivery_orders;

-- 11. Review on-time performance alongside elapsed time and promise lead time.
SELECT purchase_month,COUNT(*) AS eligible_orders,
       ROUND(100.0*SUM(1-late_flag)/COUNT(*),4) AS on_time_pct,
       ROUND(AVG(JULIANDAY(DATE(estimated_timestamp))-JULIANDAY(DATE(purchase_timestamp))),4) AS mean_promised_calendar_days,
       ROUND(AVG(delivery_seconds)/86400.0,4) AS mean_actual_elapsed_days
FROM v_delivery_orders WHERE eligible_flag=1 GROUP BY purchase_month ORDER BY purchase_month;
