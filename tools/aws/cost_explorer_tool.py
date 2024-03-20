from typing import Type

import boto3
from langchain_core.tools import ToolException
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from lib.cost_explorer_helper import CostExplorerHelper
from tools.common import get_tool_error_string


class AwsCostExplorerDescribeCostAndUsageOperation(BaseModel):
    operation_type: str = "describe_cost_and_usage"
    start_date: str
    end_date: str


AwsCostExplorerOperation = AwsCostExplorerDescribeCostAndUsageOperation


class AwsCostExplorerQueryInput(BaseModel):
    operation: AwsCostExplorerOperation = Field(
        description="should be an AWS Cost Explorer operation"
    )


class AwsCostExplorerTool(BaseTool):
    name: str = "AwsCostExplorer"
    description: str = "Determine information about AWS costs"
    args_schema: Type[BaseModel] = AwsCostExplorerQueryInput

    def _run(
        self,
        operation: AwsCostExplorerOperation,
        run_manager: CallbackManagerForToolRun | None = None,
    ):
        try:
            ce_helper = CostExplorerHelper(ce_client=boto3.client("ce"))
            if isinstance(operation, AwsCostExplorerDescribeCostAndUsageOperation):
                return ce_helper.get_usd_costs_for_all_services(
                    start_date=operation.start_date, end_date=operation.end_date
                )

            raise ValueError("Unexpected AWS Cost Explorer operation")
        except Exception as exc:
            raise ToolException(get_tool_error_string(tool_operation='querying AWS Cost Explorer information')) from exc

    def _arun(
        self,
        operation: AwsCostExplorerOperation,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ):
        raise NotImplementedError("Not implemented")
