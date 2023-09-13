import boto3


class S3Client:
    s3 = boto3.client('s3')

    @classmethod
    def list_buckets(cls):
        return cls.s3.list_buckets()

    @classmethod
    def list_objects_v2(cls, Bucket):
        return cls.s3.list_objects_v2(Bucket=Bucket)

    @classmethod
    def upload_fileobj(cls, file, Bucket, Key):
        cls.s3.upload_fileobj(file, Bucket=Bucket, Key=Key)

    @classmethod
    def download_file(cls, Bucket, Key, Filename):
        cls.s3.download_file(Bucket=Bucket, Key=Key, Filename=Filename)

    @classmethod
    def generate_presigned_url(cls, Params, ExpiresIn):
        return cls.s3.generate_presigned_url(
            'get_object',
            Params=Params,
            ExpiresIn=ExpiresIn
        )

    @classmethod
    def delete_object(cls, Bucket, Key):
        cls.s3.delete_object(Bucket=Bucket, Key=Key)

    @classmethod
    def delete_objects(cls, Bucket, Delete):
        cls.s3.delete_objects(Bucket=Bucket, Delete=Delete)

    @classmethod
    def get_bucket_versioning(cls, Bucket):
        return cls.s3.get_bucket_versioning(Bucket=Bucket)

    @classmethod
    def create_bucket(cls, Bucket):
        return cls.s3.create_bucket(Bucket=Bucket)

    @classmethod
    def get_bucket_policy(cls, Bucket):
        return cls.s3.get_bucket_policy(Bucket=Bucket)

    @classmethod
    def put_bucket_policy(cls, Bucket, Policy):
        cls.s3.put_bucket_policy(Bucket=Bucket, Policy=Policy)

    @classmethod
    def put_bucket_website(cls, Bucket):
        index_doc = 'index.html'
        error_doc = 'error.html'

        cls.s3.put_bucket_website(
            Bucket=Bucket,
            WebsiteConfiguration={
                'ErrorDocument': {'Key': error_doc},
                'IndexDocument': {'Suffix': index_doc},
            }
        )

    @classmethod
    def delete_bucket(cls, Bucket):
        cls.s3.delete_bucket(Bucket=Bucket)
