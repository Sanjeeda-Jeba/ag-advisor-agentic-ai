#!/usr/bin/env python3
"""
Fix Corrupted SQLite Database
Attempts to recover data, then recreates database if needed
"""

import sys
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_database_integrity(db_path: str) -> bool:
    """Check if database is valid"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Try to read from database
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == "ok":
            return True
        return False
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
        return False

def recover_database(db_path: str) -> bool:
    """Attempt to recover data from corrupted database"""
    print("   🔄 Attempting to recover data...")
    
    try:
        # Try to dump data using .dump command
        backup_path = db_path.replace(".db", "_recovered.db")
        
        # Use sqlite3 command line tool to recover
        import subprocess
        result = subprocess.run(
            ["sqlite3", db_path, ".dump"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            # Write recovered data to new file
            with open(backup_path, 'w') as f:
                f.write(result.stdout)
            print(f"   ✅ Recovered data saved to: {backup_path}")
            return True
        else:
            print(f"   ⚠️  Recovery attempt failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ⚠️  Recovery failed: {e}")
        return False

def backup_corrupted_database(db_path: str) -> str:
    """Backup corrupted database before deletion"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.corrupted_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"   ✅ Corrupted database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"   ⚠️  Backup failed: {e}")
        return None

def recreate_database(db_path: str):
    """Recreate database with fresh schema"""
    print("   🔄 Recreating database...")
    
    try:
        # Remove corrupted database
        if Path(db_path).exists():
            Path(db_path).unlink()
        
        # Recreate using DatabaseManager
        from src.cdms.schema import DatabaseManager
        
        db_manager = DatabaseManager(db_path=db_path)
        print(f"   ✅ Database recreated at: {db_path}")
        print(f"   ✅ Tables created: documents, document_chunks")
        
        return True
    except Exception as e:
        print(f"   ❌ Failed to recreate database: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main fix routine"""
    print("=" * 80)
    print("SQLite Database Corruption Fix")
    print("=" * 80)
    
    db_path = "data/cdms_metadata.db"
    db_file = Path(db_path)
    
    # Check if database exists
    if not db_file.exists():
        print(f"\n📄 Database file not found: {db_path}")
        print("   Creating new database...")
        recreate_database(db_path)
        print("\n✅ Done! New database created.")
        return
    
    print(f"\n📄 Database file: {db_path}")
    print(f"   Size: {db_file.stat().st_size:,} bytes")
    
    # Step 1: Check integrity
    print("\n🔍 Step 1: Checking database integrity...")
    is_valid = check_database_integrity(db_path)
    
    if is_valid:
        print("   ✅ Database is valid! No corruption detected.")
        print("\n💡 If you're still getting errors, try restarting the application.")
        return
    
    print("   ❌ Database is corrupted!")
    
    # Step 2: Attempt recovery
    print("\n🔧 Step 2: Attempting data recovery...")
    recovery_success = recover_database(db_path)
    
    if recovery_success:
        print("   ✅ Some data may have been recovered.")
        print("   💡 Check the recovered database file if you need to restore data.")
    
    # Step 3: Backup corrupted database
    print("\n💾 Step 3: Backing up corrupted database...")
    backup_path = backup_corrupted_database(db_path)
    
    if not backup_path:
        response = input("\n⚠️  Backup failed. Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            print("   ❌ Aborted. Database not modified.")
            return
    
    # Step 4: Recreate database
    print("\n🔄 Step 4: Recreating database...")
    success = recreate_database(db_path)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ Database fixed successfully!")
        print("=" * 80)
        print("\n📝 Next steps:")
        print("   1. Your PDFs are still in data/pdfs/")
        print("   2. You'll need to re-index them:")
        print("      python src/cdms/document_loader.py")
        print("   3. The corrupted database is backed up (if backup succeeded)")
        if backup_path:
            print(f"      Backup location: {backup_path}")
    else:
        print("\n❌ Failed to fix database. Please check the error messages above.")

if __name__ == "__main__":
    main()
