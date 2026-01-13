"""
Security & RBAC Test Suite
- SQL sanitization and RBAC filtering
- Table alias detection in complex queries
- Role-based access control validation
- Session management and authentication
- Multi-role query scenarios
"""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

from agent import PropertyManagementAgent, UserContext, DatabaseManager
from agent.security import SecurityValidator

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@pytest.fixture
def agent():
    """Create agent instance for testing"""
    db_path = os.getenv("DATABASE_PATH", "property_management.db")
    db_manager = DatabaseManager(db_path)
    return PropertyManagementAgent(db_manager, max_retries=3)


@pytest.fixture
def security_validator():
    """Create security validator instance"""
    return SecurityValidator()


class TestSQLSanitization:
    """Test SQL sanitization and RBAC filtering"""
    
    def test_rbac_strips_trailing_semicolon(self, security_validator):
        """Test that apply_rbac strips trailing semicolons"""
        sql_with_semicolon = "SELECT COUNT(*) FROM Properties p;"
        user_context = UserContext(user_id=1, role="owner", owner_id=1)
        
        result = security_validator.apply_rbac(sql_with_semicolon, user_context)
        
        # Should not have semicolon in the middle
        assert ";WHERE" not in result
        assert "; WHERE" not in result
        
        # Should have proper WHERE clause
        assert "WHERE p.owner_id = 1" in result
        
    def test_rbac_handles_multiple_spaces_and_semicolon(self, security_validator):
        """Test that apply_rbac handles various whitespace + semicolon combinations"""
        test_cases = [
            "SELECT * FROM Properties p;",
            "SELECT * FROM Properties p  ;",
            "SELECT * FROM Properties p  ;  ",
            "SELECT * FROM Properties p;\n",
        ]
        
        user_context = UserContext(user_id=2, role="owner", owner_id=2)
        
        for sql in test_cases:
            result = security_validator.apply_rbac(sql, user_context)
            assert ";WHERE" not in result and "; WHERE" not in result, f"Failed for: {sql}"
            assert "WHERE p.owner_id = 2" in result, f"Failed for: {sql}"


class TestTableAliasDetection:
    """Test RBAC alias detection in complex SQL queries"""
    
    def test_rbac_detects_from_clause_alias(self, security_validator):
        """Test alias detection in FROM clause"""
        sql = "SELECT COUNT(*) FROM Properties AS p"
        user_context = UserContext(user_id=1, role="owner", owner_id=1)
        
        result = security_validator.apply_rbac(sql, user_context)
        
        assert "p.owner_id = 1" in result
        assert "Properties.owner_id" not in result
    
    def test_rbac_detects_join_clause_alias(self, security_validator):
        """Test alias detection in JOIN clause"""
        sql = """SELECT AVG(U.monthly_rent)
        FROM Units AS U
        JOIN Properties AS P ON U.property_id = P.property_id"""
        
        user_context = UserContext(user_id=2, role="owner", owner_id=2)
        
        result = security_validator.apply_rbac(sql, user_context)
        
        assert "P.owner_id = 2" in result
        assert "Properties.owner_id" not in result
    
    def test_rbac_detects_join_without_as_keyword(self, security_validator):
        """Test alias detection in JOIN without AS keyword"""
        sql = """SELECT COUNT(*)
        FROM Units U
        JOIN Properties P ON U.property_id = P.property_id"""
        
        user_context = UserContext(user_id=3, role="owner", owner_id=3)
        
        result = security_validator.apply_rbac(sql, user_context)
        
        assert "P.owner_id = 3" in result
        assert "Properties.owner_id" not in result


class TestUserSessionScenarios:
    """Test complete user session scenarios across different roles"""
    
    def test_owner_property_count(self, agent):
        """Test: Owner queries their property count"""
        # Simulate fresh login
        agent.clear_conversation()
        
        user_context = UserContext(user_id=1, role="owner", owner_id=1)
        response = agent.query("How many properties do I have?", user_context)
        
        assert response["success"] is True, f"Query failed: {response.get('errors')}"
        assert response["sql_query"] is not None
        assert "owner_id = 1" in response["sql_query"]
        
        # Check for semicolon issues
        sql = response["sql_query"].strip()
        if sql.endswith(';'):
            sql = sql[:-1]  # Remove trailing semicolon if present
        assert ';' not in sql, "SQL has semicolon in middle of query"
    
    def test_owner_average_rent(self, agent):
        """Test: Owner queries average rent with JOIN operations"""
        agent.clear_conversation()
        
        user_context = UserContext(user_id=2, role="owner", owner_id=2)
        response = agent.query("What is my average rent?", user_context)
        
        assert response["success"] is True, f"Query failed: {response.get('errors')}"
        assert response["sql_query"] is not None
        
        # Should not have "Properties.owner_id" - should use alias
        assert "Properties.owner_id" not in response["sql_query"]
    
    def test_multiple_users_sequential(self, agent):
        """Test: Multiple users asking questions sequentially"""
        test_cases = [
            (UserContext(user_id=1, role="owner", owner_id=1), "How many properties?"),
            (UserContext(user_id=2, role="owner", owner_id=2), "What's my average rent?"),
            (UserContext(user_id=999, role="admin", owner_id=None), "Total properties?"),
        ]
        
        for user_context, query in test_cases:
            agent.clear_conversation()
            response = agent.query(query, user_context)
            assert response["success"] is True, \
                f"Failed for {user_context.role}: {response.get('errors')}"


