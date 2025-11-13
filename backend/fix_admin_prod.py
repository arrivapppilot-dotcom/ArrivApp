"""
Fix admin user in production database
"""
import psycopg2
import bcrypt

PROD_DB = "postgresql://arrivapp_user:Kzu0qp96GCgBJ482q5FX54tAP1Jxre0D@dpg-d4aoe7ili9vc73dheug0-a.frankfurt-postgres.render.com/arrivapp"

def fix_admin():
    try:
        conn = psycopg2.connect(PROD_DB)
        cur = conn.cursor()
        
        print("Fixing admin user in production...\n")
        
        # Create correct password hash
        password = "admin123"
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        print(f"New hash for 'admin123': {hashed_pw[:30]}...")
        
        # Update admin to have correct password and is_admin=True
        cur.execute("""
            UPDATE users 
            SET hashed_password = %s, is_admin = true, role = 'admin'
            WHERE username = 'admin'
        """, (hashed_pw,))
        
        conn.commit()
        rows_updated = cur.rowcount
        print(f"✓ Updated {rows_updated} row(s)\n")
        
        # Verify the fix
        cur.execute("SELECT id, username, email, hashed_password, is_admin, role FROM users WHERE username = 'admin'")
        admin = cur.fetchone()
        if admin:
            print("Updated admin user:")
            print(f"  ID: {admin[0]}")
            print(f"  Username: {admin[1]}")
            print(f"  Email: {admin[2]}")
            print(f"  Is Admin: {admin[4]}")
            print(f"  Role: {admin[5]}")
            
            # Verify password
            matches = bcrypt.checkpw(password.encode('utf-8'), admin[3].encode('utf-8'))
            print(f"  Password 'admin123' matches: {matches}")
        
        conn.close()
        print("\n✓ Admin user fixed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_admin()
