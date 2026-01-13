"""
Database Interface
Handles SQL execution and schema management
"""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd


class DatabaseManager:
    """Manages database connections and query execution"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent.parent / "schema.json"
        self._schema_metadata = None
    
    def get_schema_metadata(self) -> Dict[str, Any]:
        """Load schema metadata from JSON file"""
        if self._schema_metadata is None:
            with open(self.schema_path, 'r') as f:
                self._schema_metadata = json.load(f)
        return self._schema_metadata
    
    def get_schema_description(self) -> str:
        """Generate a natural language description of the database schema"""
        schema = self.get_schema_metadata()
        
        description = f"Database: {schema['description']}\n\n"
        description += "Tables:\n"
        
        for table in schema['tables']:
            description += f"\n{table['name']}: {table['description']}\n"
            description += "  Columns:\n"
            for col in table['columns']:
                description += f"    - {col['name']} ({col['type']}): {col['description']}\n"
        
        description += "\nRelationships:\n"
        for rel in schema['relationships']:
            description += f"  - {rel['description']} ({rel['from']} → {rel['to']})\n"
        
        description += "\nBusiness Rules:\n"
        for rule in schema['business_rules']:
            description += f"  - {rule}\n"
        
        return description
    
    def execute_query(self, sql: str) -> Tuple[bool, Any, str]:
        """
        Execute SQL query
        Returns: (success, result, error_message)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Execute query
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            return True, df, ""
            
        except Exception as e:
            return False, None, str(e)
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> Optional[pd.DataFrame]:
        """Get sample rows from a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
            conn.close()
            return df
        except:
            return None
    
    def validate_connection(self) -> bool:
        """Check if database connection is valid"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False
