from src.clipper import ClipsMeta, Clipper, gen_id
from pprint import pprint


# a = Clipper()
# uid = a.generate("https://youtu.be/_6_gwZd-HEE", "00:13:48", "00:13:49")
# a.publish_clip("66e985", "moe", dict(zh="绝叫", en='Scary Scream'))


l = []
count = 0
N = 100000
for i in range(N):
    gid = gen_id()
    if gid in l:
        print(f"Collapsed #{count} - {i}/{N}")
        count += 1
    l.append(gid)

print(f"Probability: {count/N*100}%")