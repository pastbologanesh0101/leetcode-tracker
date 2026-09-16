from collections import OrderedDict
from datetime import datetime, date, timedelta, timezone

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash

bp = Blueprint("main", __name__)

DIFFICULTIES = ("Easy", "Medium", "Hard")
STATUSES = ("todo", "attempted", "solved")


def db():
    return current_app.get_db()


@bp.route("/")
def index():
    status = request.args.get("status", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    topic = request.args.get("topic", "").strip()

    query = "SELECT * FROM problem WHERE 1=1"
    params = []

    if status in STATUSES:
        query += " AND status = ?"
        params.append(status)
    if difficulty in DIFFICULTIES:
        query += " AND difficulty = ?"
        params.append(difficulty)
    if topic:
        query += " AND topic LIKE ?"
        params.append(f"%{topic}%")

    query += " ORDER BY created_at DESC"

    problems = db().execute(query, params).fetchall()

    return render_template(
        "index.html",
        problems=problems,
        difficulties=DIFFICULTIES,
        statuses=STATUSES,
        filters={"status": status, "difficulty": difficulty, "topic": topic},
    )


@bp.route("/add", methods=["GET", "POST"])
def add_problem():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        url_val = request.form.get("url", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        topic = request.form.get("topic", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        if difficulty not in DIFFICULTIES:
            errors.append("Difficulty must be one of Easy, Medium, or Hard.")

        if errors:
            for e in errors:
                flash(e)
            return render_template(
                "add.html",
                difficulties=DIFFICULTIES,
                form={
                    "title": title,
                    "url": url_val,
                    "difficulty": difficulty,
                    "topic": topic,
                    "notes": notes,
                },
            ), 400

        db().execute(
            """
            INSERT INTO problem (title, url, difficulty, topic, status, notes, date_solved, created_at)
            VALUES (?, ?, ?, ?, 'todo', ?, NULL, ?)
            """,
            (title, url_val, difficulty, topic, notes, datetime.now(timezone.utc).isoformat()),
        )
        db().commit()
        flash(f'Added "{title}"')
        return redirect(url_for("main.index"))

    return render_template("add.html", difficulties=DIFFICULTIES, form={})


@bp.route("/problem/<int:problem_id>/update", methods=["POST"])
def update_problem(problem_id):
    status = request.form.get("status", "").strip()
    notes = request.form.get("notes", "")

    if status not in STATUSES:
        flash("Invalid status.")
        return redirect(url_for("main.index")), 400

    row = db().execute("SELECT * FROM problem WHERE id = ?", (problem_id,)).fetchone()
    if row is None:
        flash("Problem not found.")
        return redirect(url_for("main.index")), 404

    date_solved = row["date_solved"]
    if status == "solved" and not date_solved:
        date_solved = date.today().isoformat()
    elif status != "solved":
        date_solved = None

    db().execute(
        "UPDATE problem SET status = ?, notes = ?, date_solved = ? WHERE id = ?",
        (status, notes, date_solved, problem_id),
    )
    db().commit()
    flash("Problem updated.")
    return redirect(url_for("main.index"))


@bp.route("/stats")
def stats():
    by_difficulty = OrderedDict((d, 0) for d in DIFFICULTIES)
    for row in db().execute("SELECT difficulty, COUNT(*) AS c FROM problem GROUP BY difficulty"):
        by_difficulty[row["difficulty"]] = row["c"]

    by_status = OrderedDict((s, 0) for s in STATUSES)
    for row in db().execute("SELECT status, COUNT(*) AS c FROM problem GROUP BY status"):
        by_status[row["status"]] = row["c"]

    total = sum(by_status.values())

    solved_rows = db().execute(
        "SELECT date_solved FROM problem WHERE status = 'solved' AND date_solved IS NOT NULL"
    ).fetchall()

    weekly_counts = OrderedDict()
    today = date.today()
    # Build the last 8 ISO weeks so the trend table always has a shape,
    # even with no data yet.
    for i in range(7, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7 * i)
        key = week_start.isocalendar()[:2]  # (iso_year, iso_week)
        weekly_counts[key] = {"label": f"{key[0]}-W{key[1]:02d}", "count": 0}

    for row in solved_rows:
        try:
            d = datetime.strptime(row["date_solved"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        key = d.isocalendar()[:2]
        if key in weekly_counts:
            weekly_counts[key]["count"] += 1
        else:
            weekly_counts[key] = {"label": f"{key[0]}-W{key[1]:02d}", "count": 1}

    trend = sorted(weekly_counts.values(), key=lambda v: v["label"])

    return render_template(
        "stats.html",
        by_difficulty=by_difficulty,
        by_status=by_status,
        total=total,
        trend=trend,
    )
