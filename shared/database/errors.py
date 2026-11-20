"""
Database Error Definitions for My K-Drama 2.0
"""

class DatabaseError(Exception):
    """Base exception for all database operations"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DuplicateKeyError(DatabaseError):
    """Raised when a unique constraint or duplicate key violation occurs"""
    pass

class DocumentNotFoundError(DatabaseError):
    """Raised when an expected document is not found"""
    pass

class ValidationError(DatabaseError):
    """Raised when document data fails schema validation"""
    pass

class ConnectionError(DatabaseError):
    """Raised when database connection fails or times out"""
    pass
