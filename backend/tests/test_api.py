from datetime import date, timedelta


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.com"
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "dup@b.com", "password": "password123"})
    r = client.post("/auth/register", json={"email": "dup@b.com", "password": "password123"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "c@b.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "c@b.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_applications_require_auth(client):
    assert client.get("/applications").status_code == 401


def test_create_and_list_application(client, auth_headers):
    r = client.post(
        "/applications",
        json={"company": "Example Corp", "role": "Software Engineering Intern", "status": "applied"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["company"] == "Example Corp"
    r = client.get("/applications", headers=auth_headers)
    assert len(r.json()) == 1


def test_status_filter(client, auth_headers):
    client.post("/applications", json={"company": "A", "role": "SWE Intern", "status": "saved"}, headers=auth_headers)
    client.post("/applications", json={"company": "B", "role": "SWE Intern", "status": "applied"}, headers=auth_headers)
    r = client.get("/applications?status=applied", headers=auth_headers)
    assert len(r.json()) == 1
    assert r.json()[0]["company"] == "B"


def test_update_and_delete_application(client, auth_headers):
    app_id = client.post(
        "/applications", json={"company": "A", "role": "SWE Intern"}, headers=auth_headers
    ).json()["id"]
    r = client.put(f"/applications/{app_id}", json={"status": "interview"}, headers=auth_headers)
    assert r.json()["status"] == "interview"
    assert client.delete(f"/applications/{app_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/applications/{app_id}", headers=auth_headers).status_code == 404


def test_users_cannot_see_each_others_applications(client, auth_headers):
    app_id = client.post(
        "/applications", json={"company": "Private", "role": "SWE Intern"}, headers=auth_headers
    ).json()["id"]
    client.post("/auth/register", json={"email": "other@b.com", "password": "password123"})
    token = client.post("/auth/login", data={"username": "other@b.com", "password": "password123"}).json()["access_token"]
    other = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/applications/{app_id}", headers=other).status_code == 404
    assert client.get("/applications", headers=other).json() == []


def test_stats(client, auth_headers):
    soon = (date.today() + timedelta(days=5)).isoformat()
    client.post("/applications", json={"company": "A", "role": "SWE Intern", "status": "applied", "deadline": soon}, headers=auth_headers)
    client.post("/applications", json={"company": "B", "role": "ML Intern", "status": "saved"}, headers=auth_headers)
    r = client.get("/stats", headers=auth_headers)
    data = r.json()
    assert data["total"] == 2
    assert data["by_status"]["applied"] == 1
    assert data["by_status"]["saved"] == 1
    assert len(data["upcoming_deadlines"]) == 1
    assert data["upcoming_deadlines"][0]["company"] == "A"
