import uuid

import boto3
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

app = FastAPI()


@app.api_route(
    "/task/{original_path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    status_code=201,
)
async def create_task(
    request: Request, original_path: str, background_tasks: BackgroundTasks
):
    headers = dict(request.headers)
    params = dict(request.query_params)
    data = await request.json()

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

    return {"transaction_id": transaction_id}


@app.get("/check/{transaction_id}")
async def check_task(transaction_id: str):
    # DynamoDBサービスに接続
    #    dynamodb = boto3.resource("dynamodb")
    # ローカルのDynamoDBに接続
    dynamodb = boto3.resource("dynamodb", endpoint_url="http://127.0.0.1:8000")

    # テーブルを指定
    table = dynamodb.Table("tasks")

    # TODO: ここでDynamoDBのテーブルを検索して、transaction_idに紐づくレコードがあるか確認する
    # テーブルから全てのアイテムを取得
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
    requests.request(method, url, headers=headers, data=data, params=params)

    # TODO: ここでDynamoDBにtransaction_idとレスポンスを保存する


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8088)
