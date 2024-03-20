from typing import Literal, Optional, Type

import boto3
from langchain_core.tools import ToolException
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from lib.iam_helper import IamHelper
from tools.common import get_tool_error_string


class AwsIamDescribeUserPermissionsOperation(BaseModel):
    operation_type: Literal["describe_user_permissions"] = "describe_user_permissions"
    username: str


AwsIamOperation = AwsIamDescribeUserPermissionsOperation


class AwsIamQueryInput(BaseModel):
    operation: AwsIamOperation = Field(description="should be an IAM operation")


class AwsIamTool(BaseTool):
    name = "AwsIam"
    description = "Determine information about AWS IAM users"
    args_schema: Type[BaseModel] = AwsIamQueryInput

    def _run(
        self,
        operation: AwsIamOperation,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        try:
            iam_helper = IamHelper(iam_client=boto3.client("iam"))
            if isinstance(operation, AwsIamDescribeUserPermissionsOperation):
                return iam_helper.get_user_permissions(username=operation.username)
        except Exception as exc:
            raise ToolException(
                get_tool_error_string(tool_operation="querying AWS IAM information")
            ) from exc

    def _arun(
        self,
        operation: AwsIamOperation,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ):
        raise NotImplementedError("Does not support async")
