import json
import logging
from mypy_boto3_s3 import S3Client
import mimetypes
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

SMALL_FILE_SIZE_THRESHOLD_MB = 5
BYTES_PER_MB = 1024**2


def is_likely_text_file(file_name: str, content_type: str | None):
    if content_type:
        return content_type.startswith("text/")
    else:
        # Use file extension guessing, but this is less reliable.
        _, extension = mimetypes.guess_type(file_name)
        return extension in [".txt", ".csv", ".json", ".xml", ".html", ".log", ".ini"]


def is_small_file(size):
    return size <= SMALL_FILE_SIZE_THRESHOLD_MB * BYTES_PER_MB


@dataclass
class S3BucketObject:
    object_key: str
    size_bytes: int
    is_text_file: bool
    contents: str | None


class S3Helper:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def list_buckets(self) -> list:
        result = self._s3_client.list_buckets()
        if result.get("Buckets"):
            return result["Buckets"]
        else:
            return []

    def count_buckets(self, exposed_to_public: bool) -> int:
        buckets = self.list_buckets()
        if exposed_to_public is None:
            return len(buckets)

        tally = 0
        for bucket in buckets:
            bucket_name = bucket["Name"]
            is_public_facing = self._is_bucket_public(bucket_name=bucket_name)
            if exposed_to_public == is_public_facing:
                tally += 1

        return tally

    def describe_bucket_contents(self, bucket_name: str) -> list[S3BucketObject]:
        response = self._s3_client.list_objects_v2(Bucket=bucket_name)
        if response["KeyCount"] == 0:
            return []

        return [
            self._get_object_info(bucket_name=bucket_name, object_key=obj["Key"])
            for obj in response["Contents"]
        ]

    def _get_object_info(self, bucket_name: str, object_key: str) -> S3BucketObject:
        response = self._s3_client.head_object(Bucket=bucket_name, Key=object_key)

        file_size = response["ContentLength"]
        content_type = response["ContentType"]
        is_text_file = is_likely_text_file(
            file_name=object_key, content_type=content_type
        )

        object_info = S3BucketObject(
            object_key=object_key,
            size_bytes=file_size,
            is_text_file=is_text_file,
            contents=None,
        )

        if not is_small_file(file_size):
            _LOGGER.info(f"Skipping '{object_key}': File size exceeds the threshold.")
            return object_info

        if not is_text_file:
            _LOGGER.info(f"Skipping '{object_key}': Not a text file.")
            return object_info

        file_obj = self._s3_client.get_object(Bucket=bucket_name, Key=object_key)
        object_info.contents = file_obj["Body"].read().decode("utf-8")

        return object_info

    def _is_bucket_public(self, bucket_name: str) -> bool:
        # Check Bucket Policy for public access statements
        try:
            policy = self._s3_client.get_bucket_policy(Bucket=bucket_name)
            policy_statement = policy["Policy"]
            policy_json = json.loads(policy_statement)

            for statement in policy_json["Statement"]:
                if statement["Effect"] == "Allow" and (
                    statement["Principal"] == "*"
                    or statement["Principal"]["AWS"] == "*"
                ):
                    return True
        except self._s3_client.exceptions.from_code("NoSuchBucketPolicy"):
            _LOGGER.info(f"No Bucket Policy for bucket {bucket_name}")

        # Check Bucket ACL as well
        try:
            acl = self._s3_client.get_bucket_acl(Bucket=bucket_name)
            for grant in acl["Grants"]:
                grantee = grant.get("Grantee", {})
                if grantee.get("Type") == "Group" and grantee.get("URI") in [
                    "http://acs.amazonaws.com/groups/global/AllUsers",
                    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
                ]:
                    return True
        except self._s3_client.exceptions.from_code("AccessControlListNotSupported"):
            _LOGGER.info(f"No Bucket ACL for bucket {bucket_name}")

        return False
