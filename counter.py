import os
from collections import defaultdict  # print(*zip(dupes, sizes), sep="\n")
path = r"Z:/KisPeti/SULI/ipari/p/pc/insta"
counter = defaultdict(int)
for i in os.listdir(path):
    name = i.split("-")[0]
    counter[name] += 1
counter = dict(sorted(counter.items(), key=lambda x: x[1], reverse=True))
print(*counter.items(), sep="\n")
print(len(counter))
print("asd---asd")
print(*[f"{k} {(v)}" for k,v in counter.items() if v > 1],sep="\n")