"""
Database Schema for CDMS (Document Management System)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import hashlib

Base = declarative_base()


class Document(Base):
    """PDF Document metadata"""
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)  # Hash of filepath
    filename = Column(String, unique=True)
    filepath = Column(String)
    file_size = Column(Integer)  # Size in bytes
    num_pages = Column(Integer)
    num_chunks = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_processed = Column(DateTime)
    processed = Column(Integer, default=0)  # 0=No, 1=Yes
    doc_metadata = Column(JSON)  # Additional metadata (renamed from 'metadata' - SQLAlchemy reserved)
    
    @staticmethod
    def generate_id(filepath: str) -> str:
        """Generate document ID from filepath"""
        return hashlib.md5(filepath.encode()).hexdigest()


class DocumentChunk(Base):
    """Text chunks from documents"""
    __tablename__ = 'document_chunks'
    
    id = Column(String, primary_key=True)  # unique chunk id
    document_id = Column(String)  # FK to documents.id
    chunk_index = Column(Integer)  # Order in document
    content = Column(Text)  # The actual text content
    page_number = Column(Integer)  # Which page this chunk is from
    char_count = Column(Integer)
    token_count = Column(Integer)  # Estimated tokens
    chunk_metadata = Column(JSON)  # Additional metadata (renamed from 'metadata' - SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_id(document_id: str, chunk_index: int) -> str:
        """Generate chunk ID"""
        return f"{document_id}_{chunk_index}"


class DatabaseManager:
    """Manages the CDMS database"""
    
    def __init__(self, db_path: str = "data/cdms_metadata.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        # SQLite concurrency fixes:
        #   - timeout=30: wait up to 30s for locks instead of default 5s
        #   - check_same_thread=False: allow cross-thread access (safe with scoped sessions)
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"timeout": 30, "check_same_thread": False},
            pool_pre_ping=True,
        )
        
        # Enable WAL mode for better concurrent read/write performance
        from sqlalchemy import event
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session"""
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=self.engine)
        return Session()


# Test function
if __name__ == "__main__":
    print("Testing CDMS Database Schema...")
    print("-" * 70)
    
    # Create database
    db = DatabaseManager()
    
    print("✅ Database initialized")
    print(f"   Location: {db.db_path}")
    print(f"   Tables created: documents, document_chunks")
    
    # Test ID generation
    doc_id = Document.generate_id("/path/to/test.pdf")
    chunk_id = DocumentChunk.generate_id(doc_id, 0)
    
    print(f"\n✅ ID generation works:")
    print(f"   Document ID: {doc_id[:16]}...")
    print(f"   Chunk ID: {chunk_id}")

