import pytest
from backend.app.db.session import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
