import os

from src.clipManager import ClipperError

from b2sdk.v1 import InMemoryAccountInfo, B2Api


class BtnSession:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if kwargs.get("new_instance"):
            return object.__new__(cls)
        elif not cls.__instance:
            cls.__instance = object.__new__(cls)
            return cls.__instance
        else:
            return cls.__instance

    def __init__(self):
        key_id = os.environ["B2_KEY_ID"]
        app_key = os.environ["B2_APP_KEY"]
        if not (key_id and app_key):
            raise ClipperError("Credential for B2 is needed, "
                               "set B2_KEY_ID and B2_APP_KEY "
                               "as environment variable or pass in as arguments")
        info = InMemoryAccountInfo()
        self._api = B2Api(info)
        self._api.authorize_account("production", key_id, app_key)
        self._bucket = self._api.get_bucket_by_name("RushiaBtn")
        self._file_link_template = "https://f002.backblazeb2.com/file/RushiaBtn/{}"

    def upload(self, clip):
        return self._bucket.upload_local_file(local_file=clip.normalized_path, file_name=clip.full_name)

