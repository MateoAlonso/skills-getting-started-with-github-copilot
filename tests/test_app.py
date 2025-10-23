from fastapi.testclient import TestClient
import pytest

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    # Run each test with a fresh copy of participants to avoid test interdependence
    original = {
        name: {k: (v.copy() if isinstance(v, list) else v) for k, v in data.items()}
        for name, data in activities.items()
    }
    yield
    # restore
    activities.clear()
    activities.update(original)


client = TestClient(app)


def test_root_redirects_to_static_index():
    r = client.get("/")
    assert r.status_code == 200
    # ultimately serves the static index.html; content-type should be html
    assert "text/html" in r.headers.get("content-type", "")


def test_get_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    json = r.json()
    assert isinstance(json, dict)
    assert "Soccer Team" in json


def test_signup_success_and_prevent_double_signup():
    email = "newstudent@mergington.edu"
    r = client.post(f"/activities/Soccer Team/signup", params={"email": email})
    assert r.status_code == 200
    assert email in activities["Soccer Team"]["participants"]

    # trying to sign up for another activity should be rejected because already signed up
    r2 = client.post(f"/activities/Art Club/signup", params={"email": email})
    assert r2.status_code == 400
    assert r2.json()["detail"] == "Student already signed up for an activity"


def test_signup_activity_not_found():
    r = client.post(f"/activities/Nonexistent/signup", params={"email": "x@x.com"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Activity not found"


def test_remove_participant_success_and_not_found():
    email = "tom@mergington.edu"
    # add then remove
    activities["Art Club"]["participants"].append(email)
    r = client.delete(f"/activities/Art Club/participants", params={"email": email})
    assert r.status_code == 200
    assert email not in activities["Art Club"]["participants"]

    # removing non-existent participant returns 404
    r2 = client.delete(f"/activities/Art Club/participants", params={"email": "noone@x.com"})
    assert r2.status_code == 404
    assert r2.json()["detail"] == "Participant not found in activity"


def test_remove_participant_activity_not_found():
    r = client.delete(f"/activities/Nope/participants", params={"email": "x@x.com"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Activity not found"
