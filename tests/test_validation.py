"""
Unit Tests for Answer Validation Module
========================================
Tests the AnswerValidator class to ensure proper validation of LLM answers
against SQL results.
"""

import pytest
from agent.validation import AnswerValidator


class TestAnswerValidator:
    """Test suite for AnswerValidator"""
    
    def test_extract_numbers_simple(self):
        """Test extracting numbers from simple text"""
        text = "You have 15 properties."
        numbers = AnswerValidator.extract_numbers(text)
        assert numbers == [15.0]
    
    def test_extract_numbers_multiple(self):
        """Test extracting multiple numbers"""
        text = "You have 15 properties with an average rent of $1,234.56."
        numbers = AnswerValidator.extract_numbers(text)
        assert 15.0 in numbers
        assert 1234.56 in numbers
    
    def test_extract_numbers_currency(self):
        """Test extracting numbers with currency"""
        text = "Total: $5,432.10"
        numbers = AnswerValidator.extract_numbers(text)
        assert 5432.10 in numbers
    
    def test_extract_numbers_comma_separated(self):
        """Test extracting numbers with comma separators"""
        text = "The value is 1,234,567.89"
        numbers = AnswerValidator.extract_numbers(text)
        assert 1234567.89 in numbers
    
    def test_extract_numbers_no_numbers(self):
        """Test text with no numbers"""
        text = "This is descriptive text only."
        numbers = AnswerValidator.extract_numbers(text)
        assert numbers == []
    
    def test_extract_sql_numbers_list_of_tuples(self):
        """Test extracting numbers from SQL result (list of tuples)"""
        sql_result = [(12,), (34,)]
        numbers = AnswerValidator.extract_sql_numbers(sql_result)
        assert 12.0 in numbers
        assert 34.0 in numbers
    
    def test_extract_sql_numbers_single_value(self):
        """Test extracting number from single value result"""
        sql_result = 42
        numbers = AnswerValidator.extract_sql_numbers(sql_result)
        assert numbers == [42.0]
    
    def test_extract_sql_numbers_mixed_types(self):
        """Test extracting numbers from mixed type results"""
        sql_result = [(123, "text", 456.78)]
        numbers = AnswerValidator.extract_sql_numbers(sql_result)
        assert 123.0 in numbers
        assert 456.78 in numbers
    
    def test_extract_sql_numbers_empty(self):
        """Test empty SQL result"""
        sql_result = []
        numbers = AnswerValidator.extract_sql_numbers(sql_result)
        assert numbers == []
    
    def test_numbers_match_exact(self):
        """Test exact number matching"""
        assert AnswerValidator.numbers_match(100, 100) == True
    
    def test_numbers_match_within_tolerance(self):
        """Test number matching within tolerance"""
        # 2% tolerance by default
        assert AnswerValidator.numbers_match(100, 101) == True
        assert AnswerValidator.numbers_match(100, 102) == True
        assert AnswerValidator.numbers_match(100, 103) == False
    
    def test_numbers_match_zero_case(self):
        """Test number matching with zero"""
        assert AnswerValidator.numbers_match(0, 0) == True
        assert AnswerValidator.numbers_match(0, 0.005) == True
        assert AnswerValidator.numbers_match(0, 0.02) == False
    
    def test_validate_answer_matching(self):
        """Test validation with matching numbers"""
        sql_result = [(12,)]
        llm_answer = "You have 12 properties."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert warning is None
        assert confidence == 1.0
    
    def test_validate_answer_hallucination(self):
        """Test detection of hallucinated numbers"""
        sql_result = [(12,)]
        llm_answer = "You have 15 properties."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == False
        assert warning is not None
        assert "15" in warning or "15.0" in warning
        assert confidence < 1.0
    
    def test_validate_answer_multiple_numbers(self):
        """Test validation with multiple numbers"""
        sql_result = [(12, 1234.56)]
        llm_answer = "You have 12 properties with average rent of $1,234.56."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert warning is None
        assert confidence == 1.0
    
    def test_validate_answer_partial_match(self):
        """Test validation with some matching and some non-matching numbers"""
        sql_result = [(12,)]
        llm_answer = "You have 12 properties and 999 units."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == False
        assert warning is not None
        assert "999" in warning or "999.0" in warning
        assert 0.3 <= confidence < 1.0
    
    def test_validate_answer_descriptive_no_numbers(self):
        """Test validation of descriptive answer without numbers"""
        sql_result = [(12,)]
        llm_answer = "Here are your properties:"
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert warning is None
        assert confidence == 1.0
    
    def test_validate_answer_numbers_in_answer_no_sql_numbers(self):
        """Test suspicious case: numbers in answer but not in SQL"""
        sql_result = [("text",)]
        llm_answer = "You have 15 properties."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == False
        assert warning is not None
        assert confidence < 0.5
    
    def test_validate_answer_with_tolerance(self):
        """Test validation with custom tolerance"""
        sql_result = [(100,)]
        llm_answer = "The value is 105."
        
        # With default 2% tolerance - should fail
        is_valid_strict, _, _ = AnswerValidator.validate_answer(
            sql_result, llm_answer, tolerance=0.02
        )
        assert is_valid_strict == False
        
        # With 10% tolerance - should pass
        is_valid_loose, _, _ = AnswerValidator.validate_answer(
            sql_result, llm_answer, tolerance=0.10
        )
        assert is_valid_loose == True
    
    def test_format_validated_answer_valid(self):
        """Test formatting of valid answer"""
        answer = "You have 12 properties."
        formatted = AnswerValidator.format_validated_answer(
            answer, is_valid=True, warning=None, confidence=1.0
        )
        
        assert formatted == answer
        assert "WARNING" not in formatted
    
    def test_format_validated_answer_with_warning(self):
        """Test formatting with validation warning"""
        answer = "You have 15 properties."
        warning = "Number 15 doesn't match SQL result"
        formatted = AnswerValidator.format_validated_answer(
            answer, is_valid=False, warning=warning, confidence=0.5
        )
        
        assert answer in formatted
        assert warning in formatted
        assert "Confidence" in formatted
    
    def test_format_validated_answer_low_confidence(self):
        """Test formatting with low confidence"""
        answer = "The result is 100."
        formatted = AnswerValidator.format_validated_answer(
            answer, is_valid=True, warning=None, confidence=0.4
        )
        
        assert answer in formatted
        assert "Confidence" in formatted
        assert "LOW" in formatted or "🔴" in formatted
    
    def test_format_validated_answer_medium_confidence(self):
        """Test formatting with medium confidence"""
        answer = "The result is 100."
        formatted = AnswerValidator.format_validated_answer(
            answer, is_valid=True, warning=None, confidence=0.6
        )
        
        assert answer in formatted
        assert "Confidence" in formatted
        assert "MEDIUM" in formatted or "🟡" in formatted
    
    def test_format_validated_answer_with_raw_result(self):
        """Test formatting includes raw SQL result on failure"""
        answer = "Wrong answer"
        sql_result = [(12,)]
        formatted = AnswerValidator.format_validated_answer(
            answer, is_valid=False, warning="Test warning", 
            confidence=0.3, sql_result=sql_result
        )
        
        assert answer in formatted
        assert "Raw SQL Result" in formatted
        assert str(sql_result) in formatted
    
    def test_validate_and_format_convenience(self):
        """Test convenience method validate_and_format"""
        sql_result = [(12,)]
        llm_answer = "You have 12 properties."
        
        formatted_answer, is_valid, confidence = AnswerValidator.validate_and_format(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert confidence == 1.0
        assert "12" in formatted_answer
    
    def test_validate_and_format_with_failure(self):
        """Test convenience method with validation failure"""
        sql_result = [(12,)]
        llm_answer = "You have 999 properties."
        
        formatted_answer, is_valid, confidence = AnswerValidator.validate_and_format(
            sql_result, llm_answer, include_raw_result=True
        )
        
        assert is_valid == False
        assert confidence < 1.0
        assert "WARNING" in formatted_answer
        assert "Raw SQL Result" in formatted_answer
    
    def test_validate_real_world_scenario_property_count(self):
        """Test real-world scenario: property count query"""
        sql_result = [(22,)]
        llm_answer = "You have 22 properties in your portfolio."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert confidence == 1.0
    
    def test_validate_real_world_scenario_average_rent(self):
        """Test real-world scenario: average rent query"""
        sql_result = [(970.49,)]
        llm_answer = "Your average rent is $970.49 per month."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer
        )
        
        assert is_valid == True
        assert confidence == 1.0
    
    def test_validate_real_world_scenario_rounded_number(self):
        """Test real-world scenario: LLM rounds number slightly"""
        sql_result = [(970.49,)]
        llm_answer = "Your average rent is approximately $970 per month."
        
        is_valid, warning, confidence = AnswerValidator.validate_answer(
            sql_result, llm_answer, tolerance=0.05
        )
        
        # Should pass with 5% tolerance
        assert is_valid == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
