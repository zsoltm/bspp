import hashlib
from zipfile import ZipFile
import struct


def pk3_hash(file_name: str) -> bytes:
    """
    Implement Quake3's pk3 hashing.
    It's essentially an md4 hash of all crc32 values in the archive that are greater than zero size uncompressed,
    that is split into four 32bit ints, that are xor-ed into each other.
    :param file_name: input pk3 file.
    :return: hash bytes -- that has a hex() method.
    """
    md4 = hashlib.new("md4")
    with ZipFile(file_name, 'r') as zip_obj:
        info_list = zip_obj.infolist()
        for info in info_list:
            if info.file_size > 0:
                md4.update(struct.pack('<I', info.CRC))
    digest = md4.digest()
    int1, int2, int3, int4 = struct.unpack('<IIII', digest)
    hash_value = int1 ^ int2 ^ int3 ^ int4
    return struct.pack('>I', hash_value)


if __name__ == '__main__':
    import sys
    import os

    for root, dirs, files in os.walk(sys.argv[1]):
        for fn in files:
            if fn[-4:].lower() == '.pk3':
                # print("ID3Hash:", '{:0>8}'.format(pak_hash(sys.argv[1]).hex()))
                print("ID3Hash:", pk3_hash(os.path.join(root, fn)).hex(), "--", fn)
