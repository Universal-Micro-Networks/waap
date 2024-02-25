import pytest
from fastapi.testclient import TestClient
from handler.main import (
    app,
)  # your_appはあなたのFastAPIアプリケーションの名前に置き換えてください


def test_root():
    client = TestClient(app)

    # GETリクエストを送信
    response = client.get("/")

    # レスポンスのステータスコードを確認
    assert response.status_code == 200

    # レスポンスの内容を確認
    assert response.json() == {"message": "Hello World"}


def test_say_hello():
    client = TestClient(app)

    # GETリクエストを送信
    response = client.get("/hello/test")

    # レスポンスのステータスコードを確認
    assert response.status_code == 200

    # レスポンスの内容を確認
    assert response.json() == {"message": "Hello test"}
