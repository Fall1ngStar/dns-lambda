"""Lambdas to create and delete DNS records for EC2 instances in Route53."""
import os

import boto3


def get_dns_tag(event):
    """Get the dns DNS value for the instance."""
    instance_id = event["detail"]["instance-id"]
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    try:
        for tag in instance.tags:
            if tag["Key"] == "dns-name":
                return tag["Value"], instance.public_ip_address
    except TypeError:
        pass
    return None, None


def create_record(event, _context):
    """Create the record if necessary for the instance in the event."""
    dns_prefix, instance_ip = get_dns_tag(event)
    if dns_prefix and instance_ip:
        domain_name = os.getenv("DOMAIN_NAME")
        dns_record = f"{dns_prefix}.{domain_name}"
        boto3.client("route53").change_resource_record_sets(
            HostedZoneId=os.getenv("HOSTED_ZONE_ID"),
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
    """Delete the record if necessary for the instance in the event."""
    dns_prefix, _ = get_dns_tag(event)
    if dns_prefix:
        route53 = boto3.client("route53")
        domain_name = os.getenv("DOMAIN_NAME")
        hosted_zone_id = os.getenv("HOSTED_ZONE_ID")
        dns_record = f"{dns_prefix}.{domain_name}"
        current_value = route53.test_dns_answer(
            HostedZoneId=hosted_zone_id,
            RecordName=dns_record,
            RecordType="A",
        )["RecordData"][0]
        route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
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
