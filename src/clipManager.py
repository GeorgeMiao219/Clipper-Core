import os
import os.path as pt
import logging
import traceback
from typing import Optional

from src.clip import *

import requests
from b2sdk.v1 import *


lg = logging.getLogger("Clipper")


class ClipManager:
    _cf_endpoint = "https://category.rushia.moe"

    def __init__(self):
        lg.info("Start initializing ClipSync")
        self._cat = []
        self.clips = {}
        self._load_init()
        self.endpoint_token = os.environ.get("CLIPPER_TOKEN")
        if not self.endpoint_token or not self._test_token():
            raise ClipperError("Invalid Clipper token")
        """
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
        """
        self.storage_path = "storage"
        self.normalized_path = "normalized"
        if not pt.exists(self.storage_path):
            os.mkdir(self.storage_path)
        if not pt.exists(self.normalized_path):
            os.mkdir(self.normalized_path)
        lg.info("Finished initializing ClipSync")

    def new_clip(self, url, start, end) -> 'Clip':
        try:
            clip = Clip(url, start, end)
            self.clips[clip.uid] = clip
            return clip
        except ClipperError as e:
            lg.error(traceback.format_exc(e))

    def new_cat(self, catId, name_dict):
        if self._exist_cat(catId):
            raise ClipperError(f"{catId} already exists:\n{self.get_cat(catId)['name']}")
        if not isinstance(name_dict, dict):
            raise TypeError(
                "Expect dict contains name info like:\n"
                "    {'en': 'foo', 'zh': '歪比巴伯'}\n"
                "Got " + str(type(name_dict))
            )
        self._cat.append({
            'clips': [],
            'catId': catId,
            'name': name_dict
        })
        self.sync_cat()

    def set_cat(self, uid, catId):
        if not self._exist_cat(catId):
            raise ClipperError(f"Cannot find {catId}")
        clip = self.get_clip(uid, True)
        clip.cat = self.get_cat(catId)
        self.sync_cat()

    def get_cat(self, catId):
        for cat in self._cat:
            if cat['catId'] == catId:
                return cat

    def get_clip(self, uid, _raise=False) -> Optional['Clip']:
        clip = self.clips.get(uid)
        if _raise and not clip:
            raise ClipperError(f"Cannot find {uid}")
        return clip

    def set_name(self, uid, name_dict):
        clip = self.get_clip(uid, True)
        if not isinstance(name_dict, dict):
            raise TypeError(
                "Expect dict contains name info like:\n"
                "    {'en': 'foo', 'zh': '歪比巴伯'}\n"
                "Got " + str(type(name_dict))
            )
        clip.name = name_dict

    def set_class(self):
        pass

    def generate(self, uid):
        self.get_clip(uid, True).generate()

    def upload(self, uid):
        clip = self.get_clip(uid, True)
        ret = self._bucket.upload_local_file(local_file=clip.normalized_path, file_name=clip.full_name)
        return ret

    def publish(self, uid):
        clip = self.get_clip(uid, True)

    def sync_cat(self):
        return requests.post(self._cf_endpoint, data=self._cat, params={"t": self.endpoint_token})

    def _exist_cat(self, catId):
        return catId in [x['catId'] for x in self._cat]

    def _test_token(self):
        return requests.options(self._cf_endpoint, params={"t": self.endpoint_token}).ok

    def _load_cat(self):
        return requests.get(self._cf_endpoint).json()

    def _load_clips(self):
        ret = []
        for x in self._cat:

    def _load_init(self):
        self._cat = self._load_cat()
        self.clips = self._load_clips()
