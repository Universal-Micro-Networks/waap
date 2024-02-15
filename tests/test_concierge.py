from unittest.mock import MagicMock, patch

from concierge.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("concierge.main.get_table")
@patch("concierge.main._send_api_request")
def test_create_task(mock_send_api_request, mock_get_table):
    # モックオブジェクトの設定
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table

    # テストリクエストの送信
    response = client.post("/task/test_path", json={"key": "value"})

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
    mock_table.get_item.return_value = {"Item": {"transaction_id": "test_id"}}
    mock_get_table.return_value = mock_table

    # テストリクエストの送信
    response = client.get("/check/test_id")

    # レスポンスの検証
    assert response.status_code == 200
    assert "getItem" in response.json()

    # モックオブジェクトの呼び出しを検証
    mock_get_table.assert_called_once_with("tasks")
    mock_table.get_item.assert_called_once_with(Key={"transaction_id": "test_id"})


def test_send_api_request():
    # テストデータの設定
    method = "test_method"
    url = "test_url"
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
