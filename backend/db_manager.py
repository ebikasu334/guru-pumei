#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Manager Class
- Handles database connections (SQLite and PostgreSQL)
- Provides context manager for safe database operations
- Supports environment variable configuration for Render deployment
"""

import sqlite3
import os
from typing import Optional, Any, Iterator, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import urlparse

class DatabaseManager:
    """Database connection and cursor management class"""

    def __init__(self, db_url: str = None):
        """
        Initialize the DatabaseManager

        Args:
            db_url: Database connection URL (uses DATABASE_URL env var if None)
                   Format: sqlite:///path/to/db or postgresql://user:pass@host:port/dbname
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL', 'sqlite:///db/games.db')
        self._connection = None
        self._db_type = self._determine_db_type()

    def _determine_db_type(self) -> str:
        """Determine database type from connection URL"""
        if self.db_url.startswith('postgresql://') or self.db_url.startswith('postgres://'):
            return 'postgresql'
        elif self.db_url.startswith('sqlite:///'):
            return 'sqlite'
        else:
            # Default to SQLite for backward compatibility
            return 'sqlite'

    def _get_sqlite_connection(self):
        """Get SQLite connection"""
        # Extract path from sqlite:///path/to/db
        db_path = self.db_url.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA case_sensitive_like = ON")
        return conn

    def _get_postgresql_connection(self):
        """Get PostgreSQL connection"""
        # Parse PostgreSQL URL
        if self.db_url.startswith('postgres://'):
            # Convert postgres:// to postgresql:// for psycopg2
            db_url = self.db_url.replace('postgres://', 'postgresql://', 1)
        else:
            db_url = self.db_url

        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        return conn

    def connect(self):
        """
        Establish database connection

        Returns:
            Database connection object (sqlite3.Connection or psycopg2.connection)
        """
        if self._connection is None:
            if self._db_type == 'sqlite':
                self._connection = self._get_sqlite_connection()
            elif self._db_type == 'postgresql':
                self._connection = self._get_postgresql_connection()
        return self._connection

    def close(self) -> None:
        """Close database connection if it exists"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor

        Yields:
            Database cursor object (sqlite3.Cursor or psycopg2.cursor)

        Example:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM games")
                results = cursor.fetchall()
        """
        conn = self.connect()
        if self._db_type == 'sqlite':
            cursor = conn.cursor()
        else:  # postgresql
            cursor = conn.cursor(cursor_factory=DictCursor)

        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions

        Yields:
            Database cursor object within a transaction

        Example:
            with db_manager.transaction() as cursor:
                cursor.execute("INSERT INTO games (...) VALUES (?)", (value,))
                # Automatically committed if no exception
                # Automatically rolled back if exception occurs
        """
        conn = self.connect()
        if self._db_type == 'sqlite':
            cursor = conn.cursor()
        else:  # postgresql
            cursor = conn.cursor(cursor_factory=DictCursor)

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

            if self._db_type == 'sqlite':
                return cursor.fetchall()
            else:  # postgresql
                return [dict(row) for row in cursor.fetchall()]

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

            if self._db_type == 'sqlite':
                return cursor.rowcount
            else:  # postgresql
                return cursor.rowcount

    def get_last_insert_id(self) -> int:
        """
        Get the last inserted row ID

        Returns:
            Last inserted row ID
        """
        conn = self.connect()
        if self._db_type == 'sqlite':
            return conn.total_changes
        else:  # postgresql
            # For PostgreSQL, we need to get the last inserted ID differently
            with self.get_cursor() as cursor:
                cursor.execute("SELECT lastval()")
                result = cursor.fetchone()
                return result[0] if result else 0
