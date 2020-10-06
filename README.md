# dns-lambda

A Lambda that creates DNS record on EC2 startup and shutdown.

## Explaination

Having your IP for you EC2 instance change every time your stop and restart it can be annoying. 
And adding an Elastic IP can end up costing a lot of money if you have multiple instances you want a fixed access to.

This simple lambda create / delete automatically a record in Route53 for tagged instances so you can access your instance with a domain name.

Example:

You have the domain `example.com`, and you want your EC2 to points to `my-ec2.example.com`.
You tag your instance with the tag `dns-name` and the value `my-ec2`, you start your instance and voila !
Your instance is now accessible from `my-ec2.example.com`.

## Requirements

In your AWS account:
 
 - A Route53 Hosted Zone
 - A S3 bucket to store serverless deployment package
 
On your computer:

 - NodeJS & Python 3.8 installed
 - Serverless & Pipenv installed
 
## Preparation

You must fill the `config/env_variables.sh` file before deploying.

It contains the following variables:

- `DEPLOYMENT_BUCKET`: Name of the S3 bucket where the serverless artifact will be deployed.
- `DOMAIN_NAME`: Name of the DNS suffix that will be used (Can be a subdomain of your hosted zone).
- `HOSTED_ZONE_ID`: ID of the hosted zone where the records will be stored.
 
## Installation

- Complete the `config/env_variables.sh` file (see documentation above)
- Load the variables in your environment: `source config/env_variables.sh`
- Install the serverless plugins: `npm install`
- Deploy the project: `serverless deploy`