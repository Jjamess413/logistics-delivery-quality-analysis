"""Embed a compact anonymised order model in a self-contained offline dashboard."""
from pathlib import Path
import calendar
from datetime import datetime
import hashlib
import json
import sqlite3

ROOT=Path(__file__).resolve().parents[1]


def main():
    with sqlite3.connect(ROOT/'data/processed/logistics.sqlite') as db:
        db.row_factory=sqlite3.Row
        rows=[dict(r) for r in db.execute('SELECT * FROM v_delivery_orders ORDER BY case_code')]
    fields={'months':'purchase_month','states':'customer_state','categories':'category','routes':'route_type',
      'statuses':'order_status','reasons':'eligibility_reason','origins':'origin_state'}
    lists={key:sorted({row[col] for row in rows}) for key,col in fields.items()}
    maps={key:{v:i for i,v in enumerate(values)} for key,values in lists.items()}
    packed=[]
    for r in rows:
        purchase=calendar.timegm(datetime.fromisoformat(r['purchase_timestamp']).timetuple())
        promise=int(calendar.timegm(datetime.fromisoformat(r['estimated_timestamp']).timetuple())/86400) if r['estimated_timestamp'] else None
        packed.append([int(r['case_code'].split('-')[1]),purchase,maps['months'][r['purchase_month']],maps['states'][r['customer_state']],
          maps['categories'][r['category']],maps['routes'][r['route_type']],maps['statuses'][r['order_status']],r['eligible_flag'],
          r['late_days'],r['delivery_seconds'],r['processing_seconds'],r['post_handover_seconds'],r['review_score'],r['valid_review_count'],
          r['seller_count'],r['priority_rank'],maps['reasons'][r['eligibility_reason']],promise,maps['origins'][r['origin_state']]])
    data=lists|{'rows':packed,'summary':json.loads((ROOT/'reports/summary.json').read_text()),
      'license':'CC BY-NC-SA 4.0','source':'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce'}
    payload=json.dumps(data,separators=(',',':'),ensure_ascii=False,allow_nan=False).replace('</','<\\/')
    template=(ROOT/'dashboard/template.html').read_text()
    assert template.count('__DATA__')==1
    html=template.replace('__DATA__',payload)
    output=ROOT/'dashboard/index.html';output.write_text(html)
    checks={'orders_match_summary':len(rows)==data['summary']['orders'],
      'eligible_count_matches':sum(r[7] for r in packed)==data['summary']['eligible_orders'],
      'late_count_matches':sum(r[7] and r[8]>0 for r in packed)==data['summary']['late_orders'],
      'no_customer_identifiers_or_review_text':not any(x in html for x in ['customer_unique_id','review_comment_message','customer_zip_code_prefix']),
      'one_row_per_case':len({r[0] for r in packed})==len(packed),'no_external_scripts':'src="http' not in html}
    result={'passed':all(checks.values()),'checks':checks,'embedded_order_rows':len(rows),'html_bytes':output.stat().st_size,
      'html_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'grain':'One anonymised order; no source order/customer/seller/review identifiers or free text'}
    (ROOT/'reports/dashboard_data_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
