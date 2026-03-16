import os
import pytest


@pytest.fixture(autouse=True)
def set_env():
    os.environ["DB_DSN"] = "sqlite:///:memory:"
    os.environ["WORKERS_TYPE"] = "processes"
    os.environ["LEMMAS_CACHE_MAX_SIZE"] = "1000"
