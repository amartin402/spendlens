from datetime import date

from sqlalchemy import select

from backend.db import Category, SessionLocal, Subscription, Transaction, User
from backend.main import monthly_equivalent, report_data


def test_monthly_equivalent_uses_integer_rounding():
    assert monthly_equivalent(12000, "yearly") == 1000
    assert monthly_equivalent(1000, "weekly") == 4333


def test_report_sums_categories_merchants_and_active_subscriptions():
    with SessionLocal() as db:
        user_id = db.scalar(select(User.id))
        categories = {x.name: x for x in db.query(Category).filter_by(user_id=user_id).all()}
        db.query(Transaction).delete()
        db.query(Subscription).delete()
        db.add_all([
            Transaction(id="a", user_id=user_id, date=date(2026, 10, 2), description="Coffee", amount_cents=450, category_id=categories["Food"].id),
            Transaction(id="b", user_id=user_id, date=date(2026, 10, 3), description="Coffee", amount_cents=550, category_id=categories["Food"].id),
            Transaction(id="c", user_id=user_id, date=date(2026, 10, 4), description="Rent", amount_cents=10000, category_id=categories["Rent"].id),
            Subscription(id="active", user_id=user_id, name="Annual", amount_cents=12000, billing_period="yearly", next_renewal_date=date(2027, 1, 1), category_id=categories["Software"].id),
            Subscription(id="cancelled", user_id=user_id, name="Old", amount_cents=5000, billing_period="monthly", next_renewal_date=date(2026, 1, 1), category_id=categories["Software"].id, status="cancelled"),
        ])
        db.commit()
    report = report_data(user_id, "2026-10")
    assert report["totalCents"] == 11000
    assert report["subscriptionCents"] == 1000
    assert report["categories"][:2] == [{"name": "Food", "totalCents": 1000, "color": "#e86f51"}, {"name": "Rent", "totalCents": 10000, "color": "#1f9d8b"}]
    assert report["topMerchants"] == [{"name": "Rent", "totalCents": 10000}, {"name": "Coffee", "totalCents": 1000}]
