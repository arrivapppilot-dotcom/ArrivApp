"""
Simple migration script - copies data from local SQLite to production PostgreSQL
Run: python3 simple_migrate.py
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import sys

# Production database URL
PROD_DB = "postgresql://arrivapp_user:Kzu0qp96GCgBJ482q5FX54tAP1Jxre0D@dpg-d4aoe7ili9vc73dheug0-a.frankfurt-postgres.render.com/arrivapp"

def migrate():
    print("=" * 70)
    print("MIGRATING DATA FROM LOCAL SQLITE TO PRODUCTION POSTGRESQL")
    print("=" * 70)
    
    # Connect to local SQLite
    local_conn = sqlite3.connect('arrivapp.db')
    local_conn.row_factory = sqlite3.Row
    local_cur = local_conn.cursor()
    
    # Connect to production PostgreSQL
    prod_conn = psycopg2.connect(PROD_DB)
    prod_cur = prod_conn.cursor()
    
    try:
        # Check local data
        local_cur.execute("SELECT COUNT(*) FROM schools")
        local_schools = local_cur.fetchone()[0]
        local_cur.execute("SELECT COUNT(*) FROM students")
        local_students = local_cur.fetchone()[0]
        local_cur.execute("SELECT COUNT(*) FROM users")
        local_users = local_cur.fetchone()[0]
        
        print(f"\nLocal database:")
        print(f"  Schools: {local_schools}")
        print(f"  Students: {local_students}")
        print(f"  Users: {local_users}")
        
        # Check production data
        prod_cur.execute("SELECT COUNT(*) FROM schools")
        prod_schools = prod_cur.fetchone()[0]
        prod_cur.execute("SELECT COUNT(*) FROM students")
        prod_students = prod_cur.fetchone()[0]
        prod_cur.execute("SELECT COUNT(*) FROM users")
        prod_users = prod_cur.fetchone()[0]
        
        print(f"\nProduction database:")
        print(f"  Schools: {prod_schools}")
        print(f"  Students: {prod_students}")
        print(f"  Users: {prod_users}")
        
        print("\n" + "=" * 70)
        print("Starting migration...")
        print("=" * 70)
        
        # Migrate Schools
        print("\n1. Migrating Schools...")
        local_cur.execute("SELECT * FROM schools")
        schools = local_cur.fetchall()
        
        school_id_map = {}
        for school in schools:
            # Check if exists
            prod_cur.execute("SELECT id FROM schools WHERE name = %s", (school['name'],))
            existing = prod_cur.fetchone()
            
            if existing:
                school_id_map[school['id']] = existing[0]
                print(f"  ⚠️  '{school['name']}' exists, skipping...")
                continue
            
            prod_cur.execute("""
                INSERT INTO schools (name, address, contact_email, contact_phone, timezone, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (school['name'], school['address'], school['contact_email'], 
                  school['contact_phone'], school['timezone'], bool(school['is_active']), school['created_at']))
            
            new_id = prod_cur.fetchone()[0]
            school_id_map[school['id']] = new_id
            print(f"  ✓ {school['name']} (ID: {school['id']} → {new_id})")
        
        prod_conn.commit()
        
        # Migrate Users (skip admin)
        print("\n2. Migrating Users...")
        local_cur.execute("SELECT * FROM users WHERE username != 'admin'")
        users = local_cur.fetchall()
        
        for user in users:
            # Check if exists
            prod_cur.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
            if prod_cur.fetchone():
                print(f"  ⚠️  '{user['username']}' exists, skipping...")
                continue
            
            school_id = school_id_map.get(user['school_id']) if user['school_id'] else None
            
            prod_cur.execute("""
                INSERT INTO users (username, email, hashed_password, full_name, role, 
                                   school_id, is_active, is_admin, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user['username'], user['email'], user['hashed_password'], user['full_name'],
                  user['role'], school_id, bool(user['is_active']), bool(user['is_admin']), user['created_at']))
            
            print(f"  ✓ {user['username']} ({user['role']})")
        
        prod_conn.commit()
        
        # Migrate Students
        print("\n3. Migrating Students...")
        local_cur.execute("SELECT * FROM students")
        students = local_cur.fetchall()
        
        batch = []
        for i, student in enumerate(students, 1):
            school_id = school_id_map.get(student['school_id'])
            
            batch.append((
                student['student_id'], student['name'], student['class_name'],
                student['parent_email'], school_id, student['qr_code_path'],
                bool(student['is_active']), student['created_at']
            ))
            
            # Insert in batches of 100
            if len(batch) >= 100 or i == len(students):
                execute_values(prod_cur, """
                    INSERT INTO students (student_id, name, class_name, parent_email, 
                                         school_id, qr_code_path, is_active, created_at)
                    VALUES %s
                    ON CONFLICT (student_id) DO NOTHING
                """, batch)
                prod_conn.commit()
                print(f"  → Migrated {i}/{len(students)} students...")
                batch = []
        
        print(f"  ✓ Students migration complete!")
        
        # Final counts
        prod_cur.execute("SELECT COUNT(*) FROM schools")
        final_schools = prod_cur.fetchone()[0]
        prod_cur.execute("SELECT COUNT(*) FROM students")
        final_students = prod_cur.fetchone()[0]
        prod_cur.execute("SELECT COUNT(*) FROM users")
        final_users = prod_cur.fetchone()[0]
        
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE!")
        print("=" * 70)
        print(f"Production database now has:")
        print(f"  Schools: {final_schools}")
        print(f"  Students: {final_students}")
        print(f"  Users: {final_users}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        prod_conn.rollback()
        sys.exit(1)
    finally:
        local_conn.close()
        prod_conn.close()

if __name__ == "__main__":
    migrate()
