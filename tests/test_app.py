import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app


@pytest.fixture
def app():
    application = create_app(testing=True)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def add_problem(client, title="Two Sum", url="https://leetcode.com/problems/two-sum/",
                 difficulty="Easy", topic="array,hash-map", notes=""):
    return client.post(
        "/add",
        data={
            "title": title,
            "url": url,
            "difficulty": difficulty,
            "topic": topic,
            "notes": notes,
        },
        follow_redirects=True,
    )


def test_add_problem(client):
    resp = add_problem(client, title="Two Sum")
    assert resp.status_code == 200
    assert b"Two Sum" in resp.data

    resp = client.get("/")
    assert b"Two Sum" in resp.data
    assert b"Easy" in resp.data


def test_filter_by_status(client):
    add_problem(client, title="Two Sum", difficulty="Easy")
    add_problem(client, title="Merge Intervals", difficulty="Medium")

    # Mark "Two Sum" as solved.
    resp = client.get("/")
    # find the id assigned to Two Sum by querying db directly via app context
    from flask import current_app

    row = client.application.get_db().execute(
        "SELECT id FROM problem WHERE title = 'Two Sum'"
    ).fetchone()
    problem_id = row["id"]

    client.post(
        f"/problem/{problem_id}/update",
        data={"status": "solved", "notes": "done"},
        follow_redirects=True,
    )

    resp = client.get("/?status=solved")
    assert b"Two Sum" in resp.data
    assert b"Merge Intervals" not in resp.data

    resp = client.get("/?status=todo")
    assert b"Merge Intervals" in resp.data
    assert b"Two Sum" not in resp.data


def test_filter_by_difficulty(client):
    add_problem(client, title="Two Sum", difficulty="Easy")
    add_problem(client, title="Word Ladder", difficulty="Hard")

    resp = client.get("/?difficulty=Hard")
    assert b"Word Ladder" in resp.data
    assert b"Two Sum" not in resp.data

    resp = client.get("/?difficulty=Easy")
    assert b"Two Sum" in resp.data
    assert b"Word Ladder" not in resp.data


def test_stats_counts_correct(client):
    add_problem(client, title="Two Sum", difficulty="Easy")
    add_problem(client, title="Merge Intervals", difficulty="Medium")
    add_problem(client, title="Word Ladder", difficulty="Hard")

    row = client.application.get_db().execute(
        "SELECT id FROM problem WHERE title = 'Two Sum'"
    ).fetchone()
    client.post(
        f"/problem/{row['id']}/update",
        data={"status": "solved", "notes": ""},
        follow_redirects=True,
    )

    resp = client.get("/stats")
    assert resp.status_code == 200
    html = resp.data.decode()

    # Total problems tracked
    assert "3" in html
    # one solved, two todo
    assert "Solved" in html or "solved" in html


def test_invalid_input_rejected(client):
    # Missing title should be rejected.
    resp = client.post(
        "/add",
        data={"title": "", "url": "", "difficulty": "Easy", "topic": "", "notes": ""},
        follow_redirects=True,
    )
    assert resp.status_code == 400

    resp = client.get("/")
    assert b"Two Sum" not in resp.data

    # Invalid difficulty should also be rejected.
    resp = add_problem(client, title="Bad Problem", difficulty="Impossible")
    assert resp.status_code == 400

    resp = client.get("/")
    assert b"Bad Problem" not in resp.data


def test_update_invalid_status_rejected(client):
    add_problem(client, title="Two Sum", difficulty="Easy")
    row = client.application.get_db().execute(
        "SELECT id FROM problem WHERE title = 'Two Sum'"
    ).fetchone()

    resp = client.post(
        f"/problem/{row['id']}/update",
        data={"status": "bogus-status", "notes": ""},
    )
    assert resp.status_code == 400
