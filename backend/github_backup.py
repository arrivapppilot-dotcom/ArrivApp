#!/usr/bin/env python3
"""
GitHub Release-Based Backup System for ArrivApp

This script creates backups of the database and QR codes, then uploads them
as GitHub Release artifacts for free, reliable cloud storage.

Features:
- Creates compressed database backups (SQLite)
- Backs up QR codes directory
- Uploads to GitHub Releases automatically
- Cleans up old releases to manage storage
- Can be run locally or via GitHub Actions

Usage:
    python3 github_backup.py backup          # Create and upload backup
    python3 github_backup.py list            # List all releases/backups
    python3 github_backup.py cleanup         # Remove old releases (keep latest 5)
    python3 github_backup.py restore TAG     # Download and restore backup

Environment Variables:
    GITHUB_TOKEN: GitHub Personal Access Token with repo scope
    GITHUB_REPO: Repository in format "owner/repo" (e.g., "arrivapppilot-dotcom/ArrivApp")
    DATABASE_PATH: Path to database file (default: ./arrivapp.db)
    QR_CODES_DIR: Path to QR codes directory (default: ./qr_codes)
"""

import os
import sys
import json
import gzip
import shutil
import tarfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import subprocess
import requests


class GitHubBackupManager:
    """Manages backups stored as GitHub Releases."""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO", "arrivapppilot-dotcom/ArrivApp")
        self.database_path = Path(os.getenv("DATABASE_PATH", "arrivapp.db"))
        self.qr_codes_dir = Path(os.getenv("QR_CODES_DIR", "qr_codes"))
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.api_base = f"https://api.github.com/repos/{self.github_repo}"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_tag = f"backup-{self.timestamp}"
        
    def backup_database(self) -> Optional[Path]:
        """Create a compressed database backup."""
        if not self.database_path.exists():
            print(f"⚠️  Database not found at {self.database_path}")
            return None
        
        backup_file = Path(f"arrivapp_db_{self.timestamp}.sqlite.gz")
        
        try:
            print(f"📦 Backing up database to {backup_file}...")
            with open(self.database_path, 'rb') as f_in:
                with gzip.open(backup_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✅ Database backup created: {file_size_mb:.2f} MB")
            return backup_file
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return None
    
    def backup_qr_codes(self) -> Optional[Path]:
        """Create a compressed QR codes backup."""
        if not self.qr_codes_dir.exists():
            print(f"⚠️  QR codes directory not found at {self.qr_codes_dir}")
            return None
        
        backup_file = Path(f"qr_codes_{self.timestamp}.tar.gz")
        
        try:
            print(f"📦 Backing up QR codes to {backup_file}...")
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(self.qr_codes_dir, arcname="qr_codes")
            
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✅ QR codes backup created: {file_size_mb:.2f} MB")
            return backup_file
        except Exception as e:
            print(f"❌ Error backing up QR codes: {e}")
            return None
    
    def create_release(self) -> bool:
        """Create a GitHub Release for this backup."""
        print(f"📝 Creating GitHub Release: {self.backup_tag}...")
        
        data = {
            "tag_name": self.backup_tag,
            "name": f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "body": f"Automated backup created at {datetime.now().isoformat()}\n\nBackup includes:\n- Database snapshot\n- QR codes archive",
            "draft": False,
            "prerelease": True
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/releases",
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 201:
                print(f"❌ Failed to create release: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            print(f"✅ Release created: {self.backup_tag}")
            return True
        except Exception as e:
            print(f"❌ Error creating release: {e}")
            return False
    
    def upload_asset(self, file_path: Path) -> bool:
        """Upload a file as an asset to the release."""
        print(f"📤 Uploading {file_path.name}...")
        
        # Get upload URL from release
        try:
            response = requests.get(
                f"{self.api_base}/releases/tags/{self.backup_tag}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get release: {response.status_code}")
                return False
            
            upload_url = response.json()["upload_url"]
            # Remove the {?name,label} template parameter
            upload_url = upload_url.split("{")[0]
            
        except Exception as e:
            print(f"❌ Error getting release: {e}")
            return False
        
        # Upload file
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f)}
                headers = {"Authorization": f"token {self.github_token}"}
                response = requests.post(
                    f"{upload_url}?name={file_path.name}",
                    headers=headers,
                    files=files,
                    timeout=120
                )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to upload asset: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ Uploaded {file_path.name} ({file_size_mb:.2f} MB)")
            return True
        except Exception as e:
            print(f"❌ Error uploading asset: {e}")
            return False
    
    def perform_backup(self) -> bool:
        """Perform full backup: database + QR codes."""
        print("\n" + "="*60)
        print("🔄 ArrivApp GitHub Backup Starting")
        print("="*60)
        
        # Create backups
        db_backup = self.backup_database()
        qr_backup = self.backup_qr_codes()
        
        if not db_backup and not qr_backup:
            print("❌ No backups created!")
            return False
        
        # Create release
        if not self.create_release():
            print("❌ Failed to create release")
            return False
        
        # Upload files
        all_uploaded = True
        if db_backup:
            if not self.upload_asset(db_backup):
                all_uploaded = False
            db_backup.unlink()  # Clean up local file
        
        if qr_backup:
            if not self.upload_asset(qr_backup):
                all_uploaded = False
            qr_backup.unlink()  # Clean up local file
        
        if all_uploaded:
            print("\n" + "="*60)
            print("✅ Backup completed successfully!")
            print(f"📌 Release tag: {self.backup_tag}")
            print("="*60 + "\n")
            return True
        else:
            print("\n❌ Some files failed to upload\n")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all backup releases."""
        print("\n📋 Available Backups:\n")
        
        try:
            response = requests.get(
                f"{self.api_base}/releases",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to list releases: {response.status_code}")
                return []
            
            releases = response.json()
            backups = [r for r in releases if r["tag_name"].startswith("backup-")]
            
            if not backups:
                print("No backups found")
                return []
            
            for backup in backups[:10]:  # Show last 10
                created = backup["created_at"]
                assets_count = len(backup["assets"])
                asset_size_mb = sum(a["size"] for a in backup["assets"]) / (1024 * 1024)
                
                print(f"📌 {backup['tag_name']}")
                print(f"   Created: {created}")
                print(f"   Files: {assets_count}, Total Size: {asset_size_mb:.2f} MB")
                for asset in backup["assets"]:
                    print(f"   - {asset['name']} ({asset['size']/(1024*1024):.2f} MB)")
                print()
            
            return backups
        except Exception as e:
            print(f"❌ Error listing releases: {e}")
            return []
    
    def cleanup_old_backups(self, keep_count: int = 5) -> bool:
        """Delete old backups, keeping only the latest N."""
        print(f"\n🧹 Cleaning up old backups (keeping latest {keep_count})...\n")
        
        try:
            response = requests.get(
                f"{self.api_base}/releases",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to list releases: {response.status_code}")
                return False
            
            releases = response.json()
            backups = [r for r in releases if r["tag_name"].startswith("backup-")]
            
            # Sort by created date, newest first
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Delete old ones
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    del_response = requests.delete(
                        f"{self.api_base}/releases/{backup['id']}",
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if del_response.status_code == 204:
                        size_mb = sum(a["size"] for a in backup["assets"]) / (1024 * 1024)
                        print(f"🗑️  Deleted {backup['tag_name']} ({size_mb:.2f} MB)")
                        deleted_count += 1
                except Exception as e:
                    print(f"❌ Error deleting {backup['tag_name']}: {e}")
            
            print(f"\n✅ Deleted {deleted_count} old backups")
            return True
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False
    
    def restore_backup(self, tag: str) -> bool:
        """Download and restore a backup."""
        print(f"\n📥 Restoring backup: {tag}\n")
        
        try:
            # Get release
            response = requests.get(
                f"{self.api_base}/releases/tags/{tag}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Backup not found: {tag}")
                return False
            
            release = response.json()
            assets = release["assets"]
            
            if not assets:
                print("❌ No files in this backup")
                return False
            
            print(f"Found {len(assets)} files to restore:")
            for asset in assets:
                print(f"  - {asset['name']} ({asset['size']/(1024*1024):.2f} MB)")
            
            # Download files
            for asset in assets:
                print(f"\n📥 Downloading {asset['name']}...")
                
                response = requests.get(
                    asset["browser_download_url"],
                    timeout=120,
                    stream=True
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to download: {response.status_code}")
                    continue
                
                with open(asset["name"], 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Downloaded: {asset['name']}")
            
            print("\n✅ Restore files downloaded. Next steps:")
            print("   1. Extract: tar -xzf qr_codes_*.tar.gz")
            print("   2. Restore DB: gunzip -c arrivapp_db_*.sqlite.gz > arrivapp.db")
            
            return True
        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    try:
        manager = GitHubBackupManager()
        command = sys.argv[1].lower()
        
        if command == "backup":
            success = manager.perform_backup()
            sys.exit(0 if success else 1)
        
        elif command == "list":
            manager.list_backups()
        
        elif command == "cleanup":
            success = manager.cleanup_old_backups(keep_count=5)
            sys.exit(0 if success else 1)
        
        elif command == "restore":
            if len(sys.argv) < 3:
                print("Usage: python3 github_backup.py restore <tag>")
                print("Example: python3 github_backup.py restore backup-20251113_120000")
                sys.exit(1)
            tag = sys.argv[2]
            success = manager.restore_backup(tag)
            sys.exit(0 if success else 1)
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nRequired environment variables:")
        print("  GITHUB_TOKEN - GitHub Personal Access Token (with 'repo' scope)")
        print("  GITHUB_REPO - Repository (e.g., 'owner/repo')")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
