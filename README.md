# LeetCode Tracker

A small Flask + SQLite app for tracking coding-interview practice problems:
add problems you want to solve, filter them by status/difficulty/topic,
update your progress and notes, and see stats on how you're doing.

## Features

- **Add problems** with a title, URL, difficulty (Easy/Medium/Hard), topic
  tags, and notes.
- **List & filter** problems by status (`todo` / `attempted` / `solved`),
  difficulty, or topic.
- **Update** a problem's status and notes in place; marking a problem
  `solved` automatically stamps today's date.
- **Stats view** showing counts by difficulty, counts by status, and a
  solved-per-week trend table for the last 8 weeks.
- Server-rendered Jinja2 templates with plain CSS — no JS framework, no
  build step.

## Project layout

```
leetcode-tracker/
├── app/
│   ├── __init__.py       # app factory (create_app)
│   ├── routes.py         # views: index, add, update, stats
│   ├── templates/        # Jinja2 templates
│   └── static/style.css
├── tests/
│   └── test_app.py       # unit tests using Flask's test client
├── wsgi.py                # entry point for running the dev server
├── requirements.txt
└── .github/workflows/tests.yml
```

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python wsgi.py
```

Then open http://127.0.0.1:5000 in your browser. The SQLite database is
created automatically at `instance/leetcode_tracker.db` on first run.

## Example usage

1. Go to **Add Problem**, fill in:
   - Title: `Two Sum`
   - URL: `https://leetcode.com/problems/two-sum/`
   - Difficulty: `Easy`
   - Topic: `array, hash-map`
2. Submit — it now shows up on the **Problems** page with status `todo`.
3. Once you've attempted it, change its status to `attempted` and jot a note
   like "brute force works, need O(n) with a hash map".
4. Once solved, set status to `solved` — the date is recorded automatically.
5. Visit **Stats** to see totals by difficulty/status and how many problems
   you've solved per week.

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest
```

Tests use `create_app(testing=True)`, which wires up an in-memory SQLite
database, so no files are touched on disk and no dev server needs to be
running.

## CI

`.github/workflows/tests.yml` runs the test suite on every push and pull
request against Python 3.11 and 3.12.

## License

MIT — see [LICENSE](LICENSE).
