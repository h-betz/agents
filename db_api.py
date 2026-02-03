import os
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Tuple, Optional, Any


class DBAPI:
    """Database API that can be used as a context manager for connection pooling"""

    def __init__(
        self,
        dbname: str = None,
        user: str = None,
        password: str = None,
        host: str = None,
        port: str = None
    ):
        self.conn = None
        self.cursor = None

        # Store credentials, falling back to environment variables
        self.dbname = dbname or os.environ.get("DB_NAME", "groceries")
        self.user = user or os.environ["DB_USER"]
        self.password = password or os.environ["DB_PASSWORD"]
        self.host = host or os.environ["DB_HOST"]
        self.port = port or os.environ.get("DB_PORT", "5432")

    def __enter__(self):
        """Create a database connection when entering context"""
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context, rollback on error"""
        if exc_type is not None:
            # An exception occurred, rollback
            if self.conn:
                self.conn.rollback()
        else:
            # No exception, commit
            if self.conn:
                self.conn.commit()

        # Clean up
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

        # Don't suppress exceptions
        return False

    def execute(self, query: str, params: Tuple = None) -> Optional[Any]:
        """Execute a single query and return one result"""
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute_with_returning(self, query: str, params: Tuple) -> Optional[Any]:
        """Execute a single insert/update and return the RETURNING value"""
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute_batch(self, query: str, values: List[Tuple]) -> int:
        """Execute a batch insert/update and return the number of rows affected"""
        execute_batch(self.cursor, query, values)
        return self.cursor.rowcount

    def execute_many_with_returning(self, query: str, values: List[Tuple]) -> List[Any]:
        """Execute multiple inserts and collect all RETURNING values"""
        results = []
        for value_tuple in values:
            self.cursor.execute(query, value_tuple)
            result = self.cursor.fetchone()
            if result:
                results.append(result)
        return results
