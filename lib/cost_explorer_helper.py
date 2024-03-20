from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from mypy_boto3_ce import CostExplorerClient


@dataclass
class CostInfo:
    daily_costs_by_service: list[tuple[tuple[date, date], dict[str, Decimal]]]

    total_cost_by_service: dict[str, Decimal]


class TimeGranularity(Enum):
    DAILY = "DAILY"


class CostExplorerHelper:
    def __init__(self, ce_client: CostExplorerClient) -> None:
        self._ce_client = ce_client

    def get_usd_costs_for_all_services(
        self, start_date: str, end_date: str
    ) -> CostInfo:
        cost_and_usage_items = self._get_cost_and_usage_for_all_services(
            start_date=start_date, end_date=end_date, granularity=TimeGranularity.DAILY
        )

        daily_costs_by_service = []
        total_cost_by_service = {}
        for daily_cost in cost_and_usage_items:
            time_period_start, time_period_end = (
                datetime.strptime(daily_cost["TimePeriod"]["Start"], "%Y-%m-%d").date(),
                datetime.strptime(daily_cost["TimePeriod"]["End"], "%Y-%m-%d").date(),
            )

            daily_cost_by_service = {}
            for daily_service_cost_item in daily_cost["Groups"]:
                grouping_keys = daily_service_cost_item.get("Keys", [])
                if len(grouping_keys) == 0:
                    continue

                metrics = daily_service_cost_item.get(
                    "Metrics", {"BlendedCost": {"Amount": 0, "Unit": "USD"}}
                )

                # NOTE: Currently only support USD calculations since this
                # doesn't have historical exchange rates for converting to/from
                # currencies.
                if metrics["BlendedCost"]["Unit"] != "USD":
                    continue

                service = grouping_keys[0]
                cost_amount = Decimal(metrics["BlendedCost"]["Amount"])

                daily_cost_by_service[service] = cost_amount
                total_cost_by_service[service] = (
                    cost_amount + total_cost_by_service.get(service, Decimal("0"))
                )

            daily_costs_by_service.append(
                ((time_period_start, time_period_end), daily_cost_by_service)
            )

        return CostInfo(
            daily_costs_by_service=daily_costs_by_service,
            total_cost_by_service=total_cost_by_service,
        )

    def _get_cost_and_usage_for_all_services(
        self, start_date: str, end_date: str, granularity: TimeGranularity
    ) -> list[dict]:
        response = self._ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity.value,
            Metrics=["BLENDED_COST"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        return response["ResultsByTime"]
