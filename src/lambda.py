import os

import boto3

DOMAIN_NAME = os.getenv("DOMAIN_NAME")
HOSTED_ZONE_ID = os.getenv("HOSTED_ZONE_ID")


def get_dns_tag(event):
    instance_id = event["detail"]["instance-id"]
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    try:
        for tag in instance.tags:
            if tag["Key"] == "dns-name":
                return tag["Value"], instance.public_ip_address
    except TypeError:
        return None, None


def create_record(event, _context):
    dns_prefix, instance_ip = get_dns_tag(event)
    if dns_prefix and instance_ip:
        dns_record = f"{dns_prefix}.{DOMAIN_NAME}"
        boto3.client("route53").change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                "Comment": f"Add {dns_prefix} EC2 record",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": dns_record,
                            "Type": "A",
                            "TTL": 10,
                            "ResourceRecords": [{"Value": instance_ip}],
                        },
                    }
                ],
            },
        )
        print(f"Created record '{dns_record}'")


def delete_record(event, _context):
    dns_prefix, _ = get_dns_tag(event)
    if dns_prefix:
        route53 = boto3.client("route53")
        dns_record = f"{dns_prefix}.{DOMAIN_NAME}"
        current_value = route53.test_dns_answer(
            HostedZoneId=HOSTED_ZONE_ID, RecordName=dns_record, RecordType="A"
        )["RecordData"][0]
        route53.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                "Comment": f"Add {dns_prefix} EC2 record",
                "Changes": [
                    {
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": dns_record,
                            "Type": "A",
                            "TTL": 10,
                            "ResourceRecords": [{"Value": current_value}],
                        },
                    }
                ],
            },
        )
        print(f"Deleted record '{dns_record}'")
