import sqlite3

def migrate():
    conn = sqlite3.connect('servease.db')
    cursor = conn.cursor()
    
    # Existing migration
    try:
        cursor.execute("ALTER TABLE services ADD COLUMN images JSON DEFAULT '[]'")
        print("Successfully added 'images' column to 'services' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration error or already applied for services.images: {e}")
        
    try:
        cursor.execute("ALTER TABLE deals ADD COLUMN images JSON DEFAULT '[]'")
        print("Successfully added 'images' column to 'deals' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration error or already applied for deals.images: {e}")
        
    # New migration for users table
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR")
        print("Successfully added 'full_name' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration error or already applied for users.full_name: {e}")
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0")
        print("Successfully added 'is_banned' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration error or already applied for users.is_banned: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
