from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Adjust these imports to match your project structure
from app.models import User  # Change if your User model is elsewhere
from app.core.security import get_password_hash  # Change if needed

# TODO: Replace with your actual Render database connection string
DATABASE_URL = "PASTE_YOUR_RENDER_DB_CONNECTION_STRING_HERE"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# TODO: Set your new admin password here
new_password = "PASTE_YOUR_NEW_PASSWORD_HERE"
hashed_password = get_password_hash(new_password)

admin_user = session.query(User).filter(User.username == "admin").first()
if admin_user:
    admin_user.hashed_password = hashed_password
    session.commit()
    print("Admin password updated successfully.")
else:
    print("Admin user not found.")

session.close()
