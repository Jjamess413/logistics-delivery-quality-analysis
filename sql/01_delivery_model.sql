-- Aggregate one-to-many children BEFORE joining them to the order grain.
CREATE VIEW v_item_rollup AS
SELECT case_code, COUNT(*) AS item_count, COUNT(DISTINCT seller_key) AS seller_count,
       CASE WHEN COUNT(DISTINCT category)=1 THEN MAX(category) ELSE 'Multiple categories' END AS category,
       CASE WHEN COUNT(DISTINCT seller_key)=1 THEN MAX(origin_state) ELSE 'MULTI' END AS origin_state,
       SUM(price_cents) AS merchandise_cents, SUM(freight_cents) AS freight_cents
FROM stg_items GROUP BY case_code;

-- Latest valid response per order. The final tie-breaker is deterministic,
-- not evidence that tied review records have an intrinsic temporal order.
CREATE VIEW v_latest_review AS
WITH ranked AS (
 SELECT *, COUNT(*) OVER (PARTITION BY case_code) AS valid_review_count,
        ROW_NUMBER() OVER (PARTITION BY case_code ORDER BY
          COALESCE(answered_timestamp,'') DESC, COALESCE(created_timestamp,'') DESC, review_key DESC) AS rn
 FROM stg_reviews WHERE review_score BETWEEN 1 AND 5
)
SELECT case_code, review_score, valid_review_count FROM ranked WHERE rn=1;

CREATE VIEW v_delivery_orders AS
WITH joined AS (
 SELECT o.*, COALESCE(i.item_count,0) AS item_count, COALESCE(i.seller_count,0) AS seller_count,
        COALESCE(i.category,'Unknown category') AS category,
        COALESCE(i.origin_state,'UNKNOWN') AS origin_state,
        COALESCE(i.merchandise_cents,0) AS merchandise_cents, COALESCE(i.freight_cents,0) AS freight_cents,
        r.review_score, COALESCE(r.valid_review_count,0) AS valid_review_count,
        CASE WHEN o.order_status!='delivered' THEN 'Recorded non-delivered status'
             WHEN o.delivered_timestamp IS NULL OR o.estimated_timestamp IS NULL
               THEN 'Missing delivery/promise timestamp'
             WHEN o.delivered_timestamp<o.purchase_timestamp
               OR DATE(o.estimated_timestamp)<DATE(o.purchase_timestamp)
               THEN 'Contradictory chronology'
             ELSE 'Eligible delivered order' END AS eligibility_reason
 FROM stg_orders o LEFT JOIN v_item_rollup i USING(case_code)
 LEFT JOIN v_latest_review r USING(case_code)
), flags AS (
 SELECT *, CASE WHEN eligibility_reason='Eligible delivered order' THEN 1 ELSE 0 END AS eligible_flag,
        CASE WHEN order_status='delivered' THEN 1 ELSE 0 END AS delivered_flag,
        CASE WHEN seller_count=1 AND origin_state=customer_state THEN 'Same state'
             WHEN seller_count=1 AND origin_state NOT IN ('MULTI','UNKNOWN') THEN 'Cross state'
             WHEN seller_count>1 THEN 'Multiple sellers' ELSE 'Unknown origin' END AS route_type
 FROM joined
), durations AS (
 SELECT *, DATE(purchase_timestamp) AS purchase_date, SUBSTR(purchase_timestamp,1,7) AS purchase_month,
        CASE WHEN eligible_flag=1 THEN MAX(0,CAST(JULIANDAY(DATE(delivered_timestamp))-
             JULIANDAY(DATE(estimated_timestamp)) AS INTEGER)) END AS late_days,
        CASE WHEN eligible_flag=1 THEN CAST(ROUND((JULIANDAY(delivered_timestamp)-
             JULIANDAY(purchase_timestamp))*86400) AS INTEGER) END AS delivery_seconds,
        CASE WHEN eligible_flag=1 AND handover_timestamp>=purchase_timestamp
             AND handover_timestamp<=delivered_timestamp THEN 1 ELSE 0 END AS stage_valid_flag
 FROM flags
), scored AS (
 SELECT *, CASE WHEN late_days>0 THEN 1 ELSE 0 END AS late_flag,
        CASE WHEN late_days>7 THEN 1 ELSE 0 END AS severe_late_flag,
        CASE WHEN stage_valid_flag=1 THEN CAST(ROUND((JULIANDAY(handover_timestamp)-
             JULIANDAY(purchase_timestamp))*86400) AS INTEGER) END AS processing_seconds,
        CASE WHEN stage_valid_flag=1 THEN CAST(ROUND((JULIANDAY(delivered_timestamp)-
             JULIANDAY(handover_timestamp))*86400) AS INTEGER) END AS post_handover_seconds,
        CASE WHEN eligible_flag=1 AND review_score BETWEEN 1 AND 5 THEN 1 ELSE 0 END AS reviewed_eligible_flag,
        CASE WHEN eligible_flag=1 AND review_score BETWEEN 1 AND 2 THEN 1 ELSE 0 END AS poor_review_flag
 FROM durations
)
SELECT *,
  CASE WHEN eligible_flag=0 THEN 'Not eligible' WHEN late_days=0 THEN 'On time'
       WHEN late_days<=7 THEN '1-7 days late' ELSE 'Over 7 days late' END AS late_band,
  CASE WHEN delivered_flag=1 AND eligible_flag=0 THEN 'Data quality review'
       WHEN late_days>7 AND poor_review_flag=1 THEN 'Severe delay + poor feedback'
       WHEN late_days>7 THEN 'Severe delay'
       WHEN late_days>0 AND poor_review_flag=1 THEN 'Late + poor feedback'
       WHEN late_days>0 THEN 'Late delivery'
       WHEN eligible_flag=0 THEN 'Other recorded status' ELSE 'On time' END AS review_priority,
  CASE WHEN delivered_flag=1 AND eligible_flag=0 THEN 1
       WHEN late_days>7 AND poor_review_flag=1 THEN 2 WHEN late_days>7 THEN 3
       WHEN late_days>0 AND poor_review_flag=1 THEN 4 WHEN late_days>0 THEN 5
       WHEN eligible_flag=0 THEN 6 ELSE 7 END AS priority_rank
FROM scored;
