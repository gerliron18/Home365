"""
Pytest configuration with rate limiting for API calls
"""
import pytest
import time


@pytest.fixture(scope="function", autouse=True)
def rate_limit():
    """Add delay between tests to avoid API rate limits (5 requests/minute)"""
    yield
    # Sleep 15 seconds between tests (4 tests/minute = under 5/minute limit)
    time.sleep(15)
