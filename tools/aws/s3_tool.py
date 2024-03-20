from typing import Literal, Optional, Type

import boto3
from langchain_core.tools import ToolException
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from lib.s3_helper import S3Helper
from tools.common import get_tool_error_string


class AwsS3ListBucketsOperation(BaseModel):
    operation_type: Literal["list"] = "list"
    bucket_names: list[str] | None


class AwsS3CountBucketsOperation(BaseModel):
    operation_type: Literal["count"] = "count"
    bucket_names: list[str] | None
    exposed_to_public: bool | None


class AwsS3DescribeBucketContentsOperation(BaseModel):
    operation_type: Literal["describe_data_contents"] = "describe_data_contents"
    bucket_name: str


AwsS3Operation = (
    AwsS3ListBucketsOperation
    | AwsS3CountBucketsOperation
    | AwsS3DescribeBucketContentsOperation
)


class AwsS3QueryInput(BaseModel):
    operation: AwsS3Operation = Field(
        description="should be an S3 operation", discriminator="operation_type"
    )


class AwsS3Tool(BaseTool):
    name = "AwsS3"
    description = "Determine information about AWS S3 buckets"
    args_schema: Type[BaseModel] = AwsS3QueryInput

    def _run(
        self,
        operation: AwsS3Operation,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        try:
            s3_helper = S3Helper(s3_client=boto3.client("s3"))
            if isinstance(operation, AwsS3ListBucketsOperation):
                return s3_helper.list_buckets()
            elif isinstance(operation, AwsS3CountBucketsOperation):
                return s3_helper.count_buckets(
                    exposed_to_public=operation.exposed_to_public
                )
            elif isinstance(operation, AwsS3DescribeBucketContentsOperation):
                return s3_helper.describe_bucket_contents(
                    bucket_name=operation.bucket_name
                )
        except Exception as exc:
            raise ToolException(
                get_tool_error_string(tool_operation="querying AWS S3 information")
            ) from exc

    def _arun(
        self,
        operation: AwsS3Operation,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        raise NotImplementedError("Does not support async")
