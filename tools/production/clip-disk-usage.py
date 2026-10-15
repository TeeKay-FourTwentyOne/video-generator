#!/usr/bin/env python3
"""Read allocation evidence; never modify a file. Paths arrive as JSON on stdin."""
import ctypes
import json
import os
import stat
import struct
import sys


def private_bytes(file):
    if sys.platform != "darwin":
        return None

    class AttrList(ctypes.Structure):
        _fields_ = [("bitmapcount", ctypes.c_ushort), ("reserved", ctypes.c_ushort),
                    ("common", ctypes.c_uint32), ("volume", ctypes.c_uint32),
                    ("directory", ctypes.c_uint32), ("file", ctypes.c_uint32),
                    ("extended", ctypes.c_uint32)]

    native = ctypes.CDLL(None, use_errno=True).getattrlist
    native.argtypes = [ctypes.c_char_p, ctypes.POINTER(AttrList), ctypes.c_void_p,
                       ctypes.c_size_t, ctypes.c_ulong]
    native.restype = ctypes.c_int
    # ATTR_CMN_RETURNED_ATTRS + ATTR_CMNEXT_PRIVATESIZE. The returned attribute
    # bitmap distinguishes unsupported attributes from a measured zero.
    request = AttrList(5, 0, 0x80000000, 0, 0, 0, 0x8)
    buffer = ctypes.create_string_buffer(128)
    if native(os.fsencode(file), ctypes.byref(request), buffer, len(buffer), 0x21):
        return None
    length, common, _, _, _, extended = struct.unpack_from("=6I", buffer)
    if length != 32 or not common & 0x80000000 or extended != 0x8:
        return None
    value = struct.unpack_from("=q", buffer, 24)[0]
    return value if value >= 0 else None


def measure(file):
    before = os.lstat(file)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Allocation measurement requires a regular file")
    exclusive = private_bytes(file)
    after = os.lstat(file)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("File changed during allocation measurement")
    return {"logicalBytes": before.st_size, "allocatedBytes": before.st_blocks * 512,
            "privateBytes": exclusive,
            "method": "ATTR_CMNEXT_PRIVATESIZE" if exclusive is not None else "exclusive-allocation-unavailable"}


if __name__ == "__main__":
    paths = json.load(sys.stdin)
    if not isinstance(paths, list) or not paths or len(paths) > 100000 or not all(isinstance(p, str) for p in paths):
        raise ValueError("Provide an explicit list of file paths")
    print(json.dumps([measure(p) for p in paths]))
