"""Inert ELF64 fixtures reproducing Debian libstdc++ DT_STRSZ=308098.

No system library mutation, compilation, loader or genuine inference execution.
"""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from research.qualification_035 import provision as p
from research import controlled_build_037 as build

BASE=0x400000
TABLE_OFFSET=4096
DYNAMIC_OFFSET=512


def fixture(size, *, declared=None, needed_at=None):
    # Use end-of-table names, well beyond 64 KiB for the actual Debian-sized case.
    table=bytearray(size)
    name=b'libc.so.6\0'
    offset=size-len(name) if needed_at is None else needed_at
    if 0<=offset and offset+len(name)<=size:table[offset:offset+len(name)]=name
    tags=[(1,offset),(5,BASE+TABLE_OFFSET),(10,size if declared is None else declared),(0,0)]
    image=bytearray(TABLE_OFFSET+size)
    image[:64]=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF\x02\x01'+b'\0'*10,3,62,1,0,64,0,0,64,56,2,0,0,0)
    image[64:120]=struct.pack('<IIQQQQQQ',1,5,0,BASE,0,len(image),len(image),4096)
    image[120:176]=struct.pack('<IIQQQQQQ',2,4,DYNAMIC_OFFSET,BASE+DYNAMIC_OFFSET,0,len(tags)*16,len(tags)*16,8)
    for i,pair in enumerate(tags):struct.pack_into('<qQ',image,DYNAMIC_OFFSET+16*i,*pair)
    image[TABLE_OFFSET:]=table
    return image


def program_field(image,index,field,value):
    header=list(struct.unpack_from('<IIQQQQQQ',image,64+index*56));header[field]=value
    struct.pack_into('<IIQQQQQQ',image,64+index*56,*header)


class StringTableTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'inert.so'
    def parse(self,image,*,expected=None,consumer=p.elf):
        self.path.write_bytes(image)
        sha=hashlib.sha256(image).hexdigest() if expected is None else expected
        return consumer(self.path,sha)
    def test_debian_308098_byte_table_names_after_64k(self):
        image=fixture(308098)
        self.assertEqual(self.parse(image)['needed'],['libc.so.6'])
        self.assertEqual(self.parse(image,consumer=build.passive_elf)['needed'],['libc.so.6'])
    def test_original_64k_and_larger_tables_and_exact_1m_boundary(self):
        for size in (65536,65537,1024*1024):
            with self.subTest(size=size):self.assertEqual(self.parse(fixture(size))['needed'],['libc.so.6'])
    def test_1m_plus_one_rejected_even_if_file_and_segment_fit(self):
        with self.assertRaisesRegex(ValueError,'ELF_STRING_TABLE'):self.parse(fixture(1024*1024+1))
    def test_zero_or_absent_strsz_rejected(self):
        for declared in (0,1024*1024+1):
            with self.subTest(declared=declared),self.assertRaisesRegex(ValueError,'ELF_STRING_TABLE'):
                self.parse(fixture(308098,declared=declared))
        image=fixture(308098);struct.pack_into('<q',image,DYNAMIC_OFFSET+32,99)
        with self.assertRaisesRegex(ValueError,'ELF_STRING_TABLE'):self.parse(image)
    def test_missing_strtab_address_rejected(self):
        image=fixture(308098);struct.pack_into('<q',image,DYNAMIC_OFFSET+16,99)
        with self.assertRaisesRegex(ValueError,'ELF_STRING_TABLE'):self.parse(image)
    def test_string_table_crosses_load_segment_rejected(self):
        image=fixture(308098);program_field(image,0,5,len(image)-1)
        with self.assertRaisesRegex(ValueError,'ELF_STRING_MAPPING'):self.parse(image)
    def test_string_table_address_outside_load_segment_rejected(self):
        image=fixture(308098);struct.pack_into('<Q',image,DYNAMIC_OFFSET+24,BASE+len(image))
        with self.assertRaisesRegex(ValueError,'ELF_STRING_MAPPING'):self.parse(image)
    def test_truncated_file_rejected_with_matching_truncated_hash(self):
        image=fixture(308098)[:-1]
        with self.assertRaisesRegex(ValueError,'ELF_STRING_MAPPING|ELF_TRUNCATED'):self.parse(image)
    def test_load_segment_outside_file_rejected(self):
        image=fixture(308098);program_field(image,0,2,len(image)+1)
        with self.assertRaisesRegex(ValueError,'ELF_STRING_MAPPING'):self.parse(image)
    def test_load_filesz_larger_than_memsz_rejected(self):
        image=fixture(308098);program_field(image,0,6,len(image)-1)
        with self.assertRaisesRegex(ValueError,'ELF_STRING_MAPPING'):self.parse(image)
    def test_needed_offset_at_end_and_unterminated_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'ELF_STRING_INVALID'):self.parse(fixture(308098,needed_at=308098))
        image=fixture(308098);image[-1]=ord('x')
        with self.assertRaisesRegex(ValueError,'ELF_STRING_INVALID'):self.parse(image)
    def test_hash_binding_still_rejects_corruption(self):
        image=fixture(308098);sha=hashlib.sha256(image).hexdigest();image[-2]^=1
        with self.assertRaisesRegex(ValueError,'ELF_HASH_BINDING'):self.parse(image,expected=sha)
    def test_unrelated_dynamic_metadata_64k_boundary_and_overflow(self):
        image=fixture(308098);program_field(image,1,5,65536);program_field(image,1,6,65536)
        # DT_NULL terminates the actual four entries; padding is inert.
        self.assertEqual(self.parse(image)['needed'],['libc.so.6'])
        program_field(image,1,5,65536+16);program_field(image,1,6,65536+16)
        with self.assertRaisesRegex(ValueError,'ELF_METADATA_LIMIT'):self.parse(image)
    def test_interpreter_metadata_limit_is_still_64k(self):
        image=fixture(308098)
        # Turn the second header into PT_INTERP for the independent metadata cap.
        program_field(image,1,0,3);program_field(image,1,2,TABLE_OFFSET);program_field(image,1,3,BASE+TABLE_OFFSET)
        program_field(image,1,5,65536);program_field(image,1,6,65536)
        value=b'/lib/ld-inert.so\0';image[TABLE_OFFSET:TABLE_OFFSET+len(value)]=value
        self.assertEqual(self.parse(image)['interpreter'],'/lib/ld-inert.so')
        program_field(image,1,5,65537);program_field(image,1,6,65537)
        with self.assertRaisesRegex(ValueError,'ELF_METADATA_LIMIT'):self.parse(image)
    def test_dynamic_misalignment_and_truncation_rejected(self):
        image=fixture(308098);program_field(image,1,5,63)
        with self.assertRaisesRegex(ValueError,'ELF_DYNAMIC_INVALID'):self.parse(image)
        program_field(image,1,5,64);program_field(image,1,2,len(image)-32)
        with self.assertRaisesRegex(ValueError,'ELF_TRUNCATED'):self.parse(image)


if __name__=='__main__':unittest.main()
