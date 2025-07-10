import sqlite3
from datetime import datetime

def clean_expired_premium_users(db_path='premium_users.db'):
    """
    Atomically removes users whose premium subscription has expired.
    Returns count of removed users and maintains database integrity.
    """
    try:
        # Atomic operation using connection as context manager
        with sqlite3.connect(db_path) as conn:
            conn.execute("BEGIN TRANSACTION;")  # Explicit transaction start
            
            # Get current timestamp in ISO format (UTC)
            current_time = datetime.utcnow().isoformat()
            
            # 1. First count how many will be deleted (for logging)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM premium_users 
                WHERE end_date < ?;
            """, (current_time,))
            expired_count = cursor.fetchone()[0]
            
            # 2. Perform the deletion
            if expired_count > 0:
                cursor.execute("""
                    DELETE FROM premium_users 
                    WHERE end_date < ?;
                """, (current_time,))
                
            conn.commit()  # Finalize transaction
            
            print(f"Removed {expired_count} expired premium users")
            return expired_count
            
    except sqlite3.Error as e:
        print(f"Database error during cleanup: {e}")
        conn.rollback()  # Ensure atomicity on failure
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 0

if __name__ == "__main__":
    clean_expired_premium_users()