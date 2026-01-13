#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Manager Class
- Handles SQLite connections and cursor management
- Provides context manager for safe database operations
"""

import sqlite3
from typing import Optional, Any, Iterator, Tuple
from contextlib import contextmanager

class DatabaseManager:
    """Database connection and cursor management class"""

    def __init__(self, db_path: str = 'db/games.db'):
        """
        Initialize the DatabaseManager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection

        Returns:
            SQLite connection object
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Enable case-sensitive LIKE for better search
            self._connection.execute("PRAGMA case_sensitive_like = ON")
        return self._connection

    def close(self) -> None:
        """Close database connection if it exists"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def get_cursor(self) -> Iterator[sqlite3.Cursor]:
        """
        Context manager for database cursor

        Yields:
            SQLite cursor object

        Example:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM games")
                results = cursor.fetchall()
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """
        Context manager for database transactions

        Yields:
            SQLite cursor object within a transaction

        Example:
            with db_manager.transaction() as cursor:
                cursor.execute("INSERT INTO games (...) VALUES (?)", (value,))
                # Automatically committed if no exception
                # Automatically rolled back if exception occurs
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def __enter__(self) -> 'DatabaseManager':
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()

    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Execute a SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters (prevents SQL injection)

        Returns:
            List of query results
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            query: SQL query string
            params: Query parameters (prevents SQL injection)

        Returns:
            Number of rows affected
        """
        with self.transaction() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount

    def get_last_insert_id(self) -> int:
        """
        Get the last inserted row ID

        Returns:
            Last inserted row ID
        """
        conn = self.connect()
        return conn.total_changes
