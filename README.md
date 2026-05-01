# Movie Rental System

A simple movie rental management web app built with **Python Flask**, **SQLite**
(via the standard library `sqlite3` - no ORM), and **Jinja2** templates.

## Features

- **Customers** - list, add, edit
- **Movies** - list, add, edit, see availability
- **Rentals** - list, record new rental, mark returned, flag overdue
- **Payments** - record payment, view history
- **Reports** - most rented movies, customers with overdue rentals, total payments

## Project structure

```
movie-rental/
├── app.py             # All Flask routes
├── database.py        # SQLite connection + query helpers
├── init_db.py         # Create tables and insert sample data
├── requirements.txt   # Flask, gunicorn
├── templates/         # All Jinja2 templates
├── .gitignore
└── README.md
```

## Run locally

Requires Python 3.10+.

```bash
cd movie-rental
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create the SQLite database and seed sample data
python init_db.py

# Start the dev server on http://localhost:5000
python app.py
```

The SQLite file is written to `movies.db` by default. Override with the
`DATABASE_PATH` environment variable if you want to put it elsewhere.

### Useful environment variables

| Variable        | Default            | Purpose                                       |
| --------------- | ------------------ | --------------------------------------------- |
| `PORT`          | `5000`             | Port the dev server binds to                  |
| `DATABASE_PATH` | `movies.db`        | Path to the SQLite database file              |
| `SECRET_KEY`    | `dev-secret-...`   | Flask session secret (set a real one in prod) |
| `OVERDUE_DAYS`  | `7`                | Days after which an open rental is overdue    |


## Notes

- No ORM. All SQL is plain parameterised `sqlite3` queries.
- No JavaScript frameworks. Plain HTML + a tiny bit of CSS in `base.html`.
- The SQLite database file is excluded from git via `.gitignore`.
