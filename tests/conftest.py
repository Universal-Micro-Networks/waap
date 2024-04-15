import os

import boto3
import pytest
import pytest_asyncio
from httpx import AsyncClient
from waap.concierge.main import app

dynamodb_uri = os.getenv("DYNAMODB_URI")
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_uri)


def override_get_table():
    return dynamodb.Table("test_table")


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    # テスト用に非同期HTTPクライアントを返却
    async with AsyncClient(app=app, base_url="http://localhost") as client:
        yield client
