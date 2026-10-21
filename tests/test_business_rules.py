from pathlib import Path
import sqlite3
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from core import classify_delivery, wilson_interval


class DeliveryRules(unittest.TestCase):
    def test_same_promised_day_is_on_time_after_midnight(self):
        reason,late=classify_delivery('delivered','2018-01-01 12:00:00','2018-01-05 23:59:59','2018-01-05 00:00:00')
        self.assertEqual((reason,late),('Eligible delivered order',0))

    def test_one_day_late_is_calendar_difference(self):
        self.assertEqual(classify_delivery('delivered','2018-01-01','2018-01-06 00:00:01','2018-01-05')[1],1)

    def test_missing_actual_is_excluded(self):
        self.assertEqual(classify_delivery('delivered','2018-01-01',None,'2018-01-05'),('Missing delivery/promise timestamp',None))

    def test_cancelled_is_not_classified_as_delivery_failure(self):
        self.assertEqual(classify_delivery('canceled','2018-01-01',None,'2018-01-05'),('Recorded non-delivered status',None))

    def test_negative_delivery_and_promise_chronology_excluded(self):
        for actual,promise in [('2017-12-31','2018-01-05'),('2018-01-06','2017-12-31')]:
            self.assertEqual(classify_delivery('delivered','2018-01-01',actual,promise),('Contradictory chronology',None))

    def test_unknown_denominator_has_no_interval(self):
        self.assertEqual(wilson_interval(0,0),(None,None))

    def test_interval_does_not_rank_one_late_order_as_certain_failure(self):
        lo,hi=wilson_interval(1,1)
        self.assertAlmostEqual(lo,0.2065432915,places=8)
        self.assertAlmostEqual(hi,1,places=8)

    def database(self):
        db=sqlite3.connect(':memory:')
        db.executescript((ROOT/'sql/00_schema.sql').read_text())
        db.execute("INSERT INTO stg_orders VALUES ('ORD-A','2018-01-01 00:00:00',NULL,'2018-01-02 00:00:00','2018-01-05 12:00:00','2018-01-05 00:00:00','delivered','SP')")
        db.execute("INSERT INTO stg_orders VALUES ('ORD-B','2018-01-01 00:00:00',NULL,'2017-12-31 00:00:00','2018-01-07 00:00:00','2018-01-05 00:00:00','delivered','RJ')")
        db.executemany('INSERT INTO stg_items VALUES (?,?,?,?,?,?,?)',[
          ('ORD-A',1,1,'SP','books',1000,200),('ORD-A',2,2,'RJ','toys',2000,300),('ORD-B',1,1,'SP','books',500,100)])
        db.executemany('INSERT INTO stg_reviews VALUES (?,?,?,?,?)',[
          ('R1','ORD-A',1,'2018-01-06','2018-01-07'),('R2','ORD-A',5,'2018-01-07','2018-01-08'),('R3','ORD-B',2,'2018-01-08','2018-01-09')])
        db.executescript((ROOT/'sql/01_delivery_model.sql').read_text())
        return db

    def test_two_one_to_many_tables_do_not_multiply_order_metrics(self):
        with self.database() as db:
            actual=db.execute('SELECT COUNT(*),SUM(item_count),SUM(merchandise_cents),SUM(freight_cents) FROM v_delivery_orders').fetchone()
            self.assertEqual(actual,(2,3,3500,600))
            naive=db.execute('SELECT COUNT(*) FROM stg_orders LEFT JOIN stg_items USING(case_code) LEFT JOIN stg_reviews USING(case_code)').fetchone()[0]
            self.assertEqual(naive,5)

    def test_latest_review_and_multi_seller_labels(self):
        with self.database() as db:
            row=db.execute("SELECT review_score,valid_review_count,category,route_type,poor_review_flag FROM v_delivery_orders WHERE case_code='ORD-A'").fetchone()
            self.assertEqual(row,(5,2,'Multiple categories','Multiple sellers',0))

    def test_invalid_handover_does_not_remove_valid_delivery_outcome(self):
        with self.database() as db:
            row=db.execute("SELECT eligible_flag,late_days,stage_valid_flag,processing_seconds FROM v_delivery_orders WHERE case_code='ORD-B'").fetchone()
            self.assertEqual(row,(1,2,0,None))


if __name__=='__main__': unittest.main()
