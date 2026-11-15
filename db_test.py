
from db import get_connection


def test_connection():
    with get_connection() as connection:
        print("Database connection successful!")
        print("Connected using Thick mode:", not connection.thin)

        with connection.cursor() as cursor:
            cursor.execute("SELECT USER FROM DUAL")
            print("Connected schema:", cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM OWNER")
            print("Total registered owners:", cursor.fetchone()[0])


if __name__ == "__main__":
    test_connection()
