"""
Module of Cloudinary class and methods
"""

import cloudinary
import cloudinary.uploader

from app.src.conf.config import settings


class CloudinaryService:
    api_name = settings.api_name.replace(" ", "_")
    public_id = f"{api_name}/"

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    def gen_image_name(self, username, filename, album=None):
        """
        Generate public_id of cloudinary`s image.

        :param username: The username of the user.
        :param type: str
        :param filename: The filename of the image to upload.
        :param type: str
        :param album: Optional parametr album name.
        :param type: str
        :return: Public_id for the image storage location in the cloud storage.
        :rtype: str
        """
        index_extension = filename.rfind(".")
        filename = filename[:index_extension]
        public_id = (
            CloudinaryService.public_id + f"/{username}/{album}/{filename}"
            if album
            else CloudinaryService.public_id + f"/{username}/{filename}"
        )
        return public_id

    async def upload_image(self, file, username, filename, album=None):
        """
        Uploads an user's image.

        :param file: The uploaded file of avatar.
        :type file: BinaryIO
        :param username: The username of the user.
        :type username: str
        :param filename: The filename of the image to upload.
        :type filename: str
        :param album: Optional parametr album name.
        :param type: str
        :return: The file upload result
        :rtype: json
        """
        public_id = self.gen_image_name(username, filename, album)
        try:
            result = cloudinary.uploader.upload(
                file,
                public_id=public_id,
                overwrite=True,
            )
            return result
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None

    async def get_image_url(self, result):
        """
        Get image url from cloudinary json response.

        :param result: json response.
        :type result: str
        :return: Url of uploaded image.
        :rtype: str
        """
        try:
            image_url = result.get("secure_url")
            return image_url
        except Exception as e:
            print(f"Error getting image URL: {e}")
            return None

    async def get_public_id_from_url(self, url_image):
        """
        Generate public_id from url cloudinary.

        :param url_image: Get cloudinary url.
        :param type: str
        :return: Public_id for the image storage location in the cloud storage.
        :rtype: str
        """
        l_index = url_image.find(CloudinaryService.api_name)
        r_index = url_image.rfind(".")
        public_id = url_image[l_index:r_index]
        return public_id

    async def delete_image(
            self,
            public_id,
    ):
        """
        Delete an image.

        :param public_id: The image to delete
        :type public_id: URL image
        :return: Result
        :rtype: str
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            print(f"Image deleted: {result}")
        except Exception as e:
            print(f"Error deleting image: {e}")

    async def upload_avatar(
            self,
            file,
            username,
            filename,
    ):
        """
        Uploads an user's avatar.

        :param file: The uploaded file of avatar.
        :type file: File for upload.
        :param username: The username of the user to upload avatar.
        :type username: str
        :param filename: The name of the image file
        :type filename: str
        :return: The URL of uploaded avatar.
        :rtype: str
        """
        public_id = self.gen_image_name(username, filename, album="avatars")
        r = await self.upload_image(file, username, filename, album="avatars")
        avatar_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return avatar_url

    async def image_transformations(self, image_url, transformation):
        """
        Performs various image transformations.

        :param image_url: Get the cloudinary url.
        :param type: str
        :param transformation: Pass the transformation string to the image_transformations function
        :type transformation: str, CloudinaryService variable.
        :return: Image url with the transformation specified
        :rtype: str
        """
        r_index = image_url.rfind("upload/") + 7
        transform_url = f"{image_url[:r_index]}{transformation}{image_url[r_index:]}"
        return transform_url


cloudinary_service = CloudinaryService()
