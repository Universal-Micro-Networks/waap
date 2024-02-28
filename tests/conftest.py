import os

import boto3
import pytest

dynamodb_uri = os.getenv("DYNAMODB_URI_TEST")
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_uri)

s3 = boto3.resource(
    "s3",
    endpoint_url=os.getenv("MINIO_URI"),  # MinIOサーバーのエンドポイントURL
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),  # MinIOのアクセスキー
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),  # MinIOのシークレットキー
    region_name="ap-northeast-1",
)
# バケット名を指定してバケットを取得
bucket = s3.Bucket("waap")


def override_get_bucket():
    return bucket


def override_get_table():
    return dynamodb.Table("test_table")
