import re
from src.clipper import Clipper


"""
A bat program read contents at ../bat which contains clip info like:
https://youtu.be/_6_gwZd-HEE 0:06:52 00:06:53 test_category zh:rua jp:aaa en:fff
^Url                         ^Start  ^End     ^cat          ^names(locale:name)
"""

def main():
    try:
        with open("../bat") as f:
            for line in f.readlines():
                pass