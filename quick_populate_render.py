#!/usr/bin/env python3
"""
Emergency: Run populate directly using psql on Render's PostgreSQL
Usage:
  1. Get DATABASE_URL from Render secrets
  2. Set as environment variable
  3. Run this script

Example:
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
  python quick_populate_render.py
"""
import os
import subprocess
import sys

# The populate_render_db.py script we already created
POPULATE_SCRIPT = "backend/populate_render_db.py"

def main():
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not set!")
        print("\nTo use this script:")
        print("1. Get DATABASE_URL from Render (secrets)")
        print("2. Set it: export DATABASE_URL='postgresql://...'")
        print("3. Run this script: python quick_populate_render.py")
        print("\nAlternative: Use GitHub Actions")
        print("  https://github.com/arrivapppilot-dotcom/ArrivApp/actions")
        print("  Find 'Populate Render DB Now' workflow and click 'Run workflow'")
        sys.exit(1)
    
    print("=" * 70)
    print("🚀 Quick Populate - Render Database")
    print("=" * 70)
    print(f"\n📍 Database: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    print(f"📄 Script: {POPULATE_SCRIPT}\n")
    
    # Run the populate script
    try:
        result = subprocess.run(
            ["python", POPULATE_SCRIPT],
            check=True,
            capture_output=False
        )
        print("\n" + "=" * 70)
        print("✅ Success! Dashboard will update in ~30 seconds")
        print("=" * 70)
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print(f"❌ Failed with exit code {e.returncode}")
        print("=" * 70)
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
