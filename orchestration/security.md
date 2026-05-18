# Security and Access Control Architecture

This document outlines the comprehensive security measures and IAM policies implemented for both human users (team members) and machine identities (AWS services) within our data pipeline.

## Human Access Management (Team Identities)
To enforce the Principle of Least Privilege among team members, we divided IAM User permissions based on project roles:

### Orchestration Engineer (Role 4)
Requires full access to configure base infrastructure, IAM policies, and orchestrate the final pipeline.
**Policy Attached:** `AdministratorAccess`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}
```
### Data, Quality, and Analytics Engineers (Roles 1, 2 & 3)
Require access to build and test AWS Glue Jobs and Athena queries, but must be restricted from modifying the organization's security boundaries (IAM) or accessing billing.

**Base Policy Attached:** PowerUserAccess (Allows development, denies iam:*, organizations:*, account:*).

```json

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "NotAction": [
                "iam:*",
                "organizations:*",
                "account:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "account:GetAccountInformation",
                "account:GetGovCloudAccountInformation",
                "account:GetPrimaryEmail",
                "account:ListRegions",
                "iam:CreateServiceLinkedRole",
                "iam:DeleteServiceLinkedRole",
                "iam:ListRoles",
                "organizations:DescribeEffectivePolicy",
                "organizations:DescribeOrganization"
            ],
            "Resource": "*"
        }
    ]
}
```
**Custom Policy Attached (PermisoPassRoleLabRole):** Since PowerUserAccess denies IAM actions, developers cannot assign execution roles to their Glue Jobs. We explicitly granted them the iam:PassRole permission restricted only to the LabRole to ensure they can deploy jobs without escalating privileges.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PermitirPasarLabRole",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::891943683988:role/LabRole"
        }
    ]
}
```
### Service Access Management (Machine Identities)
Due to the constraints of the AWS Academy environment, we utilized the pre-provisioned LabRole for all compute services.

**AWS Glue Jobs & Crawlers:** Assigned the LabRole to execute ETL scripts, read/write to S3, and update the Data Catalog.

**AWS Step Functions:** Assigned the LabRole to orchestrate the workflow.

### Trust Relationships (Cross-Service Execution)
To achieve full automation without manual intervention, Step Functions needed permission to trigger Glue Jobs. We modified the LabRole Trust Relationship policy to allow the Step Functions service principal (states.amazonaws.com) to assume the role safely:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": [
      "glue.amazonaws.com",
      "states.amazonaws.com"
    ]
  },
  "Action": "sts:AssumeRole"
}
```

### Data Protection (Amazon S3)
**Block Public Access:** The data lake bucket (data-source-52143) has "Block all public access" enabled at the account level to prevent unauthorized data leaks.

**Bucket Policy (Encryption in Transit):** We implemented a strict Bucket Policy on data-source-52143 using the aws:SecureTransport condition to explicitly deny any s3:* actions that do not use HTTPS. This guarantees data encryption in transit.

**Credential Management:** No AWS access keys or secret keys are hardcoded in the scripts. Boto3 automatically inherits temporary credentials from the execution role (LabRole). The .gitignore file explicitly blocks .aws/credentials, *.parquet, *.json, and .env files from being committed.