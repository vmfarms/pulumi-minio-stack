"""An AWS Python Pulumi program"""

import pulumi
import pulumi_minio as minio
from pulumi_kubernetes.core.v1 import Secret
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

user = minio.IamUser("minio-test-user",
                     name="minio-test-user",
                     force_destroy=True)

bucket = minio.S3Bucket("minio-test-bucket",
                        bucket="minio-test-bucket")

iam_policy = minio.IamPolicy("minio-test-policy",
                             name="minio-test-policy",
                             policy="""{
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
                                  "Principal":"*",
                                  "Resource": [
                                    "{}",
                                    "{}/*"
                                    ]"
                                }
                              ]
}""".format(bucket.arn, bucket.arn))

iam_user_policy_attachment = minio.IamUserPolicyAttachment("minio-test-user-policy",
                                                           user_name=user.name,
                                                           policy_name=iam_policy.name)

service_account = minio.IamServiceAccount("service-account",
                                          target_user=user.name)

service_account_secret = Secret("service-account-secret",
                                metadata=ObjectMetaArgs(
                                  name="pulumi-test-secret",
                                  namespace="default"),
                                string_data = {
                                  "ACCESS_KEY": service_account.access_key,
                                  "SECRET_KEY": service_account.secret_key
                                }
                                )