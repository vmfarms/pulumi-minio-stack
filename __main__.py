"""An AWS Python Pulumi program"""

import pulumi

import pulumi_minio as minio

user = minio.IamUser("python-user")