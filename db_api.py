import os
import psycopg2

conn = psycopg2.connect(
    dbname="groceries",
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"]
)


class DBAPI:

    @staticmethod
    def execute(query, params):
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except BaseException as e:
            conn.rollback()
            raise
