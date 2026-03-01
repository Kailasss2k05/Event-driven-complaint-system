"""
Script to seed admin users for each department.
"""
import os
import sys
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    # Parse the URL
    url = urlparse(database_url)
    
    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password,
            sslmode="require",
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def seed_admin_users():
    """Add admin users for each department."""
    conn = get_connection()
    
    # Default password for all admin accounts
    default_password = "admin123"
    hashed_password = hash_password(default_password)
    
    admin_users = [
        # Super Admin
        ("superadmin", "superadmin@municipality.gov", hashed_password, "super_admin", None),
        
        # Department Admins
        ("engineering_admin", "engineering.admin@municipality.gov", hashed_password, "department_admin", "Engineering Department"),
        ("health_admin", "health.admin@municipality.gov", hashed_password, "department_admin", "Health Department"),
        ("revenue_admin", "revenue.admin@municipality.gov", hashed_password, "department_admin", "Revenue Department"),
        
        # Sample Regular Users
        ("testuser1", "user1@example.com", hashed_password, "user", None),
        ("testuser2", "user2@example.com", hashed_password, "user", None),
    ]
    
    try:
        with conn.cursor() as cur:
            print("Seeding admin users...")
            
            for username, email, password_hash, role, department_name in admin_users:
                # Check if user already exists
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                existing_user = cur.fetchone()
                
                if existing_user:
                    print(f"User {username} already exists, skipping...")
                    continue
                
                # Insert new user
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, role, department_name, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, email, password_hash, role, department_name, True))
                
                print(f"Created user: {username} (role: {role})")
            
            conn.commit()
            print("Admin users seeded successfully!")
            print(f"Default password for all admin accounts: {default_password}")
            
    except Exception as e:
        conn.rollback()
        print(f"Failed to seed admin users: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running admin users seeding...")
    seed_admin_users()
    print("Seeding complete!")