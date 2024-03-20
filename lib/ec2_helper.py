import logging
from mypy_boto3_ec2 import EC2Client
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)


@dataclass
class Ec2InstanceBaseInfo:
    name: str
    ipv4_address: str


@dataclass
class Ec2InstanceInfo(Ec2InstanceBaseInfo):
    id: str
    instance_type: str
    image_id: str


class Ec2Helper:
    def __init__(self, ec2_client: EC2Client) -> None:
        self._ec2_client = ec2_client

    def describe_instance(
        self, name: str | None, ipv4_address: str | None
    ) -> Ec2InstanceInfo | None:
        if name is None and ipv4_address is None:
            return None

        filters = []
        if ipv4_address is not None:
            filters.append({"Name": "ip-address", "Values": [ipv4_address]})
        elif name is not None:
            filters.append({"Name": "tag:Name", "Values": [name]})

        result = self._ec2_client.describe_instances(Filters=filters)
        reservations = result.get("Reservations", [])
        if len(reservations) == 0:
            return None

        # Assuming only one matching instance
        instance = reservations[0]["Instances"][0]
        tags_dictionary = {tag["Key"]: tag["Value"] for tag in instance["Tags"]}
        return Ec2InstanceInfo(
            id=instance["InstanceId"],
            name=tags_dictionary["Name"],
            instance_type=instance["InstanceType"],
            image_id=instance["ImageId"],
            ipv4_address=instance["PublicIpAddress"],
        )

    def list_instances(self) -> list[Ec2InstanceBaseInfo]:
        result = self._ec2_client.describe_instances()
        reservations = result.get("Reservations", [])

        instances_info = []
        for reservation in reservations:
            for instance in reservation["Instances"]:
                tags_dictionary = {tag["Key"]: tag["Value"] for tag in instance["Tags"]}
                instances_info.append(
                    Ec2InstanceBaseInfo(
                        name=tags_dictionary["Name"],
                        ipv4_address=instance["PublicIpAddress"],
                    )
                )

        return instances_info
