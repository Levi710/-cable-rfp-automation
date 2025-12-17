from config.database import SessionLocal

class DatabaseConnection:
    @staticmethod
    def get_session():
        """Get database session."""
        return SessionLocal()
    
    @staticmethod
    def test_connection():
        """Test database connectivity."""
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False