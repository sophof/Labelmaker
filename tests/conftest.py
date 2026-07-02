import pytest
from fastapi.testclient import TestClient

import main

VALID = {"system_id": "small-transparent-boxes", "box_id": "standard-box", "style_id": "plain"}


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c
