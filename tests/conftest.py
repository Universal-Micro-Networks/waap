import os

import boto3
import pytest

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
