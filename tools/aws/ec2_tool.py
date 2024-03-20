from typing import Literal, Type

import boto3
from langchain_core.tools import ToolException
from langchain.pydantic_v1 import BaseModel, Field, root_validator
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from lib.ec2_helper import Ec2Helper
from tools.common import get_tool_error_string


class AwsEc2DescribeInstanceOperation(BaseModel):
    operation_type: Literal["describe_instance"] = "describe_instance"
    instance_name: str | None
    ipv4_address: str | None

    @root_validator
    def validate_has_one_identifier(cls, values: dict) -> dict:
        instance_name, ipv4_address = (
            values.get("instance_name"),
            values.get("ipv4_address"),
        )
        if instance_name is None == ipv4_address is None:
            raise ValueError("expected exactly one of instance_name or ipv4_address")

        return values


class AwsEc2ListInstancesOperation(BaseModel):
    operation_type: Literal["list_instances"] = "list_instances"


AwsEc2Operation = AwsEc2DescribeInstanceOperation | AwsEc2ListInstancesOperation


class AwsEc2QueryInput(BaseModel):
    operation: AwsEc2Operation = Field(
        description="should be an EC2 operation", discriminator="operation_type"
    )


class AwsEc2Tool(BaseTool):
    name = "AwsEc2"
    description = "Determine information about AWS EC2 instances"
    args_schema: Type[BaseModel] = AwsEc2QueryInput

    def _run(
        self,
        operation: AwsEc2Operation,
        run_manager: CallbackManagerForToolRun | None = None,
    ):
        try:
            ec2_helper = Ec2Helper(ec2_client=boto3.client("ec2"))
            if isinstance(operation, AwsEc2DescribeInstanceOperation):
                return ec2_helper.describe_instance(
                    name=operation.instance_name, ipv4_address=operation.ipv4_address
                )
            elif isinstance(operation, AwsEc2ListInstancesOperation):
                return ec2_helper.list_instances()

            raise ValueError("Unexpected EC2 operation")
        except Exception as exc:
            raise ToolException(
                get_tool_error_string(tool_operation="querying AWS EC2 information")
            ) from exc

    def _arun(
        self,
        operation: AwsEc2Operation,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ):
        raise NotImplementedError("Does not support async")
