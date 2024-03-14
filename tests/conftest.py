import os

import boto3
import pytest
import pytest_asyncio
from concierge.main import app
from httpx import AsyncClient

dynamodb_uri = os.getenv("DYNAMODB_URI_TEST")

session = boto3.session.Session(
    aws_access_key_id="DUMMY_ACCESS_KEY",
    aws_secret_access_key="DUMMY_SECRET_KEY",
    region_name="ap-northeast-1",
)

dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_uri)

# def override_get_bucket():
#    return bucket


def override_get_table():
    return dynamodb.Table("test_table")


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    # テスト用に非同期HTTPクライアントを返却
    async with AsyncClient(app=app, base_url="http://localhost") as client:
        yield client
