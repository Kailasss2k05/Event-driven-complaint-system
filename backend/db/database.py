import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Create a new database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


# ==============================
# Complaint Operations
# ==============================

def insert_complaint(complaint_id, description, status="SUBMITTED"):
    """Insert a new complaint into the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO complaints (complaint_id, description, status)
                VALUES (%s, %s, %s)
                RETURNING complaint_id, status, created_at
                """,
                (complaint_id, description, status)
            )
            result = cur.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Failed to insert complaint: {e}")
        raise
    finally:
        conn.close()


def update_complaint_categorized(complaint_id, category, priority, severity, department):
    """Update complaint after ML categorization."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE complaints
                SET category = %s,
                    priority = %s,
                    severity = %s,
                    department = %s,
                    status = 'CATEGORIZED',
                    updated_at = NOW()
                WHERE complaint_id = %s
                RETURNING complaint_id, status
                """,
                (category, priority, severity, department, complaint_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Failed to update complaint: {e}")
        raise
    finally:
        conn.close()


def update_complaint_assigned(complaint_id, assigned_to):
    """Update complaint after department assignment."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE complaints
                SET assigned_to = %s,
                    status = 'ASSIGNED',
                    updated_at = NOW()
                WHERE complaint_id = %s
                RETURNING complaint_id, status
                """,
                (assigned_to, complaint_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Failed to update complaint assignment: {e}")
        raise
    finally:
        conn.close()


def update_complaint_status(complaint_id, status):
    """Update complaint status."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE complaints
                SET status = %s,
                    updated_at = NOW()
                WHERE complaint_id = %s
                RETURNING complaint_id, status, updated_at
                """,
                (status, complaint_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Failed to update complaint status: {e}")
        raise
    finally:
        conn.close()


def get_complaint(complaint_id):
    """Get a single complaint by ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM complaints WHERE complaint_id = %s",
                (complaint_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_all_complaints():
    """Get all complaints ordered by newest first."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM complaints ORDER BY created_at DESC"
            )
            return cur.fetchall()
    finally:
        conn.close()


# ==============================
# Event / Audit Operations
# ==============================

def insert_event(complaint_id, topic, event_data, status):
    """Insert a complaint event into the audit trail."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO complaint_events
                    (complaint_id, topic, event_data, status)
                VALUES (%s, %s, %s, %s)
                RETURNING event_id, created_at
                """,
                (complaint_id, topic, json.dumps(event_data), status)
            )
            result = cur.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        print(f"Failed to insert event: {e}")
        raise
    finally:
        conn.close()


def get_complaint_events(complaint_id):
    """Get all events for a complaint (audit trail)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM complaint_events
                WHERE complaint_id = %s
                ORDER BY created_at ASC
                """,
                (complaint_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def init_db():
    """Run the schema SQL to initialize tables."""
    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "schema.sql"
    )

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
            conn.commit()
            print("Database initialized successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
