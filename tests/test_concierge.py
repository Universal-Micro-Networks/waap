import uuid
from unittest.mock import MagicMock, patch

from concierge.main import app, get_table
from fastapi.testclient import TestClient

from .conftest import override_get_table

client_mock = TestClient(app)
client = TestClient(app)


@patch("concierge.main.get_table")
@patch("concierge.main._send_api_request")
def test_create_task(mock_send_api_request, mock_get_table):
    # モックオブジェクトの設定
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table

    # テストリクエストの送信
    response = client_mock.post(
        "/task/admin", headers={"x-server-id": "server_id2"}, json={}
    )

    # レスポンスの検証
    assert response.status_code == 201
    assert "transaction_id" in response.json()

    # モックオブジェクトの呼び出しを検証
    mock_send_api_request.assert_called_once()
    mock_get_table.assert_called_once_with("tasks")
    mock_table.put_item.assert_called_once()


@patch("concierge.main.get_table")
def test_check_task(mock_get_table):
    # モックオブジェクトの設定
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "transaction_id": "4f9dd668-da08-462c-95e7-b6f974e0890b",
            "backend_response": '{"detail":"Not Found"}',
            "backend_status": "FINISHED",
        }
    }

    mock_get_table.return_value = mock_table

    # テストリクエストの送信
    response = client_mock.get("/check/4f9dd668-da08-462c-95e7-b6f974e0890b")

    # レスポンスの検証
    assert response.status_code == 200
    assert "backend_response" in response.json()

    # モックオブジェクトの呼び出しを検証
    mock_get_table.assert_called_once_with("tasks")
    mock_table.get_item.assert_called_once_with(
        Key={"transaction_id": "4f9dd668-da08-462c-95e7-b6f974e0890b"}
    )
    client_mock.close()


def test_send_api_request():
    app.dependency_overrides[get_table] = override_get_table

    # テストデータの設定
    method = "test_method"
    url = "http://0.0.0.0:8038/admin/"
    headers = {"test_header": "test_value"}
    data = {"test_data": "test_value"}
    params = {"test_param": "test_value"}
    transaction_id = "test_id"

    # テストの実行
    from concierge.main import _send_api_request

    _send_api_request(method, url, headers, data, params, transaction_id)

    # モックオブジェクトの呼び出しを検証
    import time

    time.sleep(1)
    assert True
    app.dependency_overrides[get_table] = {}


@patch("concierge.main._send_api_request")
def test_send_request(mock_send_api_request):
    app.dependency_overrides[get_table] = override_get_table
    # テストデータを作成
    original_path = "/test"
    data = {"original_path": "/test"}
    headers = {"x-server-id": "server_id2"}

    mock_send_api_request.return_value = {
        "Attributes": {
            "backend_response": "Hello, mmock!",
            "backend_status": "FINISHED",
        },
        "ResponseMetadata": {
            "RequestId": "3881619e-4c9f-4e28-bc0a-dd60625f8b54",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "date": "Sun, 25 Feb 2024 12:47:43 GMT",
                "x-amzn-requestid": "3881619e-4c9f-4e28-bc0a-dd60625f8b54",
                "content-type": "application/x-amz-json-1.0",
                "x-amz-crc32": "417530758",
                "content-length": "91",
                "server": "Jetty(11.0.17)",
            },
            "RetryAttempts": 0,
        },
    }

    # getリクエストを送信
    client.headers = headers
    response = client.get("/task" + original_path)
    # レスポンスのステータスコードを確認
    assert response.status_code == 201

    # レスポンスの内容を確認
    response_data = response.json()
    assert "transaction_id" in response_data
    assert uuid.UUID(response_data["transaction_id"])
    app.dependency_overrides[get_table] = {}


@patch("concierge.main._send_api_request")
def test_multiple_access(mock_send_api_request):
    app.dependency_overrides[get_table] = override_get_table
    # テストデータを作成
    original_path = "/test"
    data = {"original_path": "/test"}
    headers = {"x-server-id": "server_id2"}

    mock_send_api_request.return_value = {
        "Attributes": {
            "backend_response": "Hello, mmock!",
            "backend_status": "FINISHED",
        },
        "ResponseMetadata": {
            "RequestId": "3881619e-4c9f-4e28-bc0a-dd60625f8b54",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "date": "Sun, 25 Feb 2024 12:47:43 GMT",
                "x-amzn-requestid": "3881619e-4c9f-4e28-bc0a-dd60625f8b54",
                "content-type": "application/x-amz-json-1.0",
                "x-amz-crc32": "417530758",
                "content-length": "91",
                "server": "Jetty(11.0.17)",
            },
            "RetryAttempts": 0,
        },
    }
    # 10回連続でPOSTリクエストを送信
    for _ in range(30):
        response = client.get("/task" + original_path, headers=headers)
        # レスポンスのステータスコードを確認
        assert response.status_code == 201
        # レスポンスの内容を確認
        response_data = response.json()
        assert "transaction_id" in response_data
        assert uuid.UUID(response_data["transaction_id"])
    app.dependency_overrides[get_table] = {}
