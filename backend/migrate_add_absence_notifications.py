#!/usr/bin/env python3
"""
Migration: Add AbsenceNotification table to track absence notification emails
This script creates the absence_notifications table if it doesn't exist.
"""

from sqlalchemy import create_engine, Column, Integer, DateTime, Boolean, ForeignKey, String, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# For local SQLite, convert the URL format if needed
if DATABASE_URL.startswith("sqlite"):
    # Local SQLite
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL
    engine = create_engine(DATABASE_URL)

from app.models.models import Base, AbsenceNotification

def create_table():
    """Create the AbsenceNotification table"""
    inspector = inspect(engine)
    
    if "absence_notifications" in inspector.get_table_names():
        print("✓ absence_notifications table already exists")
        return
    
    print("Creating absence_notifications table...")
    Base.metadata.create_all(engine, tables=[AbsenceNotification.__table__])
    print("✓ absence_notifications table created successfully")

if __name__ == "__main__":
    print("\n🔄 Starting migration: Add AbsenceNotification table...")
    create_table()
    print("\n✓ Migration completed!\n")
