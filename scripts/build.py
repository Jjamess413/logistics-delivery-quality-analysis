"""Build the order-grain SQL model, reviewed CSVs and transparent evidence."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys

import numpy as np
import pandas as pd

from core import classify_delivery, wilson_interval
from download_data import main as download_data

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'config.json').read_text())
FACT_COLUMNS = ['case_code','purchase_date','purchase_month','customer_state','origin_state','route_type',
 'category','order_status','item_count','seller_count','eligible_flag','delivered_flag','late_flag',
 'severe_late_flag','late_days','delivery_seconds','processing_seconds','post_handover_seconds',
 'stage_valid_flag','review_score','valid_review_count','reviewed_eligible_flag','poor_review_flag',
 'late_band','review_priority','priority_rank','eligibility_reason','merchandise_cents','freight_cents']


def export(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator='\n', float_format='%.6f')


def write_json(value, path):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def as_cents(series):
    from decimal import Decimal, ROUND_HALF_UP
    return series.map(lambda x: int((Decimal(str(x))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)))


def read_raw(name, columns=None):
    return pd.read_csv(ROOT/'data/raw'/name, usecols=columns, dtype='str', keep_default_na=False)


def metrics(df):
    eligible = df[df.eligible_flag.eq(1)]
    reviewed = int(df.reviewed_eligible_flag.sum())
    n = len(eligible)
    late = int(df.late_flag.sum())
    low, high = wilson_interval(late,n)
    return {'orders': len(df), 'delivered_orders': int(df.delivered_flag.sum()),
      'eligible_orders': n, 'late_orders': late, 'on_time_orders': n-late,
      'on_time_pct': round(100*(n-late)/n,4) if n else None,
      'late_pct': round(100*late/n,4) if n else None,
      'late_rate_wilson_low_pct': round(100*low,4) if n else None,
      'late_rate_wilson_high_pct': round(100*high,4) if n else None,
      'eligibility_pct': round(100*n/len(df),4) if len(df) else None,
      'median_delivery_days': round(float(eligible.delivery_seconds.median()/86400),4) if n else None,
      'p90_delivery_days': round(float(eligible.delivery_seconds.quantile(.9)/86400),4) if n else None,
      'mean_delivery_days': round(float(eligible.delivery_seconds.mean()/86400),4) if n else None,
      'stage_valid_orders': int(df.stage_valid_flag.sum()),
      'mean_processing_days': round(float(df.processing_seconds.mean()/86400),4) if df.processing_seconds.notna().any() else None,
      'mean_post_handover_days': round(float(df.post_handover_seconds.mean()/86400),4) if df.post_handover_seconds.notna().any() else None,
      'severe_late_orders': int(df.severe_late_flag.sum()), 'reviewed_eligible_orders': reviewed,
      'poor_review_orders': int(df.poor_review_flag.sum()),
      'poor_review_pct': round(100*int(df.poor_review_flag.sum())/reviewed,4) if reviewed else None,
      'review_coverage_pct': round(100*reviewed/n,4) if n else None}


def grouped(df, columns):
    values=[]
    for keys, frame in df.groupby(columns,dropna=False,sort=True):
        if not isinstance(keys,tuple): keys=(keys,)
        values.append(dict(zip(columns,keys)) | metrics(frame))
    return pd.DataFrame(values)


def main():
    download_data()
    processed, reports = ROOT/'data/processed', ROOT/'reports'
    processed.mkdir(exist_ok=True)
    source_counts={}
    orders=read_raw('olist_orders_dataset.csv')
    customers=read_raw('olist_customers_dataset.csv',['customer_id','customer_state'])
    items=read_raw('olist_order_items_dataset.csv')
    products=read_raw('olist_products_dataset.csv',['product_id','product_category_name'])
    sellers=read_raw('olist_sellers_dataset.csv',['seller_id','seller_state'])
    translation=read_raw('product_category_name_translation.csv')
    reviews=read_raw('olist_order_reviews_dataset.csv',['review_id','order_id','review_score','review_creation_date','review_answer_timestamp'])
    for name,df in [('orders',orders),('customers',customers),('items',items),('products',products),('sellers',sellers),('reviews',reviews)]:
        source_counts[name]=len(df)
    for frame,key in [(orders,'order_id'),(customers,'customer_id'),(products,'product_id'),(sellers,'seller_id'),(translation,'product_category_name')]:
        if frame[key].duplicated().any(): raise ValueError('Duplicate join key: '+key)
    if items.duplicated(['order_id','order_item_id']).any(): raise ValueError('Duplicate order/item key')
    if not set(items.order_id)<=set(orders.order_id): raise ValueError('Orphan source item')
    all_codes={key:'ORD-'+str(i+1).zfill(6) for i,key in enumerate(sorted(orders.order_id))}
    in_period=orders.order_purchase_timestamp.ge(CONFIG['purchase_start']) & orders.order_purchase_timestamp.lt(CONFIG['purchase_end_exclusive'])
    cohort=orders[in_period].copy()
    cohort=cohort.merge(customers,on='customer_id',how='left',validate='one_to_one')
    if cohort.customer_state.isna().any(): raise ValueError('Unmatched customer geography')
    cohort['case_code']=cohort.order_id.map(all_codes)
    mapping=cohort.set_index('order_id').case_code.to_dict()
    staged=cohort.rename(columns={'order_purchase_timestamp':'purchase_timestamp','order_approved_at':'approved_timestamp',
      'order_delivered_carrier_date':'handover_timestamp','order_delivered_customer_date':'delivered_timestamp',
      'order_estimated_delivery_date':'estimated_timestamp'})
    staged=staged[['case_code','purchase_timestamp','approved_timestamp','handover_timestamp','delivered_timestamp','estimated_timestamp','order_status','customer_state']].replace('',None)
    item_cohort=items[items.order_id.isin(mapping)].copy()
    item_cohort=item_cohort.merge(products,on='product_id',how='left',validate='many_to_one')
    item_cohort=item_cohort.merge(translation,on='product_category_name',how='left',validate='many_to_one')
    item_cohort=item_cohort.merge(sellers,on='seller_id',how='left',validate='many_to_one')
    if item_cohort.seller_state.isna().any(): raise ValueError('Unknown item seller geography')
    seller_codes={key:i+1 for i,key in enumerate(sorted(sellers.seller_id))}
    item_cohort['case_code']=item_cohort.order_id.map(mapping)
    item_cohort['item_number']=item_cohort.order_item_id.astype(int)
    item_cohort['seller_key']=item_cohort.seller_id.map(seller_codes)
    item_cohort['origin_state']=item_cohort.seller_state
    item_cohort['category']=item_cohort.product_category_name_english.fillna('Unknown category').replace('','Unknown category')
    item_cohort['price_cents']=as_cents(item_cohort.price)
    item_cohort['freight_cents']=as_cents(item_cohort.freight_value)
    item_stage=item_cohort[['case_code','item_number','seller_key','origin_state','category','price_cents','freight_cents']]
    review_stage=reviews[reviews.order_id.isin(mapping)].copy()
    review_stage['case_code']=review_stage.order_id.map(mapping)
    review_stage['review_key']=review_stage.review_id
    review_stage['review_score']=pd.to_numeric(review_stage.review_score,errors='coerce')
    review_stage=review_stage.rename(columns={'review_creation_date':'created_timestamp','review_answer_timestamp':'answered_timestamp'})
    review_stage=review_stage[['review_key','case_code','review_score','created_timestamp','answered_timestamp']].replace('',None)
    database=processed/'logistics.sqlite'
    database.unlink(missing_ok=True)
    with sqlite3.connect(database) as db:
        db.executescript((ROOT/'sql/00_schema.sql').read_text())
        for table,frame in [('stg_orders',staged),('stg_items',item_stage),('stg_reviews',review_stage)]:
            frame.to_sql(table,db,if_exists='append',index=False)
        db.executescript((ROOT/'sql/01_delivery_model.sql').read_text())
        fact=pd.read_sql_query('SELECT * FROM v_delivery_orders ORDER BY case_code',db)
        fact[FACT_COLUMNS].to_sql('fact_delivery',db,index=False,if_exists='replace')
        db.execute('CREATE UNIQUE INDEX fact_case_key ON fact_delivery(case_code)')
        db.execute('CREATE INDEX fact_month_state ON fact_delivery(purchase_month,customer_state)')
        promise=pd.read_sql_query('''SELECT purchase_month,COUNT(*) AS eligible_orders,
          100.0*SUM(1-late_flag)/COUNT(*) AS on_time_pct,
          AVG(JULIANDAY(DATE(estimated_timestamp))-JULIANDAY(DATE(purchase_timestamp))) AS mean_promised_calendar_days,
          AVG(delivery_seconds)/86400.0 AS mean_actual_elapsed_days
          FROM v_delivery_orders WHERE eligible_flag=1 GROUP BY purchase_month ORDER BY purchase_month''',db)
        export(promise,reports/'promise_lead_time.csv')
        db.commit()
    reference=[classify_delivery(r.order_status,r.purchase_timestamp,r.delivered_timestamp,r.estimated_timestamp) for r in fact.itertuples()]
    independent_ok=all(reason==r.eligibility_reason and (days==r.late_days if days is not None else pd.isna(r.late_days)) for r,(reason,days) in zip(fact.itertuples(),reference))
    checks={
      'source_orders_unique': not orders.order_id.duplicated().any(),
      'one_fact_row_per_cohort_order':len(fact)==len(cohort)==fact.case_code.nunique(),
      'independent_python_delivery_rules_match_sql':independent_ok,
      'item_counts_reconcile':int(fact.item_count.sum())==len(item_stage),
      'merchandise_cents_reconcile':int(fact.merchandise_cents.sum())==int(item_stage.price_cents.sum()),
      'freight_cents_reconcile':int(fact.freight_cents.sum())==int(item_stage.freight_cents.sum()),
      'eligible_partition_reconciles':int(fact.eligible_flag.sum())==int((fact.late_flag.eq(1)|((fact.eligible_flag.eq(1))&fact.late_flag.eq(0))).sum()),
      'ineligible_duration_is_null':fact.loc[fact.eligible_flag.eq(0),'delivery_seconds'].isna().all(),
      'all_delivery_durations_nonnegative':fact.delivery_seconds.dropna().ge(0).all(),
      'joint_stage_durations_sum_to_total':((fact.processing_seconds+fact.post_handover_seconds-fact.delivery_seconds).dropna().abs()<=1).all(),
      'review_denominator_bounded':int(fact.poor_review_flag.sum())<=int(fact.reviewed_eligible_flag.sum())<=int(fact.eligible_flag.sum()),
      'no_customer_or_source_order_ids_in_export':not any('customer_id' in col or col in ['order_id','review_id'] for col in FACT_COLUMNS),
      'all_purchase_dates_in_cohort':fact.purchase_date.ge(CONFIG['purchase_start']).all() and fact.purchase_date.lt(CONFIG['purchase_end_exclusive']).all()
    }
    if not all(checks.values()): raise AssertionError(checks)
    numeric_ints=['item_count','seller_count','eligible_flag','delivered_flag','late_flag','severe_late_flag','late_days',
      'delivery_seconds','processing_seconds','post_handover_seconds','stage_valid_flag','review_score','valid_review_count',
      'reviewed_eligible_flag','poor_review_flag','priority_rank','merchandise_cents','freight_cents']
    for col in numeric_ints: fact[col]=fact[col].astype('Int64')
    export(fact[FACT_COLUMNS],processed/'fact_delivery.csv')
    dates=pd.DataFrame({'date':pd.date_range(CONFIG['purchase_start'],pd.Timestamp(CONFIG['purchase_end_exclusive'])-pd.Timedelta(days=1))})
    dates['month']=dates.date.dt.strftime('%Y-%m'); dates['year']=dates.date.dt.year
    dates['month_number']=dates.date.dt.month; dates['date']=dates.date.dt.strftime('%Y-%m-%d')
    export(dates,processed/'dim_date.csv')
    states=grouped(fact,['customer_state']).sort_values('late_orders',ascending=False).reset_index(drop=True)
    states['late_volume_rank']=np.arange(1,len(states)+1)
    export(states[['customer_state','late_volume_rank']],processed/'dim_state.csv')
    categories=pd.DataFrame({'category':sorted(fact.category.unique())})
    categories['category_label']=categories.category.str.replace('_',' ',regex=False).str.title()
    export(categories,processed/'dim_category.csv')
    monthly=grouped(fact,['purchase_month'])
    monthly['otd_change_pp']=monthly.on_time_pct.diff().round(4)
    export(monthly,reports/'monthly_delivery.csv')
    export(states,reports/'state_performance.csv')
    export(grouped(fact,['category']),reports/'category_performance.csv')
    lanes=grouped(fact[fact.seller_count.eq(1)],['origin_state','customer_state'])
    lanes['comparison_eligible']=lanes.eligible_orders.ge(CONFIG['comparison_minimum_orders']).astype(int)
    export(lanes.sort_values('late_orders',ascending=False),reports/'single_seller_lanes.csv')
    export(grouped(fact,['late_band']),reports/'review_association.csv')
    export(grouped(fact,['route_type']),reports/'route_type_performance.csv')
    export(fact.groupby(['order_status','eligibility_reason'],dropna=False).size().reset_index(name='orders'),reports/'cohort_reconciliation.csv')
    queue=fact[fact.priority_rank.le(5)].sort_values(['priority_rank','late_days','case_code'],ascending=[True,False,True])
    export(queue[['case_code','purchase_date','customer_state','category','review_priority','late_days','review_score','processing_seconds','post_handover_seconds']].head(100),reports/'historical_review_sample.csv')
    summary=metrics(fact)
    summary.update({'purchase_start':CONFIG['purchase_start'],'purchase_end_exclusive':CONFIG['purchase_end_exclusive'],
      'source_counts':source_counts,'cohort_excluded_orders':len(orders)-len(cohort),
      'multi_seller_orders':int(fact.seller_count.gt(1).sum()),
      'multiple_valid_review_orders':int(fact.valid_review_count.gt(1).sum()),
      'naive_timestamp_late_orders':int(((pd.to_datetime(fact.delivered_timestamp,errors='coerce')>pd.to_datetime(fact.estimated_timestamp,errors='coerce'))&fact.eligible_flag.eq(1)).sum()),
      'cohort_max_delivery_date':str(fact.delivered_timestamp.dropna().max())[:10]})
    write_json(summary,reports/'summary.json')
    quality={'passed':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()},'checks_count':len(checks),
      'data_grain':'One row per purchase-cohort order','raw_source_rows':source_counts,'cohort_orders':len(fact),
      'fact_sha256':hashlib.sha256((processed/'fact_delivery.csv').read_bytes()).hexdigest(),
      'desktop_validation':'Not performed; source project requires owner Windows refresh'}
    write_json(quality,reports/'validation.json')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
