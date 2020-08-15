from src.clipper import ClipsMeta, Clipper, gen_id
from pprint import pprint
from logging import basicConfig

basicConfig(level="DEBUG")

a = Clipper()
a.publish_clip("eb06d4", "moe", dict(zh="学乌鸦叫", en='Crow\'s Sound'))
# a.put_cat("memes", dict(en='memes', zh='梗', jp='ネタ'))