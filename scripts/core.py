"""Small, independently testable delivery definitions."""
from datetime import datetime
from math import sqrt


def parse_timestamp(value):
    if value is None or str(value).strip() in ('', 'None', 'NaT', 'nan'):
        return None
    return datetime.fromisoformat(str(value))


def classify_delivery(status, purchased, delivered, estimated):
    """A missing or contradictory record must never become an on-time delivery."""
    purchase, actual, promise = map(parse_timestamp, (purchased, delivered, estimated))
    if status != 'delivered':
        return 'Recorded non-delivered status', None
    if not purchase or not actual or not promise:
        return 'Missing delivery/promise timestamp', None
    if actual < purchase or promise.date() < purchase.date():
        return 'Contradictory chronology', None
    return 'Eligible delivered order', max(0, (actual.date() - promise.date()).days)


def wilson_interval(successes, total, z=1.96):
    if not total:
        return None, None
    p = successes / total
    denominator = 1 + z*z/total
    centre = (p + z*z/(2*total)) / denominator
    half = z * sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return max(0, centre-half), min(1, centre+half)
