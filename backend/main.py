from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import secrets
import uuid
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Category, SessionLocal, Subscription, Transaction, User, get_db, init_db

DateValue = date


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def _check_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$", 2)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode(), expected)
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _token(user_id: str) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({"sub": user_id}, separators=(",", ":")).encode())
    signing = f"{header}.{payload}"
    signature = _b64(hmac.new(app_settings.secret.encode(), signing.encode(), hashlib.sha256).digest())
    return f"{signing}.{signature}"


def _token_user(token: str) -> str | None:
    try:
        header, payload, signature = token.split(".")
        signing = f"{header}.{payload}"
        expected = _b64(hmac.new(app_settings.secret.encode(), signing.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return data.get("sub")
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


class Settings:
    secret = os.getenv("SPENDLENS_SECRET", "development-only-change-me")


app_settings = Settings()


DEFAULT_CATEGORIES = ("Food", "Rent", "Transport", "Entertainment", "Software", "Other")
COLORS = ("#e86f51", "#1f9d8b", "#e3a72f", "#5577b8", "#8b6fc4", "#d05b72")


def seed_store(db: Session | None = None) -> None:
    """Seed the demo account if it is absent, primarily for local development."""
    owns_session = db is None
    db = db or SessionLocal()
    if db.scalar(select(User).where(User.email == "demo@example.com")):
        if owns_session:
            db.close()
        return
    user = User(id=_id("usr"), email="demo@example.com", password_hash=_hash_password("password123"))
    db.add(user)
    db.flush()
    categories = {name: Category(id=_id("cat"), user_id=user.id, name=name) for name in DEFAULT_CATEGORIES}
    db.add_all(categories.values())
    rows = (("2026-08-02", "Market Hall", 6840, "Food"), ("2026-09-03", "Harbor rent", 185000, "Rent"),
            ("2026-09-06", "Cloudflare", 2500, "Software"), ("2026-10-02", "Market Hall", 8160, "Food"),
            ("2026-10-03", "Harbor rent", 185000, "Rent"), ("2026-10-05", "Notion", 1000, "Software"),
            ("2026-10-08", "City bikes", 1980, "Transport"), ("2026-10-10", "Grocery co-op", 6420, "Food"),
            ("2026-10-15", "Rooftop tickets", 3800, "Entertainment"))
    for raw_date, description, amount, category in rows:
        db.add(Transaction(id=_id("tx"), user_id=user.id, date=date.fromisoformat(raw_date), description=description, amount_cents=amount, category_id=categories[category].id))
    for name, amount, period, renewal, category in (("Netflix", 1599, "monthly", "2026-10-24", "Entertainment"), ("Linear", 800, "monthly", "2026-10-28", "Software"), ("Strava", 7999, "yearly", "2027-02-12", "Entertainment")):
        db.add(Subscription(id=_id("sub"), user_id=user.id, name=name, amount_cents=amount, billing_period=period, next_renewal_date=date.fromisoformat(renewal), category_id=categories[category].id))
    db.commit()
    if owns_session:
        db.close()


class ErrorBody(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def error(code: str, message: str, status_code: int, fields: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(content={"error": {"code": code, "message": message, **({"fields": fields} if fields else {})}}, status_code=status_code)


def current_user(authorization: Annotated[str | None, Header()] = None, db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError()
    user_id = _token_user(authorization[7:].strip())
    user = db.get(User, user_id or "")
    if not user:
        raise AuthError()
    return user


class AuthError(Exception):
    pass


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class CategoryInput(BaseModel):
    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()


class TransactionInput(BaseModel):
    date: date
    description: str = Field(min_length=1)
    amountCents: int = Field(gt=0)
    categoryId: str
    source: Literal["manual", "csv"] = "manual"


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: DateValue | None = None
    description: str | None = Field(default=None, min_length=1)
    amountCents: int | None = Field(default=None, gt=0)
    categoryId: str | None = None


class SubscriptionInput(BaseModel):
    name: str = Field(min_length=1)
    amountCents: int = Field(gt=0)
    billingPeriod: Literal["weekly", "monthly", "yearly"]
    nextRenewalDate: date
    categoryId: str


class SubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1)
    amountCents: int | None = Field(default=None, gt=0)
    billingPeriod: Literal["weekly", "monthly", "yearly"] | None = None
    nextRenewalDate: date | None = None
    categoryId: str | None = None
    status: Literal["active", "cancelled"] | None = None


def category_out(item: Category) -> dict[str, str]:
    return {"id": item.id, "name": item.name}


def transaction_out(item: Transaction) -> dict:
    return {"id": item.id, "date": item.date.isoformat(), "description": item.description, "amountCents": item.amount_cents, "categoryId": item.category_id, "source": item.source}


def monthly_equivalent(amount_cents: int, period: str) -> int:
    if period == "monthly":
        return amount_cents
    if period == "yearly":
        return (amount_cents + 6) // 12
    return (amount_cents * 52 + 6) // 12


def subscription_out(item: Subscription) -> dict:
    return {"id": item.id, "name": item.name, "amountCents": item.amount_cents, "billingPeriod": item.billing_period, "nextRenewalDate": item.next_renewal_date.isoformat(), "categoryId": item.category_id, "status": item.status, "monthlyEquivalentCents": monthly_equivalent(item.amount_cents, item.billing_period)}


app = FastAPI(title="SpendLens API", version="0.1.0")
init_db()
seed_store()


@app.exception_handler(AuthError)
async def auth_handler(_: Request, __: AuthError) -> JSONResponse:
    return error("unauthorized", "A valid bearer token is required", 401)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = {str(e["loc"][-1]): e["msg"] for e in exc.errors() if e["loc"][-1] != "body"}
    return error("validation_error", "Request validation failed", 400, fields or None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", status_code=201)
def register(payload: AuthRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        return error("email_exists", "Email is already registered", 409)
    user = User(id=_id("usr"), email=email, password_hash=_hash_password(payload.password))
    db.add(user)
    db.flush()
    for name in DEFAULT_CATEGORIES:
        db.add(Category(id=_id("cat"), user_id=user.id, name=name))
    db.commit()
    return {"access_token": _token(user.id), "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@app.post("/auth/login")
def login(payload: AuthRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not _check_password(payload.password, user.password_hash):
        return error("invalid_credentials", "Invalid email or password", 401)
    return {"access_token": _token(user.id), "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email}


@app.get("/categories")
def list_categories(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [category_out(x) for x in db.scalars(select(Category).where(Category.user_id == user.id)).all()]


@app.post("/categories", status_code=201)
def create_category(payload: CategoryInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(Category).where(Category.user_id == user.id, func.lower(Category.name) == payload.name.casefold())):
        return error("category_exists", "Category name already exists", 409)
    item = Category(id=_id("cat"), user_id=user.id, name=payload.name)
    db.add(item)
    db.commit()
    return category_out(item)


@app.patch("/categories/{item_id}")
def update_category(item_id: str, payload: CategoryInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Category).where(Category.id == item_id, Category.user_id == user.id))
    if not item:
        return error("not_found", "Category not found", 404)
    if db.scalar(select(Category).where(Category.user_id == user.id, Category.id != item_id, func.lower(Category.name) == payload.name.casefold())):
        return error("category_exists", "Category name already exists", 409)
    item.name = payload.name
    db.commit()
    return category_out(item)


@app.delete("/categories/{item_id}", status_code=204)
def delete_category(item_id: str, reassign_to: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Category).where(Category.id == item_id, Category.user_id == user.id))
    if not item:
        return error("not_found", "Category not found", 404)
    used = db.scalars(select(Transaction).where(Transaction.user_id == user.id, Transaction.category_id == item_id)).all()
    subscription_users = db.scalars(select(Subscription).where(Subscription.user_id == user.id, Subscription.category_id == item_id)).all()
    if used or subscription_users:
        replacement = db.scalar(select(Category).where(Category.user_id == user.id, Category.id == (reassign_to or "")))
        if not replacement or replacement.id == item_id:
            return error("category_in_use", "Category has transactions; provide a valid reassign_to", 409)
        for transaction in used:
            transaction.category_id = replacement.id
        for subscription in subscription_users:
            subscription.category_id = replacement.id
    db.delete(item)
    db.commit()
    return Response(status_code=204)


def require_category(db: Session, user_id: str, category_id: str) -> Category | JSONResponse:
    item = db.scalar(select(Category).where(Category.user_id == user_id, Category.id == category_id))
    return item or error("not_found", "Category not found", 404)


@app.get("/transactions")
def list_transactions(from_date: Annotated[date | None, Query(alias="from")] = None, to: date | None = None, category_id: str | None = None, q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Transaction).where(Transaction.user_id == user.id)
    if from_date:
        query = query.where(Transaction.date >= from_date)
    if to:
        query = query.where(Transaction.date <= to)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if q:
        query = query.where(func.lower(Transaction.description).contains(q.casefold()))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(query.order_by(Transaction.date.desc(), Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    start = (page - 1) * page_size
    return {"items": [transaction_out(x) for x in items], "page": page, "pageSize": page_size, "total": total}


@app.post("/transactions", status_code=201)
def create_transaction(payload: TransactionInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = require_category(db, user.id, payload.categoryId)
    if isinstance(category, JSONResponse):
        return category
    item = Transaction(id=_id("tx"), user_id=user.id, date=payload.date, description=payload.description, amount_cents=payload.amountCents, category_id=payload.categoryId, source=payload.source)
    db.add(item)
    db.commit()
    return transaction_out(item)


@app.get("/transactions/{item_id}")
def get_transaction(item_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Transaction).where(Transaction.id == item_id, Transaction.user_id == user.id))
    return transaction_out(item) if item else error("not_found", "Transaction not found", 404)


@app.patch("/transactions/{item_id}")
def update_transaction(item_id: str, payload: TransactionUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Transaction).where(Transaction.id == item_id, Transaction.user_id == user.id))
    if not item:
        return error("not_found", "Transaction not found", 404)
    values = payload.model_dump(exclude_unset=True)
    if "categoryId" in values and not require_category(db, user.id, values["categoryId"]):
        return error("not_found", "Category not found", 404)
    for key, value in values.items():
        setattr(item, {"amountCents": "amount_cents", "categoryId": "category_id"}.get(key, key), value)
    db.commit()
    return transaction_out(item)


@app.delete("/transactions/{item_id}", status_code=204)
def delete_transaction(item_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Transaction).where(Transaction.id == item_id, Transaction.user_id == user.id))
    if not item:
        return error("not_found", "Transaction not found", 404)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@app.post("/transactions/import")
async def import_transactions(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        content = (await request.body()).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        required = {"date", "description", "amount", "category"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            return error("invalid_csv", "CSV must include date,description,amount,category", 400)
    except UnicodeDecodeError:
        return error("invalid_csv", "CSV must be UTF-8", 400)
    imported = 0
    rejected = []
    categories = {x.name.casefold(): x for x in db.scalars(select(Category).where(Category.user_id == user.id)).all()}
    for row_number, row in enumerate(reader, 2):
        raw_date = (row.get("date") or "").strip()
        description = (row.get("description") or "").strip()
        amount = (row.get("amount") or "").strip()
        category = categories.get((row.get("category") or "").strip().casefold())
        parsed_date = None
        try:
            parsed_date = date.fromisoformat(raw_date)
            if not raw_date or len(raw_date) != 10:
                raise ValueError("Date must be YYYY-MM-DD")
            if not description:
                raise ValueError("Description is required")
            decimal_amount = Decimal(amount)
            if decimal_amount <= 0 or decimal_amount.as_tuple().exponent < -2:
                raise ValueError("Amount must be a positive number")
            amount_cents = int((decimal_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if not category:
                raise ValueError("Unknown category")
            db.add(Transaction(id=_id("tx"), user_id=user.id, date=parsed_date, description=description, amount_cents=amount_cents, category_id=category.id, source="csv"))
            imported += 1
        except (ValueError, TypeError, InvalidOperation) as exc:
            message = str(exc)
            if parsed_date is None:
                message = "Date must be YYYY-MM-DD"
            elif not description:
                message = "Description is required"
            elif not category:
                message = "Unknown category"
            elif not amount:
                message = "Amount must be a positive number"
            elif "decimal" in message.lower() or "positive" not in message.lower():
                message = "Amount must be a positive number"
            rejected.append({"row": row_number, "reason": message})
    db.commit()
    return {"imported": imported, "rejected": rejected}


@app.get("/subscriptions")
def list_subscriptions(status_filter: Annotated[str | None, Query(alias="status")] = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Subscription).where(Subscription.user_id == user.id)
    if status_filter:
        query = query.where(Subscription.status == status_filter)
    items = db.scalars(query).all()
    return [subscription_out(x) for x in items]


@app.post("/subscriptions", status_code=201)
def create_subscription(payload: SubscriptionInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = require_category(db, user.id, payload.categoryId)
    if isinstance(category, JSONResponse):
        return category
    item = Subscription(id=_id("sub"), user_id=user.id, name=payload.name, amount_cents=payload.amountCents, billing_period=payload.billingPeriod, next_renewal_date=payload.nextRenewalDate, category_id=payload.categoryId)
    db.add(item)
    db.commit()
    return subscription_out(item)


@app.get("/subscriptions/upcoming")
def upcoming(days: int = Query(14, ge=0), user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = date.today()
    end = today + timedelta(days=days)
    items = db.scalars(select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active", Subscription.next_renewal_date >= today, Subscription.next_renewal_date <= end)).all()
    return [subscription_out(x) for x in items]


@app.get("/subscriptions/{item_id}")
def get_subscription(item_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Subscription).where(Subscription.id == item_id, Subscription.user_id == user.id))
    return subscription_out(item) if item else error("not_found", "Subscription not found", 404)


@app.patch("/subscriptions/{item_id}")
def update_subscription(item_id: str, payload: SubscriptionUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Subscription).where(Subscription.id == item_id, Subscription.user_id == user.id))
    if not item:
        return error("not_found", "Subscription not found", 404)
    values = payload.model_dump(exclude_unset=True)
    if "categoryId" in values and not require_category(db, user.id, values["categoryId"]):
        return error("not_found", "Category not found", 404)
    for key, value in values.items():
        setattr(item, {"amountCents": "amount_cents", "billingPeriod": "billing_period", "nextRenewalDate": "next_renewal_date", "categoryId": "category_id"}.get(key, key), value)
    db.commit()
    return subscription_out(item)


@app.delete("/subscriptions/{item_id}", status_code=204)
def delete_subscription(item_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Subscription).where(Subscription.id == item_id, Subscription.user_id == user.id))
    if not item:
        return error("not_found", "Subscription not found", 404)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


def report_data(user_id: str, month: str, db: Session | None = None) -> dict:
    owns_session = db is None
    db = db or SessionLocal()
    start = date.fromisoformat(f"{month}-01")
    end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
    transactions = db.scalars(select(Transaction).where(Transaction.user_id == user_id, Transaction.date >= start, Transaction.date < end)).all()
    by_category = Counter()
    for transaction in transactions:
        by_category[transaction.category_id] += transaction.amount_cents
    categories = [x for x in db.scalars(select(Category).where(Category.user_id == user_id)).all() if by_category[x.id]]
    category_output = [{"name": x.name, "totalCents": by_category[x.id], "color": COLORS[index % len(COLORS)]} for index, x in enumerate(categories)]
    merchants = Counter()
    for transaction in transactions:
        merchants[transaction.description] += transaction.amount_cents
    subscriptions = db.scalars(select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")).all()
    subscription_total = sum(monthly_equivalent(x.amount_cents, x.billing_period) for x in subscriptions)
    result = {"totalCents": sum(x.amount_cents for x in transactions), "subscriptionCents": subscription_total, "categories": category_output, "topMerchants": [{"name": name, "totalCents": amount} for name, amount in merchants.most_common(5)]}
    if owns_session:
        db.close()
    return result


@app.get("/reports/monthly")
def monthly_report(month: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        date.fromisoformat(f"{month}-01")
        if len(month) != 7:
            raise ValueError
    except ValueError:
        return error("invalid_month", "month must be YYYY-MM", 400)
    return report_data(user.id, month, db)


@app.get("/reports/trend")
def trend_report(months: int = Query(6, ge=1, le=60), user: User = Depends(current_user), db: Session = Depends(get_db)):
    current = date.today().replace(day=1)
    points = []
    for offset in range(months - 1, -1, -1):
        year, month = current.year, current.month - offset
        while month <= 0:
            year -= 1
            month += 12
        key = f"{year:04d}-{month:02d}"
        report = report_data(user.id, key, db)
        points.append({"month": key, "label": date(year, month, 1).strftime("%b %Y"), "totalCents": report["totalCents"], "subscriptionCents": report["subscriptionCents"]})
    return points
