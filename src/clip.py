import re
import uuid

from youtube_dl import YoutubeDL
from ffmpeg_normalize import FFmpegNormalize


class Clip:
    _time_pattern = re.compile(r"\d*:[0-5]\d?:[0-5]\d?")
    _b2_url_template = "https://f002.backblazeb2.com/file/RushiaBtn/{}"

    def __init__(self, url, start="0:0:0", end=None):
        if not self._valid_time(start):
            raise ClipperError("Invalid start time format (`h[h]:m[m]:s[s]`)")
        if end and not self._valid_time(end):
            raise ClipperError("Invalid end time format (`h[h]:m[m]:s[s]`)")
        self.url = url
        self.start = start
        self.end = end
        self.uid = self._gen_id()
        self.full_name = f"{self.uid}.mp3"
        self.downloaded_path = None
        self.normalized_path = None
        self.file_url = None
        self.published = False
        self.b2session = b2session
        self._generate()

    def generate(self) -> 'Clip':
        self._download()
        self._normalize()
        return self

    def upload(self):
        return self.b2session.upload(self)

    def publish(self):
        pass

    def _valid_time(self, *t):
        return all([self._time_pattern.match(x) for x in t])

    def _download(self):
        sub_arg = ['-ss', self.start]
        out = f"storage/{self.uid}.%(ext)s"
        if self.end:
            sub_arg.extend(['-to', self.end])
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
            ytdl.download([self.url])
        self.downloaded_path = out % {'ext': 'mp3'}

    def _normalize(self, target_level=-16):
        fn = FFmpegNormalize(normalization_type="rms",
                             audio_codec="libmp3lame",
                             target_level=target_level)
        out = f"normalized/{self.full_name}"
        fn.add_media_file(self.downloaded_path, out)
        fn.run_normalization()
        self.normalized_path = out

    @staticmethod
    def _gen_id():
        return str(uuid.uuid4())[:8]

    @property
    def json(self):
        return dict(
            start=self.start,
            end=self.end,
            url=self.url,
            uid=self.uid,
            full_name=self.full_name,
            cat=self.cat if self.cat else "",
            name=self.name if self.name else {},
            downloaded_path=self.downloaded_path if self.downloaded_path else "",
            normalized_path=self.normalized_path if self.normalized_path else "",
        )

    @property
    def status(self):
        if self.published:
            return "PUBLISHED"
        elif self.file_url:
            return "UPLOADED"
        elif self.normalized_path or self.downloaded_path:
            return "GENERATED"
        else:
            return "PENDING"


class ClipperError(Exception):
    pass