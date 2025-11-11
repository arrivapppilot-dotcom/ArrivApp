"""
Migration script to add justifications table
Run this script to update the database with the justifications feature
"""
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create justifications table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS justifications (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id),
                justification_type VARCHAR NOT NULL,
                date TIMESTAMP NOT NULL,
                reason TEXT NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'pending',
                submitted_by VARCHAR NOT NULL,
                submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id),
                reviewed_at TIMESTAMP,
                notes TEXT
            );
        """))
        
        # Create indexes for better performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_justifications_student_id 
            ON justifications(student_id);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_justifications_date 
            ON justifications(date);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_justifications_status 
            ON justifications(status);
        """))
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Created justifications table")
        print("   - Added indexes for performance")

if __name__ == "__main__":
    migrate()
