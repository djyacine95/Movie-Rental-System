import os
from datetime import date

from flask import Flask, redirect, render_template, request, url_for, flash

from database import create_tables, execute, query_all, query_one

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OVERDUE_DAYS = int(os.environ.get("OVERDUE_DAYS", "7"))


def today_iso():
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    stats = {
        "customers": query_one("SELECT COUNT(*) AS c FROM Customers")["c"],
        "movies": query_one("SELECT COUNT(*) AS c FROM Movies")["c"],
        "active_rentals": query_one(
            "SELECT COUNT(*) AS c FROM Rentals WHERE ReturnDate IS NULL"
        )["c"],
        "total_revenue": query_one(
            "SELECT COALESCE(SUM(Amount), 0) AS s FROM Payments"
        )["s"],
    }
    return render_template("index.html", stats=stats)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


@app.route("/customers")
def customers_list():
    customers = query_all("SELECT * FROM Customers ORDER BY Name")
    return render_template("customers/list.html", customers=customers)


@app.route("/customers/new", methods=["GET", "POST"])
def customers_new():
    if request.method == "POST":
        try:
            execute(
                "INSERT INTO Customers (Name, Email, PhoneNumber, Address) "
                "VALUES (?, ?, ?, ?)",
                (
                    request.form["name"].strip(),
                    request.form["email"].strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("address", "").strip(),
                ),
            )
            flash("Customer added.", "success")
            return redirect(url_for("customers_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("customers/form.html", customer=None)


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def customers_edit(customer_id):
    customer = query_one(
        "SELECT * FROM Customers WHERE CustomerID = ?", (customer_id,)
    )
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("customers_list"))

    if request.method == "POST":
        try:
            execute(
                "UPDATE Customers SET Name = ?, Email = ?, PhoneNumber = ?, Address = ? "
                "WHERE CustomerID = ?",
                (
                    request.form["name"].strip(),
                    request.form["email"].strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("address", "").strip(),
                    customer_id,
                ),
            )
            flash("Customer updated.", "success")
            return redirect(url_for("customers_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("customers/form.html", customer=customer)


# ---------------------------------------------------------------------------
# Movies
# ---------------------------------------------------------------------------


@app.route("/movies")
def movies_list():
    movies = query_all(
        """
        SELECT m.*,
               (SELECT COUNT(*) FROM Rentals r
                 WHERE r.MovieID = m.MovieID AND r.ReturnDate IS NULL) AS Rented
        FROM Movies m
        ORDER BY m.Title
        """
    )
    return render_template("movies/list.html", movies=movies)


@app.route("/movies/new", methods=["GET", "POST"])
def movies_new():
    if request.method == "POST":
        try:
            execute(
                "INSERT INTO Movies (Title, Genre, ReleaseYear, Length, Rating, Price) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    request.form["title"].strip(),
                    request.form.get("genre", "").strip(),
                    int(request.form["release_year"]) if request.form.get("release_year") else None,
                    int(request.form["length"]) if request.form.get("length") else None,
                    request.form.get("rating", "").strip(),
                    float(request.form.get("price") or 0),
                ),
            )
            flash("Movie added.", "success")
            return redirect(url_for("movies_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("movies/form.html", movie=None)


@app.route("/movies/search")
def movies_search():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    availability = request.args.get("availability", "").strip()  # '', 'available', 'rented'

    sql = """
        SELECT m.*,
               (SELECT COUNT(*) FROM Rentals r
                 WHERE r.MovieID = m.MovieID AND r.ReturnDate IS NULL) AS Rented
        FROM Movies m
        WHERE 1 = 1
    """
    params = []
    if q:
        sql += " AND (LOWER(m.Title) LIKE ? OR LOWER(m.Genre) LIKE ?)"
        like = f"%{q.lower()}%"
        params.extend([like, like])
    if genre:
        sql += " AND LOWER(m.Genre) = ?"
        params.append(genre.lower())
    sql += " ORDER BY m.Title"

    movies = query_all(sql, tuple(params))

    if availability == "available":
        movies = [m for m in movies if (m["Rented"] or 0) == 0]
    elif availability == "rented":
        movies = [m for m in movies if (m["Rented"] or 0) > 0]

    genres = query_all(
        "SELECT DISTINCT Genre FROM Movies WHERE Genre IS NOT NULL AND Genre != '' ORDER BY Genre"
    )

    return render_template(
        "movies/search.html",
        movies=movies,
        q=q,
        genre=genre,
        availability=availability,
        genres=genres,
    )


@app.route("/movies/<int:movie_id>/edit", methods=["GET", "POST"])
def movies_edit(movie_id):
    movie = query_one("SELECT * FROM Movies WHERE MovieID = ?", (movie_id,))
    if not movie:
        flash("Movie not found.", "error")
        return redirect(url_for("movies_list"))

    if request.method == "POST":
        try:
            execute(
                "UPDATE Movies SET Title = ?, Genre = ?, ReleaseYear = ?, "
                "Length = ?, Rating = ?, Price = ? WHERE MovieID = ?",
                (
                    request.form["title"].strip(),
                    request.form.get("genre", "").strip(),
                    int(request.form["release_year"]) if request.form.get("release_year") else None,
                    int(request.form["length"]) if request.form.get("length") else None,
                    request.form.get("rating", "").strip(),
                    float(request.form.get("price") or 0),
                    movie_id,
                ),
            )
            flash("Movie updated.", "success")
            return redirect(url_for("movies_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("movies/form.html", movie=movie)


# ---------------------------------------------------------------------------
# Rentals
# ---------------------------------------------------------------------------


@app.route("/rentals")
def rentals_list():
    rentals = query_all(
        """
        SELECT r.RentalID, r.RentalDate, r.ReturnDate,
               c.CustomerID, c.Name AS CustomerName,
               m.MovieID, m.Title AS MovieTitle, m.Price,
               CASE
                 WHEN r.ReturnDate IS NULL
                  AND julianday('now') - julianday(r.RentalDate) > ?
                 THEN 1 ELSE 0
               END AS IsOverdue
        FROM Rentals r
        JOIN Customers c ON c.CustomerID = r.CustomerID
        JOIN Movies m    ON m.MovieID    = r.MovieID
        ORDER BY r.RentalDate DESC, r.RentalID DESC
        """,
        (OVERDUE_DAYS,),
    )
    return render_template("rentals/list.html", rentals=rentals, overdue_days=OVERDUE_DAYS)


@app.route("/rentals/new", methods=["GET", "POST"])
def rentals_new():
    customers = query_all("SELECT CustomerID, Name FROM Customers ORDER BY Name")
    movies = query_all("SELECT MovieID, Title, Price FROM Movies ORDER BY Title")

    if request.method == "POST":
        try:
            execute(
                "INSERT INTO Rentals (CustomerID, MovieID, RentalDate, ReturnDate) "
                "VALUES (?, ?, ?, NULL)",
                (
                    int(request.form["customer_id"]),
                    int(request.form["movie_id"]),
                    request.form.get("rental_date") or today_iso(),
                ),
            )
            flash("Rental recorded.", "success")
            return redirect(url_for("rentals_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template(
        "rentals/new.html",
        customers=customers,
        movies=movies,
        today=today_iso(),
    )


@app.route("/rentals/<int:rental_id>/return", methods=["POST"])
def rentals_return(rental_id):
    return_date = request.form.get("return_date") or today_iso()
    execute(
        "UPDATE Rentals SET ReturnDate = ? WHERE RentalID = ?",
        (return_date, rental_id),
    )
    flash("Return date updated.", "success")
    return redirect(url_for("rentals_list"))


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------


@app.route("/payments")
def payments_history():
    payments = query_all(
        """
        SELECT p.PaymentID, p.Amount, p.PaymentDate,
               r.RentalID, c.Name AS CustomerName, m.Title AS MovieTitle
        FROM Payments p
        JOIN Rentals r   ON r.RentalID    = p.RentalID
        JOIN Customers c ON c.CustomerID  = r.CustomerID
        JOIN Movies m    ON m.MovieID     = r.MovieID
        ORDER BY p.PaymentDate DESC, p.PaymentID DESC
        """
    )
    total = query_one("SELECT COALESCE(SUM(Amount), 0) AS s FROM Payments")["s"]
    return render_template("payments/history.html", payments=payments, total=total)


@app.route("/payments/new", methods=["GET", "POST"])
def payments_new():
    rentals = query_all(
        """
        SELECT r.RentalID, r.RentalDate, r.ReturnDate,
               c.Name AS CustomerName, m.Title AS MovieTitle, m.Price
        FROM Rentals r
        JOIN Customers c ON c.CustomerID = r.CustomerID
        JOIN Movies m    ON m.MovieID    = r.MovieID
        ORDER BY r.RentalDate DESC, r.RentalID DESC
        """
    )

    if request.method == "POST":
        try:
            execute(
                "INSERT INTO Payments (RentalID, Amount, PaymentDate) "
                "VALUES (?, ?, ?)",
                (
                    int(request.form["rental_id"]),
                    float(request.form["amount"]),
                    request.form.get("payment_date") or today_iso(),
                ),
            )
            flash("Payment recorded.", "success")
            return redirect(url_for("payments_history"))
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template("payments/new.html", rentals=rentals, today=today_iso())


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@app.route("/reports")
def reports():
    most_rented = query_all(
        """
        SELECT m.MovieID, m.Title, m.Genre, COUNT(r.RentalID) AS RentalCount
        FROM Movies m
        LEFT JOIN Rentals r ON r.MovieID = m.MovieID
        GROUP BY m.MovieID
        ORDER BY RentalCount DESC, m.Title
        LIMIT 10
        """
    )

    overdue_customers = query_all(
        """
        SELECT c.CustomerID, c.Name, c.Email,
               COUNT(r.RentalID) AS OverdueCount
        FROM Customers c
        JOIN Rentals r ON r.CustomerID = c.CustomerID
        WHERE r.ReturnDate IS NULL
          AND julianday('now') - julianday(r.RentalDate) > ?
        GROUP BY c.CustomerID
        ORDER BY OverdueCount DESC, c.Name
        """,
        (OVERDUE_DAYS,),
    )

    payments_total = query_one(
        "SELECT COALESCE(SUM(Amount), 0) AS s, COUNT(*) AS c FROM Payments"
    )

    payments_by_month = query_all(
        """
        SELECT substr(PaymentDate, 1, 7) AS Month,
               COUNT(*) AS PaymentCount,
               SUM(Amount) AS Total
        FROM Payments
        GROUP BY Month
        ORDER BY Month DESC
        """
    )

    return render_template(
        "reports.html",
        most_rented=most_rented,
        overdue_customers=overdue_customers,
        payments_total=payments_total,
        payments_by_month=payments_by_month,
        overdue_days=OVERDUE_DAYS,
    )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


# Ensure tables exist when the app boots (covers gunicorn / Render).
create_tables()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
