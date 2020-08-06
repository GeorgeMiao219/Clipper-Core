import uuid
from typing import Optional


class Clipper:
    def __init__(self):
        self.pending = {}
        self.downloaded = {}
        self.published = {}

    def search(self, cid) -> Optional['Clip']:
        return self.pending.get(cid) or self.downloaded.get(cid) or self.published.get(cid) or None

    def new_clip(self, url, start, end):
        clip = Clip(url, start, end)
        self.pending[cid := clip.cid] = clip
        return cid

    def download_clip(self, cid):
        pass

    def process_clip(self, cid):
        pass

    def upload_clip(self, cid):
        pass

    def publish_clip(self, cid):
        pass

    def _normalize(self, cid):
        pass


class Clip:
    def __init__(self, url, start, end):
        self.url = url
        self.start = start
        self.end = end
        self.path = None
        self.normalized = False
        self.downloaded = False
        self.published = False
        self.cid = self._gen_id()

    @staticmethod
    def _gen_id():
        return str(uuid.uuid4())[:8]