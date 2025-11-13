"""
Check what tables exist in production database
"""
import psycopg2

PROD_DB = "postgresql://arrivapp_user:Kzu0qp96GCgBJ482q5FX54tAP1Jxre0D@dpg-d4aoe7ili9vc73dheug0-a.frankfurt-postgres.render.com/arrivapp"

def check_tables():
    try:
        conn = psycopg2.connect(PROD_DB)
        cur = conn.cursor()
        
        print("Checking tables in production database...\n")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        if tables:
            print("Tables found:")
            for table in tables:
                print(f"  - {table[0]}")
                
                # Get column count for each table
                cur.execute(f"""
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = '{table[0]}'
                """)
                col_count = cur.fetchone()[0]
                print(f"    ({col_count} columns)")
        else:
            print("No tables found - database is empty!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
