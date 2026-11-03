"""Extract the hidden hIds chunk from a SilentNet engine.png, unzip it, pull the payload.

usage: python parse_png.py <png> <workdir>
"""
import hashlib
import os
import struct
import sys
import zipfile
import zlib

png, work = sys.argv[1], sys.argv[2]
raw = open(png, "rb").read()
print("png bytes", len(raw), "sha256", hashlib.sha256(raw).hexdigest())

off, found, blob = 8, [], None
while off + 8 <= len(raw):
    ln = struct.unpack(">I", raw[off:off + 4])[0]
    typ = raw[off + 4:off + 8]
    print(f"chunk {typ!r} at {off} len {ln}")
    if typ in (b"hIds", b"hIDS"):
        found.append(off)
        blob = zlib.decompress(raw[off + 8:off + 8 + ln])
    off += 12 + ln

if not blob:
    print("no hIds chunk")
    sys.exit(2)

zpath = os.path.join(work, "hidden.zip")
open(zpath, "wb").write(blob)
print("zip bytes", len(blob), "sha256", hashlib.sha256(blob).hexdigest())

z = zipfile.ZipFile(zpath)
names = z.namelist()
print("entries", len(names))
open(os.path.join(work, "ziplist.txt"), "w").write("\n".join(names))

out = os.path.join(work, "z")
for n in names:
    if n.endswith(("main.py", "app.pyd", ".dll")) and n.count("/") < 3:
        z.extract(n, out)

for root, _, files in os.walk(out):
    for f in files:
        p = os.path.join(root, f)
        print("extracted", p, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest())
