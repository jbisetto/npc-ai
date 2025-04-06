import pytest

def pytest_configure(config):
    """Configure pytest with custom marks."""
    config.addinivalue_line(
        "markers",
        "performance: mark test as a performance test"
    )

@pytest.fixture(scope="session")
def performance_threshold():
    """Fixture providing performance thresholds."""
    return {
        "max_prompt_gen_time": 0.5,  # 500ms
        "max_memory_increase": 50 * 1024 * 1024,  # 50MB
        "max_token_est_time": 0.1  # 100ms
    } 