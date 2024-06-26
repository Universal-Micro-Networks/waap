from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from waap.handler.main import app

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


@patch("waap.handler.main.request_handler")
def test_start_service_mock(mock_request_handler):
    mock_request_handler.return_value = "test"
    response = client.get("/service/?path=get_delay15s&server_id=test")
    assert response.status_code == 200
    assert response.text == '"test"'


@patch("waap.handler.main.request_handler")
def test_create_service_mock(mock_request_handler):
    mock_request_handler.return_value = "test"
    response = client.post("/service/", json={"path": "test", "server_id": "test"})
    assert response.status_code == 200
    assert response.text == '"test"'


def test_start_service_get():
    response = client.get("/service/?path=delay15s&server_id=server_id4")

    assert response.status_code == 200
    assert response.text == '"Hello, GET delay15s mock!"'


def test_start_service_post():
    response = client.post(
        "/service/",
        headers={"Content-Type": "application/json"},
        json={"path": "delay5s", "server_id": "server_id4"},
    )

    assert response.status_code == 200
    assert response.text == '"Hello, POST delay5s mock!"'


def test_start_service_post_error():
    response = client.post(
        "/service/",
        headers={"Content-Type": "application/json"},
        json={"path": "", "server_id": ""},
    )

    assert response.status_code == 422


def test_start_service_post_json_error():
    response = client.post(
        "/service/",
        headers={"Content-Type": "application/json"},
        json={"server_id": "server_id2"},
    )
    assert response.status_code == 422


def test_start_service_get_json_error():
    response = client.get(
        "/service/?server_id=server_id2",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_start_service_get_error():
    response = client.get(
        "/service/?path=&server_id=",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_start_service_timeout():
    response = client.get("/service/?path=delay8m35s&server_id=server_id4")
    assert response.status_code == 408
    assert response.text == '{"detail":"Request timed out"}'
