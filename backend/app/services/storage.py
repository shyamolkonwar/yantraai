import os
import requests
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings


class StorageService:
    def __init__(self):
        # For testing: Force local storage to avoid Supabase storage issues
        self.use_supabase = False
        self.use_s3 = False

        # Use local storage for testing
        self.local_storage_path = settings.LOCAL_STORAGE_PATH
        os.makedirs(self.local_storage_path, exist_ok=True)
        print("Using local storage (testing mode)")

    def upload_file_obj(self, file_obj, key: str):
        """Upload file object to storage"""
        if self.use_supabase:
            try:
                # Create storage path with bucket
                storage_path = f"{self.bucket_name}/{key}"
                url = f"{self.storage_url}/object/{storage_path}"

                response = requests.post(
                    url,
                    files={'file': (key, file_obj)},
                    headers=self.headers
                )

                if response.status_code in [200, 201]:
                    return storage_path
                else:
                    print(f"Supabase upload failed: {response.text}")
                    # Try to create bucket first
                    self._create_bucket_if_not_exists()
                    # Retry upload
                    response = requests.post(
                        url,
                        files={'file': (key, file_obj)},
                        headers=self.headers
                    )
                    if response.status_code in [200, 201]:
                        return storage_path
                    else:
                        raise Exception(f"Supabase upload failed: {response.text}")

            except Exception as e:
                print(f"Supabase upload failed: {e}")
                # Fallback to S3
                self.use_supabase = False

        if self.use_s3:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_obj
                )
                return key
            except Exception as e:
                print(f"S3 upload failed: {e}")
                # Fallback to local storage
                self.use_s3 = False

        # Local storage fallback
        file_path = self.get_file_path(key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(file_obj)
        return key

    def _create_bucket_if_not_exists(self):
        """Create Supabase bucket if it doesn't exist"""
        try:
            url = f"{self.storage_url}/bucket/{self.bucket_name}"
            response = requests.post(
                url,
                json={
                    "name": self.bucket_name,
                    "public": False,
                    "allowed_mime_types": ["application/pdf", "image/*"],
                    "file_size_limit": 52428800  # 50MB
                },
                headers=self.headers
            )
            if response.status_code not in [200, 201]:
                print(f"Failed to create bucket: {response.text}")
        except Exception as e:
            print(f"Error creating bucket: {e}")

    def upload_file(self, file_path: str, key: str):
        """Upload local file to storage"""
        if self.use_supabase:
            try:
                storage_path = f"{self.bucket_name}/{key}"
                url = f"{self.storage_url}/object/{storage_path}"

                with open(file_path, 'rb') as f:
                    response = requests.post(
                        url,
                        files={'file': (key, f)},
                        headers=self.headers
                    )

                if response.status_code in [200, 201]:
                    return storage_path
                else:
                    raise Exception(f"Supabase upload failed: {response.text}")

            except Exception as e:
                print(f"Supabase upload failed: {e}")
                self.use_supabase = False

        if self.use_s3:
            try:
                self.s3_client.upload_file(
                    file_path,
                    self.bucket_name,
                    key
                )
                return key
            except Exception as e:
                print(f"S3 upload failed: {e}")
                self.use_s3 = False

        # Local storage fallback
        dest_path = self.get_file_path(key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        os.rename(file_path, dest_path)
        return key

    def get_file_path(self, key: str) -> str:
        """Get local file path for key"""
        if self.use_supabase:
            # Generate public URL for Supabase
            try:
                if self.bucket_name in key:
                    storage_path = key
                else:
                    storage_path = f"{self.bucket_name}/{key}"
                return f"{self.storage_url}/object/public/{storage_path}"
            except Exception as e:
                print(f"Failed to generate Supabase URL: {e}")
                # Fallback to local path
                return os.path.join(self.local_storage_path, key)
        elif self.use_s3:
            # Generate signed URL
            try:
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=3600
                )
            except Exception as e:
                print(f"Failed to generate signed URL: {e}")
                return os.path.join(self.local_storage_path, key)
        else:
            return os.path.join(self.local_storage_path, key)

    def download_file(self, key: str, local_path: str):
        """Download file from storage"""
        if self.use_supabase:
            try:
                # Determine storage path
                if self.bucket_name in key:
                    storage_path = key
                else:
                    storage_path = f"{self.bucket_name}/{key}"

                url = f"{self.storage_url}/object/{storage_path}"
                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    return local_path
                else:
                    raise Exception(f"Supabase download failed: {response.status_code}")

            except Exception as e:
                print(f"Supabase download failed: {e}")
                self.use_supabase = False

        if self.use_s3:
            try:
                self.s3_client.download_file(
                    self.bucket_name,
                    key,
                    local_path
                )
                return local_path
            except Exception as e:
                print(f"S3 download failed: {e}")
                self.use_s3 = False

        # Local storage fallback
        source_path = self.get_file_path(key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if os.path.exists(source_path):
            if source_path != local_path:
                import shutil
                shutil.copy2(source_path, local_path)
            return local_path
        else:
            raise FileNotFoundError(f"File not found: {key}")

    def delete_file(self, key: str):
        """Delete file from storage"""
        if self.use_supabase:
            try:
                # Determine storage path
                if self.bucket_name in key:
                    storage_path = key
                else:
                    storage_path = f"{self.bucket_name}/{key}"

                url = f"{self.storage_url}/object/{storage_path}"
                response = requests.delete(url, headers=self.headers)

                if response.status_code not in [200, 204]:
                    print(f"Supabase delete failed: {response.text}")
                return

            except Exception as e:
                print(f"Supabase delete failed: {e}")
                self.use_supabase = False

        if self.use_s3:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                return
            except Exception as e:
                print(f"S3 delete failed: {e}")
                self.use_s3 = False

        # Local storage fallback
        file_path = self.get_file_path(key)
        if os.path.exists(file_path):
            os.remove(file_path)

    def file_exists(self, key: str) -> bool:
        """Check if file exists in storage"""
        if self.use_supabase:
            try:
                # Determine storage path
                if self.bucket_name in key:
                    storage_path = key
                else:
                    storage_path = f"{self.bucket_name}/{key}"

                url = f"{self.storage_url}/object/{storage_path}"
                response = requests.head(url, headers=self.headers)
                return response.status_code == 200
            except:
                return False
        elif self.use_s3:
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                return True
            except:
                return False
        else:
            return os.path.exists(self.get_file_path(key))
