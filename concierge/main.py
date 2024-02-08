import uuid

import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request

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


@app.get("/task/{transaction_id}")
async def check_task(transaction_id: str):
    # TODO: ここでDynamoDBのテーブルを検索して、transaction_idに紐づくレコードがあるか確認する
    # なければ、404を返す
    # あれば、そのレコードを返す
    return {"transaction_id": transaction_id}


def _send_api_request(
    method: str, url: str, headers: dict, data: dict, params: dict, transaction_id: str
) -> None:
    requests.request(method, url, headers=headers, data=data, params=params)

    # TODO: ここでDynamoDBにtransaction_idとレスポンスを保存する


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8088)
