NOT_FOUND_ID = "00000000-0000-0000-0000-000000000000"


def test_create_job(client):
    response = client.post("/jobs", json={"command": "echo hello"})
    assert response.status_code == 201
    body = response.json()
    assert body["command"] == "echo hello"
    assert body["status"] == "PENDING"
    assert "id" in body


def test_get_job(client):
    created = client.post("/jobs", json={"command": "echo hi"}).json()

    response = client.get(f"/jobs/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_job_not_found(client):
    response = client.get(f"/jobs/{NOT_FOUND_ID}")
    assert response.status_code == 404


def test_get_job_logs_empty(client):
    created = client.post("/jobs", json={"command": "echo hi"}).json()

    response = client.get(f"/jobs/{created['id']}/logs")
    assert response.status_code == 200
    assert response.json() == []


def test_get_job_logs_not_found(client):
    response = client.get(f"/jobs/{NOT_FOUND_ID}/logs")
    assert response.status_code == 404
