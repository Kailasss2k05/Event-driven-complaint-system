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

def insert_complaint(complaint_id, description, user_id, status="SUBMITTED"):
    """Insert a new complaint into the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO complaints (complaint_id, description, user_id, status)
                VALUES (%s, %s, %s, %s)
                RETURNING complaint_id, status, created_at
                """,
                (complaint_id, description, user_id, status)
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


# Alias for backward compatibility
get_complaint_by_id = get_complaint


def generate_complaint_id():
    """Generate sequential complaint ID in format AA01, AA02, etc."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get the highest existing complaint ID number
            cur.execute(
                "SELECT complaint_id FROM complaints WHERE complaint_id LIKE 'AA%' ORDER BY CAST(SUBSTRING(complaint_id, 3) AS INTEGER) DESC LIMIT 1"
            )
            result = cur.fetchone()
            
            if result:
                # Extract the number part and increment
                last_id = result['complaint_id']
                number_part = int(last_id[2:])  # Remove 'AA' prefix
                new_number = number_part + 1
            else:
                # First complaint
                new_number = 1
            
            # Format with zero padding (AA001, AA002, etc. - 3 digits for better readability)
            return f"AA{new_number:03d}"
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


def get_complaints_by_user(user_id):
    """Get all complaints for a specific user."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM complaints 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                """,
                (user_id,)
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


# ==============================
# User / Auth Operations
# ==============================

def create_user(username, email, password_hash, role="user", department_name=None):
    """Create a new user."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, role, department_name)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, email, role, department_name, created_at
                """,
                (username, email, password_hash, role, department_name)
            )
            result = cur.fetchone()
            conn.commit()
            return result["id"]
    except Exception as e:
        conn.rollback()
        print(f"Failed to create user: {e}")
        raise
    finally:
        conn.close()


def get_user_by_username(username):
    """Get user by username."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_email(email):
    """Get user by email."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, email, role, department_name, is_active, created_at FROM users WHERE id = %s",
                (user_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


# FastAPI dependency for protected routes
from fastapi import Depends, HTTPException, status
from backend.auth.oauth2 import oauth2_scheme
from backend.auth.jwt_handler import decode_access_token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user


# ==============================
# Role-based Access Control Functions
# ==============================

def get_complaints_by_department(department_name):
    """Get all complaints for a specific department."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM complaints 
                WHERE department = %s 
                ORDER BY created_at DESC
                """,
                (department_name,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def can_access_complaint(user, complaint_id):
    """Check if user can access a specific complaint based on role."""
    if user["role"] == "super_admin":
        return True
    
    # Regular users can only access their own complaints
    if user["role"] == "user":
        complaint = get_complaint_by_id(complaint_id)
        return complaint and complaint["user_id"] == user["id"]
    
    # Department admins can access complaints from their department
    if user["role"] == "department_admin" and user["department_name"]:
        complaint = get_complaint_by_id(complaint_id)
        return complaint and complaint["department"] == user["department_name"]
    
    return False


def require_role(*allowed_roles):
    """Decorator to check if user has required role."""
    def role_checker(user = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker


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
