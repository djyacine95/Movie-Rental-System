"""Initialize the SQLite database and insert sample data."""

from datetime import date, timedelta

from database import create_tables, execute, query_one


def insert_sample_data():
    if query_one("SELECT COUNT(*) AS c FROM Customers")["c"] > 0:
        print("Sample data already exists. Skipping inserts.")
        return

    customers = [
        ("Yacine Djeddi", "yacine@example.com", "555-000-1111", "12 Maple Street, San jose"),
        ("Alexander Singer", "alexander@example.com", "555-222-333", "44 Oak Avenue, San jose"),
        ("William Nguyen", "William@example.com", "555-444-5555", "7 Pine Road, San jose"),
        ("Jim Carrey", "Jim@example.com", "555-333-4444", "88 Birch Lane, New york"),
    ]
    for c in customers:
        execute(
            "INSERT INTO Customers (Name, Email, PhoneNumber, Address) VALUES (?, ?, ?, ?)",
            c,
        )

    movies = [
        ("The Shawshank Redemption", "Drama", 1994, 142, "R", 3.99),
        ("Inception", "Sci-Fi", 2010, 148, "PG-13", 4.49),
        ("The Godfather", "Crime", 1972, 175, "R", 3.99),
        ("Toy Story", "Animation", 1995, 81, "G", 2.99),
        ("The Dark Knight", "Action", 2008, 152, "PG-13", 4.49),
        ("Parasite", "Thriller", 2019, 132, "R", 4.99),
    ]
    for m in movies:
        execute(
            "INSERT INTO Movies (Title, Genre, ReleaseYear, Length, Rating, Price) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            m,
        )

    today = date.today()
    rentals = [
        # (customer_id, movie_id, rental_date, return_date_or_None)
        (1, 1, (today - timedelta(days=10)).isoformat(), (today - timedelta(days=7)).isoformat()),
        (2, 2, (today - timedelta(days=5)).isoformat(), None),
        (3, 3, (today - timedelta(days=12)).isoformat(), None),
        (4, 4, (today - timedelta(days=2)).isoformat(), None),
        (1, 5, (today - timedelta(days=20)).isoformat(), (today - timedelta(days=15)).isoformat()),
    ]
    for r in rentals:
        rental_id = execute(
            "INSERT INTO Rentals (CustomerID, MovieID, RentalDate, ReturnDate) "
            "VALUES (?, ?, ?, ?)",
            r,
        )
        # Insert a payment for completed rentals
        if r[3] is not None:
            movie = query_one("SELECT Price FROM Movies WHERE MovieID = ?", (r[1],))
            execute(
                "INSERT INTO Payments (RentalID, Amount, PaymentDate) VALUES (?, ?, ?)",
                (rental_id, movie["Price"], r[3]),
            )

    print("Sample data inserted.")


if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("Database initialized.")
