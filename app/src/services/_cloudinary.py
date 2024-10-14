"""
Module of Cloudinary class and methods
"""


import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, File, status

from app.src.conf.config import settings


class CloudinaryService:
    def __init__(self) -> None:
        self.cloudinary_api_key = settings.cloudinary_api_key
        self.cloudinary_api_secret = settings.cloudinary_api_secret
        self.cloudinary_cloud_name = settings.cloudinary_cloud_name
        self.api_name = settings.api_name.replace(" ", "_")
        public_id = f"{self.api_name}/"
        self.configure_cloudinary()

    def configure_cloudinary(self):
        cloudinary.config(
            cloud_name=self.cloudinary_cloud_name,
            api_key=self.cloudinary_api_key,
            api_secret=self.cloudinary_api_secret,
            secure=True,
        )

    def upload_image(self, file, public_id):
        response = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return response["secure_url"]

    async def edit_image(self):
        pass

    async def delete_image(self):
        pass

    async def upload_avatar(self):
        pass

        # await upload_image(...)
cloudinary_service = CloudinaryService()
"""
 @staticmethod
    def generate_name_avatar(email: str):
        name = hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]
        return f"avatars/{name}"
    @staticmethod
    def upload(file, public_id: str):
        r = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return r
    @staticmethod
    def get_url_for_avatar(public_id, r):
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
"""
async def upload_avatar(
    file: UploadFile,
    username: str,
):
    """
    Uploads an user's avatar.
    :param file: The uploaded file of avatar.
    :type file: UploadFile
    :param username: The username of the user to upload avatar.
    :type username: User
    :return: The URL of uploaded avatar.
    :rtype: str
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    api_name = settings.api_name.replace(" ", "_")
    try:
        r = cloudinary.uploader.upload(
            file.file,
            public_id=f"{api_name}/{username}",
            overwrite=True,
        )
        src_url = cloudinary.CloudinaryImage(f"{api_name}/{username}").build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload image error: {str(error_message)}",
        )

if __name__ == "__main__":
    result = cloudinary_service.upload_image("/Users/milvus/Downloads/photo_2024-08-20 13.13.28.jpeg")
    print(result)