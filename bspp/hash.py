import hashlib
import struct
from typing import List
from zipfile import ZipFile, ZipInfo


def pk3_hash_info(inf_list: List[ZipInfo]) -> bytes:
    md4 = hashlib.new("md4")
    for info in inf_list:
        if info.file_size > 0:
            md4.update(struct.pack("<I", info.CRC))
    digest = md4.digest()
    return _md4_to_32bit(digest)


def _md4_to_32bit(digest: bytes):
    int1, int2, int3, int4 = struct.unpack("<IIII", digest)
    hash_value = int1 ^ int2 ^ int3 ^ int4
    return struct.pack(">I", hash_value)


def pk3_hash(file_name: str) -> bytes:
    """
    Implement Quake3's pk3 hashing.
    It's essentially an md4 hash of all crc32 values in the archive that are greater than zero size uncompressed,
    that is split into four 32bit ints, that are xor-ed into each other.
    :param file_name: input pk3 file.
    :return: hash bytes -- that has a hex() method.
    """
    with ZipFile(file_name, "r") as zip_obj:
        return pk3_hash_info(zip_obj.infolist())


def bsp_hash(b: bytes) -> bytes:
    md4 = hashlib.new("md4")
    md4.update(b)
    digest = md4.digest()
    # A553 4CD1
    return _md4_to_32bit(digest)
