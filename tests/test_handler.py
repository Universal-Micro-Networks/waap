from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from handler.main import app

client = TestClient(app)


def test_root():
    # GETリクエストを送信
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_say_hello():
    # GETリクエストを送信
    response = client.get("/hello/test")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello test"}


@patch("handler.main.request_handler")
def test_start_service_mock(mock_request_handler):
    mock_request_handler.return_value = "test"
    response = client.get("/service/?path=test&server_id=test")
    assert response.status_code == 200
    assert response.text == '"test"'


@patch("handler.main.request_handler")
def test_create_service_mock(mock_request_handler):
    mock_request_handler.return_value = "test"
    response = client.post("/service/?path=test&server_id=test")
    assert response.status_code == 201
    assert response.text == '"test"'


def test_start_service_get():
    response = client.get("/service/?path=test&server_id=server_id2")

    assert response.status_code == 201
    assert response.text == '"Hello, mock!"'


def test_start_service_post():
    response = client.post("/service/?path=test&server_id=server_id2")

    assert response.status_code == 201
    assert response.text == '"Hello, POST mock!"'
