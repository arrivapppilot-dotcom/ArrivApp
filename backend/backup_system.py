"""
Automated Backup and Disaster Recovery System for ArrivApp
Provides database backups, file backups, and recovery mechanisms
"""
import os
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/arrivapp_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupManager:
    def __init__(self, backup_dir="/var/backups/arrivapp"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for different backup types
        self.db_backup_dir = self.backup_dir / "database"
        self.files_backup_dir = self.backup_dir / "files"
        self.qr_backup_dir = self.backup_dir / "qr_codes"
        
        for directory in [self.db_backup_dir, self.files_backup_dir, self.qr_backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Detect database type from DATABASE_URL
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./arrivapp.db")
        self.db_type = self._detect_db_type()
        
        # Get database credentials from environment or config (PostgreSQL)
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "arrivapp")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")
        
        # SQLite database path
        self.sqlite_db_path = self._get_sqlite_path()
        
        # Retention policy (days)
        self.daily_retention = 7
        self.weekly_retention = 30
        self.monthly_retention = 365
    
    def _detect_db_type(self):
        """Detect if using SQLite or PostgreSQL"""
        if self.database_url.startswith("sqlite"):
            return "sqlite"
        elif self.database_url.startswith("postgresql"):
            return "postgresql"
        else:
            return "unknown"
    
    def _get_sqlite_path(self):
        """Extract SQLite database file path from DATABASE_URL"""
        if self.db_type == "sqlite":
            # Remove sqlite:/// prefix
            db_path = self.database_url.replace("sqlite:///", "")
            # Handle relative paths
            if not db_path.startswith("/"):
                db_path = Path(__file__).parent / db_path
            return Path(db_path)
        return None
    
    def backup_database(self):
        """Create a database backup (SQLite or PostgreSQL)"""
        if self.db_type == "sqlite":
            return self._backup_sqlite()
        elif self.db_type == "postgresql":
            return self._backup_postgresql()
        else:
            logger.error(f"Unsupported database type: {self.db_type}")
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _backup_sqlite(self):
        """Backup SQLite database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.db_backup_dir / f"arrivapp_db_{timestamp}.sqlite"
        
        try:
            logger.info(f"Starting SQLite database backup: {backup_file}")
            
            if not self.sqlite_db_path or not self.sqlite_db_path.exists():
                raise FileNotFoundError(f"SQLite database not found: {self.sqlite_db_path}")
            
            # Copy SQLite database file
            shutil.copy2(self.sqlite_db_path, backup_file)
            
            # Compress the backup
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, 'rb') as f_in:
                with subprocess.Popen(['gzip'], stdin=subprocess.PIPE, stdout=open(compressed_file, 'wb')) as proc:
                    shutil.copyfileobj(f_in, proc.stdin)
            
            # Remove uncompressed file
            backup_file.unlink()
            
            backup_size = Path(compressed_file).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"SQLite database backup completed: {compressed_file} ({backup_size:.2f} MB)")
            
            # Create backup metadata
            metadata = {
                "timestamp": timestamp,
                "file": str(compressed_file),
                "size_mb": backup_size,
                "type": "database",
                "database_type": "sqlite",
                "source_file": str(self.sqlite_db_path)
            }
            
            metadata_file = self.db_backup_dir / f"arrivapp_db_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            raise
    
    def _backup_postgresql(self):
        """Create a PostgreSQL database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.db_backup_dir / f"arrivapp_db_{timestamp}.sql"
        
        try:
            logger.info(f"Starting PostgreSQL database backup: {backup_file}")
            
            # Set password environment variable for pg_dump
            env = os.environ.copy()
            if self.db_password:
                env['PGPASSWORD'] = self.db_password
            
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-F', 'c',  # Custom format (compressed)
                '-f', str(backup_file)
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Compress the backup
            compressed_file = f"{backup_file}.gz"
            subprocess.run(['gzip', str(backup_file)], check=True)
            
            backup_size = Path(compressed_file).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"PostgreSQL database backup completed: {compressed_file} ({backup_size:.2f} MB)")
            
            # Create backup metadata
            metadata = {
                "timestamp": timestamp,
                "file": str(compressed_file),
                "size_mb": backup_size,
                "type": "database",
                "database_type": "postgresql",
                "database": self.db_name
            }
            
            metadata_file = self.db_backup_dir / f"arrivapp_db_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return compressed_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL backup failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PostgreSQL backup: {e}")
            raise
    
    def backup_qr_codes(self):
        """Backup QR code directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        qr_source = Path(__file__).parent / "qr_codes"
        
        if not qr_source.exists():
            logger.warning("QR codes directory not found, skipping")
            return None
        
        try:
            logger.info("Starting QR codes backup")
            
            # Create tar.gz archive
            backup_file = self.qr_backup_dir / f"qr_codes_{timestamp}.tar.gz"
            
            cmd = [
                'tar', '-czf', str(backup_file),
                '-C', str(qr_source.parent),
                qr_source.name
            ]
            
            subprocess.run(cmd, check=True)
            
            backup_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"QR codes backup completed: {backup_file} ({backup_size:.2f} MB)")
            
            # Create metadata
            file_count = len(list(qr_source.glob("*.png")))
            metadata = {
                "timestamp": timestamp,
                "file": str(backup_file),
                "size_mb": backup_size,
                "type": "qr_codes",
                "file_count": file_count
            }
            
            metadata_file = self.qr_backup_dir / f"qr_codes_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return backup_file
            
        except Exception as e:
            logger.error(f"QR codes backup failed: {e}")
            raise
    
    def backup_configuration(self):
        """Backup application configuration files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            logger.info("Starting configuration backup")
            
            config_files = [
                Path(__file__).parent / "app" / "core" / "config.py",
                Path(__file__).parent / ".env",
                Path(__file__).parent / "requirements.txt",
                Path(__file__).parent / "docker-compose.yml",
            ]
            
            backup_dir = self.files_backup_dir / f"config_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for config_file in config_files:
                if config_file.exists():
                    shutil.copy2(config_file, backup_dir / config_file.name)
            
            # Create tar.gz archive
            backup_file = self.files_backup_dir / f"config_{timestamp}.tar.gz"
            cmd = [
                'tar', '-czf', str(backup_file),
                '-C', str(backup_dir.parent),
                backup_dir.name
            ]
            subprocess.run(cmd, check=True)
            
            # Remove temporary directory
            shutil.rmtree(backup_dir)
            
            backup_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Configuration backup completed: {backup_file} ({backup_size:.2f} MB)")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            raise
    
    def full_backup(self):
        """Perform a complete system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"=== Starting Full Backup: {timestamp} ===")
        
        results = {
            "timestamp": timestamp,
            "backups": {}
        }
        
        try:
            # Database backup
            db_backup = self.backup_database()
            results["backups"]["database"] = str(db_backup)
        except Exception as e:
            results["backups"]["database"] = f"FAILED: {e}"
        
        try:
            # QR codes backup
            qr_backup = self.backup_qr_codes()
            results["backups"]["qr_codes"] = str(qr_backup) if qr_backup else "SKIPPED"
        except Exception as e:
            results["backups"]["qr_codes"] = f"FAILED: {e}"
        
        try:
            # Configuration backup
            config_backup = self.backup_configuration()
            results["backups"]["configuration"] = str(config_backup)
        except Exception as e:
            results["backups"]["configuration"] = f"FAILED: {e}"
        
        # Save backup summary
        summary_file = self.backup_dir / f"backup_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"=== Full Backup Completed: {timestamp} ===")
        return results
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        now = datetime.now()
        logger.info("Starting backup cleanup")
        
        for backup_type_dir in [self.db_backup_dir, self.qr_backup_dir, self.files_backup_dir]:
            for backup_file in backup_type_dir.glob("*"):
                if backup_file.suffix not in ['.gz', '.sql', '.json']:
                    continue
                
                # Get file age
                file_age = now - datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                # Determine if should delete based on retention policy
                should_delete = False
                
                if file_age.days > self.daily_retention:
                    # Keep weekly backups (Sunday)
                    if backup_file.stat().st_mtime % (7 * 86400) != 0:
                        if file_age.days > self.weekly_retention:
                            # Keep monthly backups (1st of month)
                            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if file_date.day != 1 or file_age.days > self.monthly_retention:
                                should_delete = True
                
                if should_delete:
                    logger.info(f"Deleting old backup: {backup_file}")
                    backup_file.unlink()
        
        logger.info("Backup cleanup completed")
    
    def restore_database(self, backup_file):
        """Restore database from backup (SQLite or PostgreSQL)"""
        logger.info(f"Starting database restoration from: {backup_file}")
        
        if self.db_type == "sqlite":
            return self._restore_sqlite(backup_file)
        elif self.db_type == "postgresql":
            return self._restore_postgresql(backup_file)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _restore_sqlite(self, backup_file):
        """Restore SQLite database from backup"""
        try:
            # Decompress if needed
            if backup_file.endswith('.gz'):
                decompressed = backup_file[:-3]
                subprocess.run(['gunzip', '-k', backup_file], check=True)
                backup_file = decompressed
            
            # Backup current database
            if self.sqlite_db_path and self.sqlite_db_path.exists():
                backup_current = f"{self.sqlite_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.sqlite_db_path, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
            
            # Restore from backup
            shutil.copy2(backup_file, self.sqlite_db_path)
            
            logger.info("SQLite database restoration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite restoration failed: {e}")
            raise
    
    def _restore_postgresql(self, backup_file):
        """Restore PostgreSQL database from backup"""
        try:
            # Decompress if needed
            if backup_file.endswith('.gz'):
                decompressed = backup_file[:-3]
                subprocess.run(['gunzip', '-k', backup_file], check=True)
                backup_file = decompressed
            
            # Set password environment variable
            env = os.environ.copy()
            if self.db_password:
                env['PGPASSWORD'] = self.db_password
            
            # Restore using pg_restore
            cmd = [
                'pg_restore',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-c',  # Clean (drop) database objects before recreating
                '--if-exists',  # Don't error if objects don't exist
                backup_file
            ]
            
            subprocess.run(cmd, env=env, check=True)
            
            logger.info("PostgreSQL database restoration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL restoration failed: {e}")
            raise
    
    def list_backups(self):
        """List all available backups"""
        backups = {
            "database": [],
            "qr_codes": [],
            "configuration": []
        }
        
        # Database backups (both .sql.gz and .sqlite.gz)
        for pattern in ["*.sql.gz", "*.sqlite.gz"]:
            for backup in sorted(self.db_backup_dir.glob(pattern), reverse=True):
                backups["database"].append({
                    "file": str(backup),
                    "size_mb": backup.stat().st_size / (1024 * 1024),
                    "date": datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
                })
        
        # QR code backups
        for backup in sorted(self.qr_backup_dir.glob("*.tar.gz"), reverse=True):
            backups["qr_codes"].append({
                "file": str(backup),
                "size_mb": backup.stat().st_size / (1024 * 1024),
                "date": datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
        
        # Configuration backups
        for backup in sorted(self.files_backup_dir.glob("*.tar.gz"), reverse=True):
            backups["configuration"].append({
                "file": str(backup),
                "size_mb": backup.stat().st_size / (1024 * 1024),
                "date": datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
        
        return backups


def main():
    """Main backup execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ArrivApp Backup System')
    parser.add_argument('action', choices=['backup', 'cleanup', 'list', 'restore'],
                       help='Action to perform')
    parser.add_argument('--restore-file', help='Backup file to restore (for restore action)')
    parser.add_argument('--backup-dir', default='/var/backups/arrivapp',
                       help='Backup directory path')
    
    args = parser.parse_args()
    
    manager = BackupManager(backup_dir=args.backup_dir)
    
    if args.action == 'backup':
        results = manager.full_backup()
        print(json.dumps(results, indent=2))
    
    elif args.action == 'cleanup':
        manager.cleanup_old_backups()
    
    elif args.action == 'list':
        backups = manager.list_backups()
        print(json.dumps(backups, indent=2))
    
    elif args.action == 'restore':
        if not args.restore_file:
            print("Error: --restore-file required for restore action")
            return 1
        manager.restore_database(args.restore_file)


if __name__ == "__main__":
    main()
