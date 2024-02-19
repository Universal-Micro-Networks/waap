import json
import os
import uuid
from typing import Any, Dict

import boto3
import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from model.backend_status_type import BackendStatusType

app = FastAPI()

# グローバル変数としてDynamoDBリソースを作成
# DynamoDBサービスに接続
#    dynamodb = boto3.resource("dynamodb")
# ローカルのDynamoDBに接続
# boto3.setup_default_session(region_name="ap-northeast-1")
# ダミーの認証情報を設定
session = boto3.session.Session(
    aws_access_key_id="DUMMY_ACCESS_KEY",
    aws_secret_access_key="DUMMY_SECRET_KEY",
    region_name="ap-northeast-1",
)
dynamodb_uri = os.getenv("DYNAMODB_URI")
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_uri)

# S3にアクセスするためのクライアント
s3 = boto3.resource(
    "s3",
    endpoint_url=os.getenv("MINIO_URI"),  # MinIOサーバーのエンドポイントURL
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),  # MinIOのアクセスキー
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),  # MinIOのシークレットキー
    region_name="ap-northeast-1",
)
# バケット名を指定してバケットを取得
bucket = s3.Bucket("waap")


def get_data_source(server_id: str) -> str:
    obj = s3.Object("waap", "servers.json")
    body = obj.get()["Body"].read()
    decoded_body = body.decode("utf-8")
    query_json = json.loads(decoded_body)
    if server_id in query_json:
        return query_json[server_id]
    else:
        return "Server ID not found in the JSON file."


def get_table(name):
    return dynamodb.Table(name)


@app.api_route(
    "/task/{original_path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    status_code=201,
)
async def create_task(
    request: Request,
    data: Dict[Any, Any],
    original_path: str,
    background_tasks: BackgroundTasks,
):
    headers = dict(request.headers)
    server_id = headers.get("x-server-id")
    print(headers.get("x-server-id"))
    server_uri = get_data_source(server_id)
    server_uri = server_uri + original_path
    print(server_uri)
    params = dict(request.query_params)

    transaction_id = str(uuid.uuid4())

    background_tasks.add_task(
        _send_api_request,
        request.method,
        server_uri,
        headers,
        data,
        params,
        transaction_id,
    )

    # テーブルを指定
    table = get_table("tasks")
    # レコードを追加status
    table.put_item(
        Item={
            "transaction_id": transaction_id,
            "backend_response": "",
            "backend_status": BackendStatusType.NOT_STARTED,
        }
    )

    return {"transaction_id": transaction_id}


@app.get("/check/{transaction_id}")
async def check_task(transaction_id: str):

    # テーブルを指定
    table = get_table("tasks")

    # TODO: ここでDynamoDBのテーブルを検索して、transaction_idに紐づくレコードがあるか確認する
    response = table.get_item(Key={"transaction_id": transaction_id})
    # アイテムがなければ、404を返す
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Item not found")

    response_data = response.get("Item")

    # あれば、そのレコードを返す
    return {
        "response": response_data["backend_response"],
        "status": response_data["backend_status"],
    }


def _send_api_request(
    method: str, url: str, headers: dict, data: dict, params: dict, transaction_id: str
) -> None:
    import time

    time.sleep(25)  # 長時間実行する処理をシミュレート
    _update_task_table(transaction_id, BackendStatusType.RUNNING, "")
    response = requests.request(method, url, headers=headers, data=data, params=params)
    # TODO: ここでDynamoDBにtransaction_idとレスポンスを保存する
    if response.text is not None:
        _update_task_table(transaction_id, BackendStatusType.FINISHED, response.text)
    else:
        _update_task_table(transaction_id, BackendStatusType.FAILED, response.text)


def _update_task_table(
    transaction_id: str, backend_status_type: str, backend_response: str
) -> None:
    # テーブルを指定
    table = get_table("tasks")
    # アイテムを更新
    table_response = table.update_item(
        Key={"transaction_id": transaction_id},
        UpdateExpression="set backend_response = :r ,backend_status = :s",
        ExpressionAttributeValues={":r": backend_response, ":s": backend_status_type},
        ReturnValues="UPDATED_NEW",
    )
    print(table_response)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8088)
