"""
Check and verify admin user in production database
"""
import psycopg2
import bcrypt

PROD_DB = "postgresql://arrivapp_user:Kzu0qp96GCgBJ482q5FX54tAP1Jxre0D@dpg-d4aoe7ili9vc73dheug0-a.frankfurt-postgres.render.com/arrivapp"

def check_admin():
    try:
        conn = psycopg2.connect(PROD_DB)
        cur = conn.cursor()
        
        print("Checking production database for admin user...")
        
        # Check if admin exists
        cur.execute("SELECT id, username, email, hashed_password, is_admin FROM users WHERE username = %s", ("admin",))
        admin = cur.fetchone()
        
        if admin:
            print(f"\n✓ Admin user found:")
            print(f"  ID: {admin[0]}")
            print(f"  Username: {admin[1]}")
            print(f"  Email: {admin[2]}")
            print(f"  Is Admin: {admin[4]}")
            print(f"  Hashed Password (first 30 chars): {admin[3][:30] if admin[3] else 'None'}...")
            
            # Test the hash
            password = "admin123"
            try:
                matches = bcrypt.checkpw(password.encode('utf-8'), admin[3].encode('utf-8'))
                print(f"  Password 'admin123' matches: {matches}")
            except Exception as e:
                print(f"  Error checking password: {e}")
                
                # Try to update with correct hash
                print("\n  Attempting to fix admin password hash...")
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                cur.execute(
                    'UPDATE users SET hashed_password = %s WHERE username = %s',
                    (hashed, "admin")
                )
                conn.commit()
                print("  ✓ Admin password hash updated!")
        else:
            print("\n✗ Admin user NOT found in production database!")
            print("  Creating admin user now...")
            
            password = "admin123"
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            cur.execute("""
                INSERT INTO users (username, email, full_name, hashed_password, role, is_admin, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ("admin", "admin@arrivapp.com", "Administrator", hashed_pw, "admin", True, True))
            conn.commit()
            print("  ✓ Admin user created!")
        
        # List all users
        print("\nAll users in production:")
        cur.execute("SELECT id, username, email, is_admin FROM users ORDER BY id")
        for row in cur.fetchall():
            print(f"  ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Admin: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_admin()