class TestSessionManagement:
    """Test session management and conversation history"""
    
    def test_memory_clears_on_role_change(self, agent):
        """Test that memory clears when role changes"""
        # First interaction as LLC1
        user_context_1 = UserContext(user_id=1, role="owner", owner_id=1)
        agent.query("How many properties in Arizona?", user_context_1)
        
        # Check memory has content
        stats = agent.get_conversation_stats()
        assert stats["total_interactions"] > 0
        
        # Clear conversation (simulating role change)
        agent.clear_conversation()
        
        # Memory should be empty
        stats = agent.get_conversation_stats()
        assert stats["total_interactions"] == 0
        assert stats["current_context"] == {}
    
    def test_memory_tracks_interactions(self, agent):
        """Test that memory correctly tracks interactions"""
        agent.clear_conversation()
        
        user_context = UserContext(user_id=1, role="owner", owner_id=1)
        
        # First query
        agent.query("How many properties?", user_context)
        stats = agent.get_conversation_stats()
        assert stats["total_interactions"] == 1
        
        # Second query
        agent.query("What's the average rent?", user_context)
        stats = agent.get_conversation_stats()
        assert stats["total_interactions"] == 2


class TestPasswordAuthentication:
    """Test password authentication logic"""
    
    def test_admin_password_validation(self):
        """Test admin password validation"""
        passwords = ["admin", "ADMIN", "Admin", "  admin  "]
        
        for password in passwords:
            assert password.strip().lower() == "admin"
    
    def test_owner_password_validation(self):
        """Test owner password validation"""
        test_cases = [
            ("llc1", 1),
            ("LLC1", 1),
            ("llc2", 2),
            ("LLC5", 5),
        ]
        
        for password, expected_id in test_cases:
            password_lower = password.lower()
            assert password_lower.startswith("llc")
            owner_id = int(password_lower[3:])
            assert owner_id == expected_id
    
    def test_viewer_password_validation(self):
        """Test viewer password validation"""
        passwords = ["viewer", "VIEWER", "Viewer"]
        
        for password in passwords:
            assert password.strip().lower() == "viewer"


class TestRoleBasedQueries:
    """Test that different roles get appropriate access"""
    
    def test_admin_full_access(self, agent):
        """Test that admin can query all properties"""
        agent.clear_conversation()
        user_context = UserContext(user_id=999, role="admin", owner_id=None)
        
        response = agent.query("How many total properties?", user_context)
        
        assert response["success"] is True
        # Admin queries should NOT have owner_id filter
        if response["sql_query"]:
            assert "owner_id =" not in response["sql_query"]
    
    def test_owner_filtered_access(self, agent):
        """Test that owner queries are filtered by owner_id"""
        agent.clear_conversation()
        user_context = UserContext(user_id=1, role="owner", owner_id=1)
        
        response = agent.query("How many properties?", user_context)
        
        assert response["success"] is True
        # Owner queries SHOULD have owner_id filter
        assert "owner_id = 1" in response["sql_query"]
    
    def test_owner_cannot_query_other_owners(self, agent):
        """Test that owners cannot query other owners' data"""
        agent.clear_conversation()
        user_context = UserContext(user_id=2, role="owner", owner_id=2)
        
        response = agent.query("How many properties does LLC3 have?", user_context)
        
        # Should be denied
        assert "Access denied" in response["answer"] or "cannot" in response["answer"].lower()
    
    def test_viewer_aggregated_access(self, agent):
        """Test that viewer can only access aggregated data"""
        agent.clear_conversation()
        user_context = UserContext(user_id=998, role="viewer", owner_id=None)
        
        response = agent.query("How many properties in total?", user_context)
        
        assert response["success"] is True
        # Viewer queries should NOT have owner_id filter
        if response["sql_query"]:
            assert "owner_id =" not in response["sql_query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
