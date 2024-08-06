"""An AWS Python Pulumi program"""

import json
import pulumi
import pulumi_minio as minio
from pulumi_kubernetes.core.v1 import Secret
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


config = pulumi.Config()

serviceName = config.require("Name")
serviceNamespace = config.require("Namespace")
releaseName = config.require("ReleaseName")
acl = config.require("ACL")

secret_labels = {
  "epinio.io/configuration": "true",
  "epinio.io/configuration-origin": serviceName,
  "epinio.io/configuration-type": "service",
  "app.kubernetes.io/instance": releaseName,
  "app.kubernetes.io/managed-by": "pulumi",
  "app.kubernetes.io/name": "minio-bucket"
}

user = minio.IamUser(f"minio-iam-user", name=f"{serviceNamespace}-{serviceName}", force_destroy=True)

bucket = minio.S3Bucket(f"minio-s3-bucket", bucket=f"{serviceNamespace}-{releaseName}")

pulumi.export("bucket_arn",bucket.arn)

def iam_user_policy(bucket_arn, acl):
    match acl:
        case "public":
          return pulumi.Output.all(bucket_arn).apply(
            lambda args: json.dumps(
              {
                "Version":"2012-10-17",
                "Statement": [
                  {
                    "Sid":"ListAllBucket",
                    "Effect": "Allow",
                    "Action": [
                      "s3:Put*",
                      "s3:Get*",
                      "s3:List*",
                    ],
                    "Principal":"*",
                    "Resource": [
                      f"{args[0]}",
                      f"{args[0]}/*"
                      ]
                  }
                ]
              }
            )
          )
        case "readonly":
          return pulumi.Output.all(bucket_arn).apply(
            lambda args: json.dumps(
              {
                "Version":"2012-10-17",
                "Statement": [
                  {
                    "Sid":"ListAllBucket",
                    "Effect": "Allow",
                    "Action": [
                      "s3:ListBucket",
                      "s3:GetObject",
                      "s3:GetObjectVersion",
                    ],
                    "Principal":"*",
                    "Resource": [
                      f"{args[0]}",
                      f"{args[0]}/*"
                      ]
                  }
                ]
              }
            )
          )
        case "private":
          return pulumi.Output.all(bucket_arn).apply(
            lambda args: json.dumps(
              {
                "Version":"2012-10-17",
                "Statement": [
                  {
                    "Sid":"ListAllBucket",
                    "Effect": "Allow",
                    "Action": [
                      "s3:ListBucket",
                      "s3:PutObject",
                      "s3:GetObject",
                      "s3:DeleteObject"
                    ],
                    # TODO: set the right principal here
                    "Principal":"*",
                    "Resource": [
                      f"{args[0]}",
                      f"{args[0]}/*"
                      ]
                  }
                ]
              }
            )
          )


iam_policy = minio.IamPolicy("minio-iam-policy",
                             name=f"{serviceNamespace}-{serviceName}",
                             policy=bucket.arn.apply(iam_user_policy)
                            )

iam_user_policy_attachment = minio.IamUserPolicyAttachment("minio-user-policy",
                                                            user_name=user.name,
                                                            policy_name=iam_policy.name
                                                           )

service_account = minio.IamServiceAccount("service-account",
                                           target_user=user.name,
                                           policy=bucket.arn.apply(iam_user_policy)
                                          )

service_account_secret = Secret("service-account-secret",
                                metadata=ObjectMetaArgs(
                                  name=f"{releaseName}-minio",
                                  namespace=serviceNamespace,
                                  labels=secret_labels),
                                string_data = {
                                  "ACCESS_KEY": service_account.access_key,
                                  "SECRET_KEY": service_account.secret_key
                                })

pulumi.export("secret_name",service_account_secret.metadata["name"])
