import uuid
from typing import Any, Dict

import boto3
import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

app = FastAPI()

# グローバル変数としてDynamoDBリソースを作成
# DynamoDBサービスに接続
#    dynamodb = boto3.resource("dynamodb")
# ローカルのDynamoDBに接続
dynamodb = boto3.resource("dynamodb", endpoint_url="http://127.0.0.1:8000")


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
    params = dict(request.query_params)

    transaction_id = str(uuid.uuid4())

    background_tasks.add_task(
        _send_api_request,
        request.method,
        original_path,
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
            "backend_status": "",
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

    item = response["Item"]
    print(item)
    # あれば、そのレコードを返す
    return {"getItem": item}


def _send_api_request(
    method: str, url: str, headers: dict, data: dict, params: dict, transaction_id: str
) -> None:
    response = requests.request(method, url, headers=headers, data=data, params=params)
    # TODO: ここでDynamoDBにtransaction_idとレスポンスを保存する
    if response.text is not None:
        # テーブルを指定
        table = get_table("tasks")
        # アイテムを更新
        table_response = table.update_item(
            Key={"transaction_id": transaction_id},
            UpdateExpression="set backend_response = :r , backend_status = :s",
            ExpressionAttributeValues={":r": response.text, ":s": response.status_code},
            ReturnValues="UPDATED_NEW",
        )
        print(table_response)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8088)
