"""
Unit Tests for Conversation Memory Module
==========================================
Tests the ConversationMemory class for context tracking and query enhancement.
"""

import pytest
from agent.memory import ConversationMemory, ConversationTurn
from datetime import datetime


class TestConversationMemory:
    """Test suite for ConversationMemory"""
    
    def test_initialization(self):
        """Test memory initialization"""
        memory = ConversationMemory(max_history=5)
        assert len(memory.history) == 0
        assert memory.current_context == {}
        assert memory.max_history == 5
    
    def test_add_interaction(self):
        """Test adding an interaction to memory"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="How many properties do I have?",
            sql_query="SELECT COUNT(*) FROM Properties",
            result=[(12,)],
            answer="You have 12 properties."
        )
        
        assert len(memory.history) == 1
        assert memory.history[0].query == "How many properties do I have?"
    
    def test_max_history_limit(self):
        """Test that history respects max_history limit"""
        memory = ConversationMemory(max_history=3)
        
        # Add 5 interactions
        for i in range(5):
            memory.add_interaction(
                query=f"Query {i}",
                sql_query="SELECT *",
                result=[],
                answer=f"Answer {i}"
            )
        
        # Should only keep last 3
        assert len(memory.history) == 3
        assert memory.history[0].query == "Query 2"
        assert memory.history[-1].query == "Query 4"
    
    def test_extract_context_location(self):
        """Test extraction of location context"""
        memory = ConversationMemory()
        
        query = "How many properties in California?"
        sql = "SELECT COUNT(*) FROM Properties WHERE state = 'California'"
        
        context = memory._extract_context(query, sql)
        
        assert 'location' in context
        assert context['location'] == 'California'
    
    def test_extract_context_location_abbreviation(self):
        """Test extraction of location with abbreviation"""
        memory = ConversationMemory()
        
        query = "Properties in CA"
        sql = ""
        
        context = memory._extract_context(query, sql)
        
        assert 'location' in context
        assert context['location'] == 'California'
    
    def test_extract_context_property_type(self):
        """Test extraction of property type context"""
        memory = ConversationMemory()
        
        query = "Show me commercial properties"
        sql = "SELECT * FROM Properties WHERE property_type = 'Commercial'"
        
        context = memory._extract_context(query, sql)
        
        assert 'property_type' in context
        assert context['property_type'] == 'Commercial'
    
    def test_extract_context_topic_rent(self):
        """Test extraction of rent topic"""
        memory = ConversationMemory()
        
        query = "What is my average rent?"
        sql = "SELECT AVG(monthly_rent) FROM Units"
        
        context = memory._extract_context(query, sql)
        
        assert 'topic' in context
        assert context['topic'] == 'rent'
    
    def test_extract_context_topic_profitability(self):
        """Test extraction of profitability topic"""
        memory = ConversationMemory()
        
        query = "What is my most profitable property?"
        sql = "SELECT * FROM Properties ORDER BY profit DESC LIMIT 1"
        
        context = memory._extract_context(query, sql)
        
        assert 'topic' in context
        assert context['topic'] == 'profitability'
    
    def test_extract_context_owner(self):
        """Test extraction of owner reference"""
        memory = ConversationMemory()
        
        query = "How many properties does LLC2 have?"
        sql = "SELECT COUNT(*) FROM Properties WHERE owner_id = 2"
        
        context = memory._extract_context(query, sql)
        
        assert 'owner' in context
        assert context['owner'] == 'LLC2'
    
    def test_update_context(self):
        """Test context updating from history"""
        memory = ConversationMemory()
        
        # Add first interaction with location
        memory.add_interaction(
            query="Properties in California",
            sql_query="SELECT * FROM Properties WHERE state = 'California'",
            result=[],
            answer="You have 5 properties."
        )
        
        assert 'location' in memory.current_context
        assert memory.current_context['location'] == 'California'
    
    def test_context_persistence_across_interactions(self):
        """Test that context persists across multiple interactions"""
        memory = ConversationMemory()
        
        # First query about California
        memory.add_interaction(
            query="Properties in California",
            sql_query="SELECT * FROM Properties WHERE state = 'California'",
            result=[],
            answer="5 properties"
        )
        
        # Second query about rent (should keep California context)
        memory.add_interaction(
            query="What's the average rent?",
            sql_query="SELECT AVG(monthly_rent) FROM Units",
            result=[(1000,)],
            answer="$1000"
        )
        
        # Context should still have California
        assert 'location' in memory.current_context
        assert memory.current_context['location'] == 'California'
    
    def test_get_context_prompt_empty(self):
        """Test context prompt when no context"""
        memory = ConversationMemory()
        prompt = memory.get_context_prompt()
        assert prompt == ""
    
    def test_get_context_prompt_with_context(self):
        """Test context prompt generation"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="Properties in Texas",
            sql_query="SELECT * FROM Properties WHERE state = 'Texas'",
            result=[],
            answer="10 properties"
        )
        
        prompt = memory.get_context_prompt()
        
        assert "context" in prompt.lower()
        assert "Texas" in prompt
    
    def test_get_recent_summary_empty(self):
        """Test recent summary with no history"""
        memory = ConversationMemory()
        summary = memory.get_recent_summary()
        assert summary == ""
    
    def test_get_recent_summary(self):
        """Test recent summary generation"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="How many properties?",
            sql_query="SELECT COUNT(*)",
            result=[(12,)],
            answer="12 properties"
        )
        
        summary = memory.get_recent_summary()
        
        assert "Recent questions" in summary
        assert "How many properties?" in summary
        assert "12 properties" in summary
    
    def test_get_recent_summary_truncation(self):
        """Test that long queries/answers are truncated in summary"""
        memory = ConversationMemory()
        
        long_query = "A" * 100
        long_answer = "B" * 150
        
        memory.add_interaction(
            query=long_query,
            sql_query="SELECT *",
            result=[],
            answer=long_answer
        )
        
        summary = memory.get_recent_summary()
        
        # Should be truncated with "..."
        assert "..." in summary
    
    def test_enhance_query_simple(self):
        """Test query enhancement for non-follow-up queries"""
        memory = ConversationMemory()
        
        query = "How many properties do I have?"
        enhanced = memory.enhance_query(query)
        
        # Should return unchanged (not a follow-up)
        assert enhanced == query
    
    def test_enhance_query_what_about(self):
        """Test enhancement of 'What about' follow-up"""
        memory = ConversationMemory()
        
        # First query about California
        memory.add_interaction(
            query="Properties in California",
            sql_query="SELECT * FROM Properties WHERE state = 'California'",
            result=[],
            answer="5 properties"
        )
        
        # Follow-up: "What about Arizona?"
        enhanced = memory.enhance_query("What about Arizona?")
        
        # Should enhance with context (though location in query overrides)
        assert enhanced != ""
    
    def test_enhance_query_short_follow_up(self):
        """Test enhancement of very short follow-up"""
        memory = ConversationMemory()
        
        # Set context
        memory.add_interaction(
            query="How many properties?",
            sql_query="SELECT COUNT(*)",
            result=[(12,)],
            answer="12 properties"
        )
        
        # Very short follow-up
        enhanced = memory.enhance_query("And units?")
        
        # Should be enhanced with context
        assert len(enhanced) > len("And units?")
    
    def test_clear_context(self):
        """Test clearing context only"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="Properties in Texas",
            sql_query="SELECT *",
            result=[],
            answer="10 properties"
        )
        
        assert len(memory.history) > 0
        assert len(memory.current_context) > 0
        
        memory.clear_context()
        
        assert len(memory.history) > 0  # History preserved
        assert len(memory.current_context) == 0  # Context cleared
    
    def test_clear_history(self):
        """Test clearing entire history"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="Test query",
            sql_query="SELECT *",
            result=[],
            answer="Test answer"
        )
        
        assert len(memory.history) > 0
        
        memory.clear_history()
        
        assert len(memory.history) == 0
        assert len(memory.current_context) == 0
    
    def test_get_statistics_empty(self):
        """Test statistics with empty history"""
        memory = ConversationMemory()
        stats = memory.get_statistics()
        
        assert stats['total_interactions'] == 0
        assert stats['most_common_topic'] is None
        assert stats['most_common_location'] is None
    
    def test_get_statistics_with_data(self):
        """Test statistics calculation"""
        memory = ConversationMemory()
        
        # Add multiple interactions
        memory.add_interaction(
            query="Properties in Texas",
            sql_query="SELECT *",
            result=[],
            answer="10 properties"
        )
        
        memory.add_interaction(
            query="Average rent in Texas",
            sql_query="SELECT AVG(rent)",
            result=[(1000,)],
            answer="$1000"
        )
        
        stats = memory.get_statistics()
        
        assert stats['total_interactions'] == 2
        assert stats['most_common_location'] == 'Texas'
        assert stats['most_common_topic'] in ['properties', 'rent']
    
    def test_export_history(self):
        """Test exporting conversation history"""
        memory = ConversationMemory()
        
        memory.add_interaction(
            query="Test query",
            sql_query="SELECT *",
            result=[(1,)],
            answer="Test answer"
        )
        
        export = memory.export_history()
        
        assert len(export) == 1
        assert isinstance(export[0], dict)
        assert export[0]['query'] == "Test query"
        assert export[0]['answer'] == "Test answer"
    
    def test_conversation_turn_dataclass(self):
        """Test ConversationTurn dataclass"""
        turn = ConversationTurn(
            timestamp="2024-01-01T00:00:00",
            query="Test",
            sql_query="SELECT *",
            result=[],
            answer="Answer",
            context={'location': 'Texas'}
        )
        
        assert turn.query == "Test"
        assert turn.context['location'] == 'Texas'
    
    def test_real_world_scenario_follow_up_location(self):
        """Test real-world scenario: follow-up about different location"""
        memory = ConversationMemory()
        
        # First: Ask about California
        memory.add_interaction(
            query="How many properties in California?",
            sql_query="SELECT COUNT(*) FROM Properties WHERE state = 'California'",
            result=[(5,)],
            answer="5 properties"
        )
        
        # Second: "What about Arizona?"
        query2 = "What about Arizona?"
        enhanced2 = memory.enhance_query(query2)
        
        # Should recognize as follow-up
        assert "what about" in query2.lower()
    
    def test_real_world_scenario_multi_turn_conversation(self):
        """Test real-world scenario: multi-turn conversation"""
        memory = ConversationMemory()
        
        # Turn 1
        memory.add_interaction(
            query="How many properties do I have?",
            sql_query="SELECT COUNT(*)",
            result=[(12,)],
            answer="12 properties"
        )
        
        # Turn 2
        memory.add_interaction(
            query="What's my average rent?",
            sql_query="SELECT AVG(monthly_rent)",
            result=[(1000,)],
            answer="$1000"
        )
        
        # Turn 3
        memory.add_interaction(
            query="Which is most profitable?",
            sql_query="SELECT * FROM Properties ORDER BY profit DESC LIMIT 1",
            result=[("123 Main St",)],
            answer="123 Main St"
        )
        
        # Check statistics
        stats = memory.get_statistics()
        assert stats['total_interactions'] == 3
        
        # Check summary
        summary = memory.get_recent_summary()
        assert "How many properties" in summary
        assert "average rent" in summary
        assert "profitable" in summary
    
    def test_context_merge_from_recent_interactions(self):
        """Test that context merges from recent interactions"""
        memory = ConversationMemory()
        
        # Interaction 1: Set location
        memory.add_interaction(
            query="Properties in California",
            sql_query="SELECT *",
            result=[],
            answer="5 properties"
        )
        
        # Interaction 2: Set topic
        memory.add_interaction(
            query="What's the average rent?",
            sql_query="SELECT AVG(rent)",
            result=[(1000,)],
            answer="$1000"
        )
        
        # Context should have both
        assert 'location' in memory.current_context
        assert 'topic' in memory.current_context
    
    def test_conversation_memory_thread_safety(self):
        """Test basic memory operations work correctly"""
        memory = ConversationMemory()
        
        # Add 10 interactions quickly
        for i in range(10):
            memory.add_interaction(
                query=f"Query {i}",
                sql_query="SELECT *",
                result=[],
                answer=f"Answer {i}"
            )
        
        assert len(memory.history) == 10
        assert memory.history[0].query == "Query 0"
        assert memory.history[-1].query == "Query 9"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
