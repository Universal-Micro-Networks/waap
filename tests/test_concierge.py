import asyncio
import os
import uuid
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.testclient import TestClient
from moto import mock_aws
from requests import RequestException
from waap.concierge.main import _send_api_request, app
from waap.concierge.model.backend_status_type import BackendStatusType

from .conftest import async_client


@pytest.fixture
def client():
    return TestClient(app)


def test_get_data_source():
    from waap.concierge.main import get_data_source

    server_id = "server_id1"
    result = get_data_source(server_id)
    assert result == "https://www.google.co.jp/"


def test_get_table():
    from waap.concierge.main import get_table

    result = get_table()
    assert result is not None


def test_create_task_for_get(client):
    response = client.get("/task/test", headers={"x-server-id": "server_id2"})
    assert response.status_code == 201
    assert "transaction_id" in response.json()


def test_create_task_for_post(client):
    response = client.post(
        "/task/test",
        headers={"x-server-id": "server_id2"},
        json={"original_path": "/test"},
    )
    assert response.status_code == 201
    assert "transaction_id" in response.json()


def test_check_task_error(client):
    response = client.get(f"/check/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"


def test_check_task(client):
    response = client.post(
        "/task/test",
        headers={"x-server-id": "server_id2"},
        json={"original_path": "/test"},
    )
    transaction_id = response.json()["transaction_id"]

    response = client.get(f"/check/{transaction_id}")
    assert response.status_code == 200
    assert response.json()["transaction_id"] == transaction_id


@patch("waap.concierge.main._send_api_request")
def test_create_task_for_post_mock(mock_send_api_request, client):
    # ヘッダーを設定
    client.headers.update({"x-server-id": "server_id2"})
    # テストリクエストの送信
    response = client.post("/task/admin", json={})

    # レスポンスの検証
    assert response.status_code == 201
    assert "transaction_id" in response.json()

    # モックオブジェクトの呼び出しを検証
    mock_send_api_request.assert_called_once()


def test_send_api_request(client):
    #    app.dependency_overrides[get_table] = override_get_table

    # テストデータの設定
    method = "test_method"
    url = "http://0.0.0.0:8038/admin/"
    headers = {"test_header": "test_value"}
    data = {"test_data": "test_value"}
    params = {"test_param": "test_value"}
    transaction_id = "test_id"

    # テストの実行
    from waap.concierge.main import _send_api_request

    _send_api_request(method, url, headers, data, params, transaction_id)

    # モックオブジェクトの呼び出しを検証
    import time

    time.sleep(1)
    assert True


@patch("waap.concierge.main._send_api_request")
def test_send_request(mock_send_api_request, client):
    #    app.dependency_overrides[get_table] = override_get_table
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


#    app.dependency_overrides[get_table] = {}


@patch("waap.concierge.main._send_api_request")
def test_multiple_access(mock_send_api_request, client):
    #    app.dependency_overrides[get_table] = override_get_table
    # テストデータを作成
    original_path = "/test"
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
    for _ in range(5):
        response = client.get("/task" + original_path, headers=headers)
        # レスポンスのステータスコードを確認
        assert response.status_code == 201
        # レスポンスの内容を確認
        response_data = response.json()
        assert "transaction_id" in response_data
        assert uuid.UUID(response_data["transaction_id"])


#    app.dependency_overrides[get_table] = {}


def test_send_request_headers_error(client):
    #    app.dependency_overrides[get_table] = override_get_table
    if "x-server-id" in client.headers:
        del client.headers["x-server-id"]

    response = client.get("/task/test", headers={"x-server": "server_id2"})

    assert response.status_code == 422


def test_send_check_request_uri_error(client):
    if "x-server" in client.headers:
        del client.headers["x-server"]

    response_get = client.get("/task/nodata", headers={"x-server-id": "server_id2"})
    transaction_id = response_get.json()["transaction_id"]

    response_check = client.get(f"/check/{transaction_id}")

    assert response_check.json()["status"] == "FAILED"


# グローバル変数
task_finished_first = ""


@pytest.mark.asyncio
async def test_async_get_multiple_request(async_client):
    global task_finished_first

    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(
            async_client.get("/task/test", headers={"x-server-id": "server_id2"}),
            name="task1",
        )
        task2 = tg.create_task(
            async_client.get("/task/test2", headers={"x-server-id": "server_id2"}),
            name="task2",
        )

        def on_done(task_name):
            global task_finished_first
            if task_finished_first == "":
                task_finished_first = task_name

        task1.add_done_callback(lambda _: on_done("task1"))
        task2.add_done_callback(lambda _: on_done("task2"))

    assert task_finished_first == "task2"


def test_send_request_uri_error(client):
    #    app.dependency_overrides[get_table] = override_get_table
    if "x-server" in client.headers:
        del client.headers["x-server"]

    response_get = client.get("/task/nodata", headers={"x-server-id": "server_id2"})
    transaction_id = response_get.json()["transaction_id"]

    response_check = client.get(f"/check/{transaction_id}")

    #    assert response_check.status_code == 404
    assert response_check.json()["status"] == "FAILED"


def test_send_request_json_error(client):
    #    app.dependency_overrides[get_table] = override_get_table
    if "x-server" in client.headers:
        del client.headers["x-server"]
    # ヘッダーを設定
    client.headers.update({"x-server-id": "server_id2", "Content-Type": "plain/text"})
    with pytest.raises(HTTPException) as e:
        _ = client.get("/task/test")

    assert str(e.value) == "400: Invalid Content-Type"


@patch("waap.concierge.main.get_table")
def test_update_task_table(mock_get_table, client):
    from waap.concierge.main import _update_task_table

    # モックテーブルを作成し、update_itemメソッドをモック化
    mock_table = MagicMock()
    mock_table.update_item.return_value = {
        "Attributes": {
            "transaction_id": "1234",
            "backend_response": "response",
            "backend_status": "status",
        }
    }
    mock_get_table.return_value = mock_table

    # テストデータを設定
    transaction_id = "1234"
    backend_status_type = "status"
    backend_response = "response"

    # 関数を実行
    _update_task_table(transaction_id, backend_status_type, backend_response)

    # update_itemメソッドが期待通りに呼び出されたことを確認
    mock_table.update_item.assert_called_once_with(
        Key={"transaction_id": transaction_id},
        UpdateExpression="set backend_response = :r ,backend_status = :s",
        ExpressionAttributeValues={":r": backend_response, ":s": backend_status_type},
        ReturnValues="ALL_NEW",
    )


@patch("waap.concierge.main.requests.request")
@patch("waap.concierge.main._update_task_table")
def test_send_api_request_exception(mock_update_task_table, mock_request, mocker):
    # RequestExceptionを発生させるようにrequests.requestを設定
    mock_request.side_effect = RequestException()

    # テスト対象の関数を呼び出す
    _send_api_request("GET", "http://test.url", {}, {}, {}, "test_transaction_id")

    # _update_task_tableが適切に呼び出されたことを確認
    mock_update_task_table.assert_any_call(
        "test_transaction_id", BackendStatusType.FAILED, mocker.ANY
    )


def test_create_task_exception(client):
    # RequestExceptionを発生させるようにrequests.requestを設定
    response = client.post(
        "/task/test",
        headers={"x-server-id": ""},
        json={"original_path": ""},
    )
    assert response.status_code == 422


def test_create_task_post_server_id_exception(client):
    # RequestExceptionを発生させるようにrequests.requestを設定
    response = client.post(
        "/task/test",
        headers={"x-server-id": "server_id5"},
        json={"original_path": ""},
    )

    assert response.status_code == 404
    assert response.json() == {"message": "An error occurred: ServerID not found"}


def test_create_task_get_server_id_exception(client):
    # RequestExceptionを発生させるようにrequests.requestを設定
    response = client.get("/task/test", headers={"x-server-id": "server_id5"})

    assert response.status_code == 404
    assert response.json() == {"message": "An error occurred: ServerID not found"}


def test_get_table_exists_mock():
    from waap.concierge.main import get_table

    with patch("waap.concierge.main.dynamodb.Table") as mock_table:
        mock_table.return_value.table_status = "ACTIVE"
        table = get_table()
        mock_table.assert_any_call("tasks")
        assert table.table_status == "ACTIVE"


def test_get_table_not_exists_mock():
    from waap.concierge.main import get_table

    with patch("waap.concierge.main.dynamodb.Table") as mock_table:
        mock_table.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFoundException"}},
            operation_name="DescribeTable",
        )
        with pytest.raises(ClientError) as e:
            get_table()
        mock_table.assert_any_call("tasks")
        assert e.value.response["Error"]["Code"] == "ResourceNotFoundException"


@mock_aws
def test_get_table_exists_moto():
    from waap.concierge.main import get_table

    dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
    dynamodb.create_table(
        TableName="tasks",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    table = get_table()
    assert table.table_status == "ACTIVE"


@mock_aws
def test_check_task_item_not_found(client):
    # テスト用のDynamoDBテーブルを作成
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    table = dynamodb.create_table(
        TableName="tasks",
        KeySchema=[{"AttributeName": "transaction_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "transaction_id", "AttributeType": "S"}
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # 存在しないtransaction_idでcheck_taskを呼び出す
    response = client.get("/check/nonexistent_id")

    # 404エラーが返されることを確認
    assert response.status_code == 404
