from datetime import date
import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def register(email: str = "user@example.com") -> str:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def category_id(token: str, name: str = "Food") -> str:
    return next(x["id"] for x in client.get("/categories", headers=auth(token)).json() if x["name"] == name)


def test_health_auth_and_seeded_demo_data():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/categories").status_code == 401
    login = client.post("/auth/login", json={"email": "demo@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert len(client.get("/transactions", headers=auth(token)).json()["items"]) > 0


def test_registration_seeds_categories_and_duplicate_is_conflict():
    token = register()
    assert len(client.get("/categories", headers=auth(token)).json()) == 6
    duplicate = client.post("/auth/register", json={"email": "USER@example.com", "password": "password123"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_exists"


def test_resources_are_scoped_to_authenticated_user():
    first = register()
    category = category_id(first)
    created = client.post("/transactions", headers=auth(first), json={"date": "2026-10-01", "description": "Private", "amountCents": 1250, "categoryId": category})
    item_id = created.json()["id"]
    second = register("other@example.com")
    assert client.get(f"/transactions/{item_id}", headers=auth(second)).status_code == 404
    assert client.patch(f"/categories/{category}", headers=auth(second), json={"name": "Stolen"}).status_code == 404


def test_transaction_crud_and_csv_partial_success():
    token = register()
    category = category_id(token)
    created = client.post("/transactions", headers=auth(token), json={"date": "2026-10-01", "description": "Coffee", "amountCents": 450, "categoryId": category})
    assert created.status_code == 201
    item_id = created.json()["id"]
    assert client.patch(f"/transactions/{item_id}", headers=auth(token), json={"amountCents": 500}).json()["amountCents"] == 500
    csv = "date,description,amount,category\n2026-10-02,Lunch,12.50,Food\nnope,Bad,2,Food\n2026-10-03,Unknown,2,Missing\n"
    imported = client.post("/transactions/import", headers={**auth(token), "Content-Type": "text/csv"}, content=csv)
    assert imported.status_code == 200
    assert imported.json()["imported"] == 1
    assert [x["row"] for x in imported.json()["rejected"]] == [3, 4]
    assert client.delete(f"/transactions/{item_id}", headers=auth(token)).status_code == 204


def test_category_delete_requires_reassignment():
    token = register()
    food = category_id(token)
    other = category_id(token, "Other")
    client.post("/transactions", headers=auth(token), json={"date": "2026-10-01", "description": "Meal", "amountCents": 100, "categoryId": food})
    assert client.delete(f"/categories/{food}", headers=auth(token)).status_code == 409
    assert client.delete(f"/categories/{food}?reassign_to={other}", headers=auth(token)).status_code == 204


def test_subscriptions_and_upcoming():
    token = register()
    category = category_id(token, "Software")
    response = client.post("/subscriptions", headers=auth(token), json={"name": "Annual tool", "amountCents": 12000, "billingPeriod": "yearly", "nextRenewalDate": date.today().isoformat(), "categoryId": category})
    assert response.status_code == 201
    assert response.json()["monthlyEquivalentCents"] == 1000
    assert any(x["id"] == response.json()["id"] for x in client.get("/subscriptions/upcoming?days=0", headers=auth(token)).json())
    assert client.patch(f"/subscriptions/{response.json()['id']}", headers=auth(token), json={"status": "cancelled"}).json()["status"] == "cancelled"


def test_data_persists_across_client_lifecycle():
    token = register("persistent@example.com")
    category = category_id(token)
    created = client.post("/transactions", headers=auth(token), json={"date": "2026-10-01", "description": "Persistent", "amountCents": 999, "categoryId": category})
    assert created.status_code == 201
    item_id = created.json()["id"]

    with TestClient(app) as fresh_client:
        login = fresh_client.post("/auth/login", json={"email": "persistent@example.com", "password": "password123"})
        assert login.status_code == 200
        fresh_token = login.json()["access_token"]
        response = fresh_client.get(f"/transactions/{item_id}", headers=auth(fresh_token))
        assert response.status_code == 200
        assert response.json()["description"] == "Persistent"
