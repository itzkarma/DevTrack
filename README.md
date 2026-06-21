# DevTrack

A minimal backend API for tracking engineering issues — engineers file bugs,
set priorities, and update statuses (a stripped-down GitHub Issues).

Built with Django. Domain logic is modelled with OOP classes in
`issues/models.py`, and data is persisted to two JSON files (`issues.json`,
`reporters.json`).

## Requirements

- Python 3.10+
- Django 6.x (`pip install django`)

## How to run

```bash
cd DevTrack
python3 manage.py migrate     # sets up Django's internal tables (admin/auth)
python3 manage.py runserver   # serves at http://127.0.0.1:8000/
```

The API lives under `/api/`. Data files `issues.json` and `reporters.json`
are created automatically in the project root on first write.

> Note: `migrate` is only needed because Django's admin/auth apps require it.
> The DevTrack data itself is stored in JSON, not the database.

## Project structure

```
DevTrack/
  manage.py
  devtrack/
    settings.py        # 'issues' registered in INSTALLED_APPS
    urls.py            # includes issues.urls under /api/
  issues/
    models.py          # OOP classes: BaseEntity, Reporter, Issue, subclasses
    storage.py         # JSON file read/write helpers
    views.py           # endpoint handlers
    urls.py            # /api/reporters/ and /api/issues/ routes
```

## OOP design

- `BaseEntity` — abstract base (`abc.ABC`) with an abstract `validate()` and a
  concrete `to_dict()` that serializes instance attributes.
- `Reporter` and `Issue` inherit from `BaseEntity` and implement `validate()`.
- `Issue.describe()` is overridden by two subclasses:
  - `CriticalIssue` → `"[URGENT] {title} — needs immediate attention"`
  - `LowPriorityIssue` → `"{title} — low priority, handle when free"`
  - medium/high priority issues use the base `Issue.describe()`.

`POST /api/issues/` instantiates the right subclass based on `priority`, calls
`validate()` then `to_dict()`, and adds `describe()` to the response `message`.

## Endpoints

### Reporters

| Method | URL | Description |
| --- | --- | --- |
| POST | `/api/reporters/` | Create a new reporter |
| GET | `/api/reporters/` | List all reporters |
| GET | `/api/reporters/?id=1` | Get a single reporter by ID (404 if missing) |

### Issues

| Method | URL | Description |
| --- | --- | --- |
| POST | `/api/issues/` | Create a new issue (returns `describe()` as `message`) |
| GET | `/api/issues/` | List all issues |
| GET | `/api/issues/?id=1` | Get a single issue by ID (404 if missing) |
| GET | `/api/issues/?status=open` | List issues filtered by status |

**Allowed values** — status: `open`, `in_progress`, `resolved`, `closed`;
priority: `low`, `medium`, `high`, `critical`.

If `id` is omitted on POST, the server assigns the next integer id.

## Example: POST /api/issues/

Request:

```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1
}
```

Response — `201 Created`:

```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1,
  "created_at": "2026-06-21 08:47:16.433016",
  "message": "[URGENT] Login button not working on mobile — needs immediate attention"
}
```

Response — `400 Bad Request` (validation failure):

```json
{ "error": "Title cannot be empty" }
```

Response — `404 Not Found`:

```json
{ "error": "Issue not found" }
```

## Postman screenshots

> Add your screenshots here. Capture at least one success and one failure.

- Success — `POST /api/issues/` returning `201`: _![success](docs/success.png)_
- Failure — `POST /api/issues/` with empty title returning `400`:
  _![failure](docs/failure.png)_

## Design decision

**Plain Python OOP classes for the domain, JSON files for storage — kept
separate from Django's ORM.**

The brief asks to model the data with OOP and persist to JSON files, so the
entities (`Reporter`, `Issue` and its priority subclasses) are plain classes
that own their own `validate()` and `to_dict()` behaviour rather than Django
models. This keeps validation and the polymorphic `describe()` logic in one
place (`models.py`), makes the inheritance hierarchy explicit, and leaves the
views thin — they just parse input, pick the right class, and read/write JSON
via a small `storage.py` helper. The trade-off is no ORM querying or DB-level
integrity, which is acceptable for this minimal tracker.
