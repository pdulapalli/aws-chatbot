import logging
from mypy_boto3_iam import IAMClient
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)


@dataclass
class PolicyInfo:
    name: str
    description: str


@dataclass
class IamUserInfo:
    username: str
    attached_policies: list[PolicyInfo]
    group_derived_policies: list[PolicyInfo]


class IamHelper:
    def __init__(self, iam_client: IAMClient) -> None:
        self._iam_client = iam_client

    def get_user_permissions(self, username: str):
        attached_policy_arns = self._list_attached_user_policy_arns(username)
        group_derived_policy_arns = [
            group_policy_arn
            for group_name in self._list_group_names_for_user(username=username)
            for group_policy_arn in self._get_group_policy_arns(group_name=group_name)
        ]

        return IamUserInfo(
            username=username,
            attached_policies=self._describe_policies(attached_policy_arns),
            group_derived_policies=self._describe_policies(group_derived_policy_arns),
        )

    def _list_attached_user_policy_arns(self, username: str) -> list[str]:
        try:
            response = self._iam_client.list_attached_user_policies(UserName=username)
            return [policy["PolicyArn"] for policy in response["AttachedPolicies"]]
        except Exception as e:
            _LOGGER.warning(f"Error listing attached policies for user {username}: {e}")
            return []

    def _list_group_names_for_user(self, username: str) -> list[str]:
        try:
            response = self._iam_client.list_groups_for_user(UserName=username)
            return [group["GroupName"] for group in response["Groups"]]
        except Exception as e:
            _LOGGER.warning(f"Error listing groups for user {username}: {e}")
            return []

    def _get_group_policy_arns(self, group_name: str) -> list[str]:
        try:
            response = self._iam_client.list_attached_group_policies(
                GroupName=group_name
            )
            return [policy["PolicyArn"] for policy in response["AttachedPolicies"]]
        except Exception as e:
            _LOGGER.warning(f"Error listing policies for group {group_name}: {e}")
            return []

    def _describe_policies(self, policy_arns: list[str]) -> list[PolicyInfo]:
        return [
            policy
            for policy in map(lambda x: self._describe_policy(x), policy_arns)
            if policy is not None
        ]

    def _describe_policy(self, policy_arn: str) -> PolicyInfo | None:
        try:
            response = self._iam_client.get_policy(PolicyArn=policy_arn)
            return PolicyInfo(
                name=response["Policy"]["PolicyName"],
                description=response["Policy"]["Description"],
            )
        except Exception as e:
            _LOGGER.warning(f"Error describing policy {policy_arn}: {e}")
            return None
