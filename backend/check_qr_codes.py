"""
Check QR code status in production database
"""
import psycopg2

PROD_DB = "postgresql://arrivapp_user:Kzu0qp96GCgBJ482q5FX54tAP1Jxre0D@dpg-d4aoe7ili9vc73dheug0-a.frankfurt-postgres.render.com/arrivapp"

def check_qr_codes():
    try:
        conn = psycopg2.connect(PROD_DB)
        cur = conn.cursor()
        
        print("Checking QR code status in production database...\n")
        
        # Check students with QR codes
        cur.execute("SELECT COUNT(*) as total FROM students")
        total = cur.fetchone()[0]
        print(f"Total students: {total}")
        
        # Check how many have QR codes
        cur.execute("SELECT COUNT(*) as with_qr FROM students WHERE qr_code_path IS NOT NULL")
        with_qr = cur.fetchone()[0]
        print(f"Students with QR code path: {with_qr}")
        
        # Check some examples
        cur.execute("SELECT id, name, qr_code_path FROM students WHERE qr_code_path IS NOT NULL LIMIT 5")
        students_with_qr = cur.fetchall()
        
        if students_with_qr:
            print(f"\nExample QR code paths:")
            for student in students_with_qr:
                print(f"  ID {student[0]}: {student[1]} → {student[2]}")
        else:
            print("\nNo students have QR code paths!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_qr_codes()
