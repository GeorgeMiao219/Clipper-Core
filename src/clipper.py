import os
import re
import uuid
import json
import atexit
from typing import Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from time import time

from src.exception import ClipError

from requests import Session
from youtube_dl import YoutubeDL
from ffmpeg_normalize import FFmpegNormalize
from b2sdk.v1 import InMemoryAccountInfo, B2Api


def gen_id():
    return str(uuid.uuid4())[:6]


@atexit.register
def clean():
    if instance := Clipper.instance:
        instance.save()


@dataclass
class Clip:
    url: str
    start: str = "0:0:0"
    end: str = None
    uid: str = field(default_factory=gen_id)
    download_path: Path = None
    normalized_path: Path = None
    file_url: str = None
    published: bool = False


class Clipper:
    _time_pattern = re.compile(r"\d*:[0-5]\d?:[0-5]\d?")
    _local_clips_path = Path("../clips.json")
    instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.instance:
            obj = object.__new__(cls)
            cls.instance = obj
            return obj
        else:
            return cls.instance

    def __init__(self):
        self.clips = None
        self.load_local_clips()
        self.meta = ClipsMeta.from_url(os.environ["TOKEN"])
        key_id = os.environ["B2_KEY_ID"]
        app_key = os.environ["B2_APP_KEY"]
        if not (key_id and app_key):
            raise ClipError("Credential for B2 is needed, "
                            "set B2_KEY_ID and B2_APP_KEY "
                            "as environment variable or pass in as arguments")
        info = InMemoryAccountInfo()
        self._api = B2Api(info)
        self._api.authorize_account("production", key_id, app_key)
        self._bucket = self._api.get_bucket_by_name("RushiaBtn")
        self._file_link_template = "https://f002.backblazeb2.com/file/RushiaBtn/{}"

    def load_local_clips(self):
        if self._local_clips_path.exists():
            with open(self._local_clips_path, "r") as f:
                self.clips = {k: Clip(**v) for k, v in json.load(f).items()}
        else:
            self._local_clips_path.touch()
            with open(self._local_clips_path, "w") as f:
                self.clips = dict()
                json.dump(self.clips, f)

    def search(self, uid) -> Optional['Clip']:
        clip = self.clips.get(uid)
        if not clip:
            raise ClipError(f"Unable to find clip #{uid}")
        return clip

    def new_clip(self, url, start, end):
        if start and not self._time_pattern.match(start):
            raise ClipError("Invalid start")
        if end and not self._time_pattern.match(end):
            raise ClipError("Invalid end")
        clip = Clip(url, start, end)
        uid = clip.uid
        self.clips[uid] = clip
        return uid

    def download_clip(self, uid):
        clip = self.search(uid)
        sub_arg = ['-ss', clip.start]
        out = f"storage/{clip.uid}.%(ext)s"
        if clip.end:
            sub_arg.extend(['-to', clip.end])
        with YoutubeDL({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'postprocessor_args': sub_arg,
            'prefer_ffmpeg': True,
            'outtmpl': out
        }) as ytdl:
            ytdl.download([clip.url])
        clip.download_path = out % {'ext': 'mp3'}
        return True

    def normalize_clip(self, uid):
        clip = self.search(uid)
        fn = FFmpegNormalize(normalization_type="rms",
                             audio_codec="libmp3lame",
                             target_level=-16)
        out = f"normalized/{clip.uid}.mp3"
        fn.add_media_file(clip.download_path, out)
        fn.run_normalization()
        clip.normalized_path = out

    def upload_clip(self, uid):
        clip = self.search(uid)
        full_name = f"{clip.uid}.mp3"
        self._bucket.upload_local_file(local_file=clip.normalized_path,
                                       file_name=full_name)
        clip.file_url = self._file_link_template.format(full_name)

    def generate(self, url, start, end):
        uid = self.new_clip(url, start, end)
        self.download_clip(uid)
        self.normalize_clip(uid)
        self.upload_clip(uid)
        return uid

    def publish_clip(self, uid, cat, names):
        clip = self.search(uid)
        self.meta.put_clip(clip, cat, names)
        self.meta.upload()
        clip.published = True

    def put_cat(self, _id, names):
        self.meta.put_cat(_id, names)

    def get_info(self, uid):
        return asdict(self.search(uid))

    def save(self):
        with open(self._local_clips_path, "w") as f:
            json.dump({clip.uid: asdict(clip) for clip in self.clips.values()}, f)


class ClipsMeta:
    _cf_endpoint = "https://category.rushia.moe"

    def __init__(self, url, token):
        self.s = Session()  # Requests Session for request and upload meta json
        self.url = url or self._cf_endpoint
        self.json = None
        self.categories = {}
        self.clips = {}
        self.token = token
        self.test_token()

    @classmethod
    def from_url(cls, token, url=None):
        obj = cls(url, token)
        obj.download()
        return obj

    def test_token(self):
        req = self.s.options(self._cf_endpoint, params={'t': self.token})
        if not req.ok:
            raise ClipError("Invalid token")
        return True

    def download(self):
        self.json = self.s.get(self.url).json()
        self.categories = self.json['categories']
        self.clips = self.json['clips']

    def upload(self):
        res = self.s.put(self.url, json=self.json, params={'t': self.token})
        if not res.ok:
            raise ClipError(f"Upload failed: {res.text}")

    def put_cat(self, _id, names):
        self.categories[_id] = names

    def put_clip(self, clip: Clip, cat, names):
        if cat not in self.categories.keys():
            raise ClipError(f"Unable to find {cat}, "
                            f"use `put_cat` to create")
        self.clips[clip.uid] = {
            "name": names,
            "category": cat,
            "url": clip.file_url,
            "publish_time": int(time())
        }
        self.upload()
