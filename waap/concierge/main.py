import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
import botocore
import requests
import uvicorn
from boto3.dynamodb.table import TableResource
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from moto.dynamodb.exceptions import ResourceNotFoundException
from waap.middleware.conten_type_validation_middleware import (
    ContentTypeValidationMiddleware,
)

from model.backend_status_type import BackendStatusType

app = FastAPI()
app.add_middleware(ContentTypeValidationMiddleware)

# スクリプトのあるディレクトリを取得
dir_path = os.path.dirname(os.path.realpath(__file__))
# logconf.iniの絶対パスを作成
logconf_path = os.path.join(dir_path, "../../logconf.ini")

# ログ設定を読み込む
logging.config.fileConfig(logconf_path)
logger = logging.getLogger("concierge")


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
bucket_name = os.getenv("MINIO_BUCKET_NAME")
bucket = s3.Bucket("waap")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"An error occurred: {exc.detail}"},
    )


def get_data_source(server_id: str) -> str:
    obj = s3.Object("waap", "servers.json")
    body = obj.get()["Body"].read()
    decoded_body = body.decode("utf-8")
    query_json = json.loads(decoded_body)
    if server_id in query_json:
        return query_json[server_id]
    else:
        return ""


def get_table() -> TableResource:
    name = "tasks"
    try:
        table = dynamodb.Table(name)
        status = table.table_status
        print(f'Table "{name}" exists with status "{status}".')
    except botocore.exceptions.ClientError as e:
        print(f'Table "{name}" does not exist.')

    return dynamodb.Table(name)


@app.get("/task/{original_path}", status_code=201)
async def create_task_for_get(
    request: Request,
    original_path: str,
    background_tasks: BackgroundTasks,
    table: TableResource = Depends(get_table),
):
    headers = dict(request.headers)
    server_id = headers.get("x-server-id")

    if not original_path or not server_id:
        raise HTTPException(status_code=422, detail="Path or server_id not provided")

    server_uri = get_data_source(server_id)
    if server_uri == "":
        raise HTTPException(status_code=404, detail="ServerID not found")
    server_uri = server_uri + original_path
    params = dict(request.query_params)

    transaction_id = str(uuid.uuid4())

    background_tasks.add_task(
        _send_api_request,
        request.method,
        server_uri,
        headers,
        {},
        params,
        transaction_id,
    )

    # テーブルを指定
    table.put_item(
        Item={
            "transaction_id": transaction_id,
            "backend_response": "",
            "backend_status": BackendStatusType.NOT_STARTED,
        }
    )
    return {"transaction_id": transaction_id}


@app.api_route(
    "/task/{original_path}",
    methods=["POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    status_code=201,
)
async def create_task(
    request: Request,
    data: Dict[Any, Any],
    original_path: str,
    background_tasks: BackgroundTasks,
    table: TableResource = Depends(get_table),
):
    if not original_path or not request.headers.get("x-server-id"):
        raise HTTPException(status_code=422, detail="Path or server_id not provided")

    headers = dict(request.headers)
    server_id = headers.get("x-server-id")
    server_uri = get_data_source(server_id)
    if server_uri == "":
        raise HTTPException(status_code=404, detail="ServerID not found")
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
async def check_task(transaction_id: str, table: TableResource = Depends(get_table)):
    # transaction_idがなければ、422を返すという処理は不要
    # なぜなら、FastAPIが自動的にパスパラメータの型をチェックしエラーの場合は422を返す為

    # TODO: ここでDynamoDBのテーブルを検索して、transaction_idに紐づくレコードがあるか確認する
    response = table.get_item(Key={"transaction_id": transaction_id})

    # アイテムがなければ、404を返す
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Item not found")

    response_data = response.get("Item")
    print(response_data)

    backend_response = response_data.get("backend_response")
    backend_status = response_data.get("backend_status", "")

    # あれば、そのレコードを返す
    return {
        "transaction_id": transaction_id,
        "response": backend_response,
        "status": backend_status,
    }


def _send_api_request(
    method: str, url: str, headers: dict, data: dict, params: dict, transaction_id: str
) -> None:
    logger.debug(f"Sending request to {url} with transaction_id {transaction_id}")

    _update_task_table(transaction_id, BackendStatusType.RUNNING, "")
    try:
        response = requests.request(
            method, url, headers=headers, data=data, params=params
        )
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Request to {url} with transaction_id {transaction_id} failed: {e}"
        )
        _update_task_table(transaction_id, BackendStatusType.FAILED, str(e))
        return

    # TODO: ここでDynamoDBにtransaction_idとレスポンスを保存する
    if response.text != "":
        _update_task_table(transaction_id, BackendStatusType.FINISHED, response.text)
    elif response.status_code != 200:
        _update_task_table(
            transaction_id, BackendStatusType.FAILED, response.status_code
        )


def _update_task_table(
    transaction_id: str,
    backend_status_type: str,
    backend_response: str,
) -> None:
    # アイテムを更新
    table = get_table()
    table_response = table.update_item(
        Key={"transaction_id": transaction_id},
        UpdateExpression="set backend_response = :r ,backend_status = :s",
        ExpressionAttributeValues={":r": backend_response, ":s": backend_status_type},
        ReturnValues="ALL_NEW",
    )
    print(table_response)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8088)
