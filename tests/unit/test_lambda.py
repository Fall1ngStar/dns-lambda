"""Unit tests for the lambda module."""

import os
from functools import wraps
from unittest.mock import patch, DEFAULT

from src import dns_lambda


def clean_env(func):
    """Empty the environment for the decorated function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wraps the decorated function."""
        backup_env = dict(os.environ)
        os.environ = {}
        result = func(*args, **kwargs)
        os.environ = backup_env
        return result

    return wrapper


def test_get_dns_tag():
    """Test for the get_dns_tag function."""
    event = {"detail": {"instance-id": "i-xxx"}}
    with patch("src.dns_lambda.boto3") as boto3:
        instance = boto3.resource().Instance()
        instance.tags = [{"Key": "dns-name", "Value": "my-ec2"}]
        instance.public_ip_address = "1.1.1.1"
        result = dns_lambda.get_dns_tag(event)
        assert result == ("my-ec2", "1.1.1.1")

        instance.tags = []
        result = dns_lambda.get_dns_tag(event)
        assert result == (None, None)


@clean_env
def test_create_record():
    """Test for the create_record function."""
    with patch.multiple(
        "src.dns_lambda",
        get_dns_tag=DEFAULT,
        boto3=DEFAULT,
    ) as mocks:
        mocks["get_dns_tag"].return_value = ("my-ec2", "1.1.1.1")
        dns_lambda.create_record({}, None)
        mocks["boto3"].client().change_resource_record_sets.assert_called_with(
            HostedZoneId=None,
            ChangeBatch={
                "Comment": "Add my-ec2 EC2 record",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": "my-ec2.None",
                            "Type": "A",
                            "TTL": 10,
                            "ResourceRecords": [{"Value": "1.1.1.1"}],
                        },
                    }
                ],
            },
        )


@clean_env
def test_delete_record():
    """Test for the delete_record funtion."""
    with patch.multiple(
        "src.dns_lambda",
        get_dns_tag=DEFAULT,
        boto3=DEFAULT,
    ) as mocks:
        mocks["get_dns_tag"].return_value = ("my-ec2", "1.1.1.1")
        mocks["boto3"].client().test_dns_answer.return_value = {
            "RecordData": ["1.1.1.1"]
        }
        dns_lambda.delete_record({}, None)
        mocks["boto3"].client().test_dns_answer.assert_called_with(
            HostedZoneId=None, RecordName="my-ec2.None", RecordType="A"
        )
        mocks["boto3"].client().change_resource_record_sets.assert_called_with(
            HostedZoneId=None,
            ChangeBatch={
                "Comment": "Add my-ec2 EC2 record",
                "Changes": [
                    {
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": "my-ec2.None",
                            "Type": "A",
                            "TTL": 10,
                            "ResourceRecords": [{"Value": "1.1.1.1"}],
                        },
                    }
                ],
            },
        )
