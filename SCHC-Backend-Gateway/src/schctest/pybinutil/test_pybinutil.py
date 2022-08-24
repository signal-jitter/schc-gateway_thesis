
import unittest

try:
    from pybinutil import byteutil as by
    from pybinutil import bitutil as bi
    print("# pybinutil test")
except:
    import byteutil as by
    import bitutil as bi
    print("# module test")

class Test_byteutil(unittest.TestCase):

    ## to_bit()
    def test_to_bit(self):
        n= [
            ([0], ['00000000']),
            ([1], ['00000001']),
            ([7], ['00000111']),
            ([8], ['00001000']),
            ([255], ['11111111']),
            ([128, 0], ['10000000', '00000000']),
            ([128, 1], ['10000000', '00000001']),
        ]
        for k, v in n:
            self.assertEqual(by.to_bit(bytearray(k)), v)

    ## to_hex()
    def test_to_hex(self):
        n= [
            ([0], ['00']),
            ([1], ['01']),
            ([7], ['07']),
            ([8], ['08']),
            ([255], ['ff']),
            ([128, 0], ['80', '00']),
            ([128, 1], ['80', '01']),
        ]
        for k, v in n:
            self.assertEqual(by.to_hex(bytearray(k)), v)

    ## to_int()
    def test_to_int(self):
        n= [
            ([0], 0),
            ([1], 1),
            ([7], 7),
            ([8], 8),
            ([255], 255),
            ([128, 0], 32768),
            ([128, 1], 32769),
        ]
        for k, v in n:
            self.assertEqual(by.to_int(bytearray(k)), v)

    ## to_int(reverse=True)
    def test_to_int_rev(self):
        n= [
            ([0], 0),
            ([1], 1),
            ([7], 7),
            ([8], 8),
            ([255], 255),
            ([128, 0], 128),
            ([128, 1], 384),
        ]
        for k, v in n:
            self.assertEqual(by.to_int(bytearray(k), reverse=True), v)

    ## int_to()
    def test_int_to(self):
        n= [
            (0, ['00000000']),
            (1, ['00000001']),
            (255, ['11111111']),
            (32768, ['10000000', '00000000']),
            (32769, ['10000000', '00000001']),
        ]
        for k, v in n:
            self.assertEqual(by.to_bit(by.int_to(k)), v)

    ## int_to(): 4 bytes width
    def test_int_to_fixed_width_4(self):
        n = [
            (0, ['00000000', '00000000', '00000000', '00000000']),
            (1, ['00000000', '00000000', '00000000', '00000001']),
            (255, ['00000000', '00000000', '00000000', '11111111']),
            (32768, ['00000000', '00000000', '10000000', '00000000']),
            (32769, ['00000000', '00000000', '10000000', '00000001']),
        ]
        for k, v in n:
            self.assertEqual(by.to_bit(by.int_to(k, 4)), v)

    ## int_to(): 3 bytes width
    def test_int_to_fixed_width_3(self):
        n = [
            (0, ['00000000', '00000000', '00000000']),
            (1, ['00000000', '00000000', '00000001']),
            (255, ['00000000', '00000000', '11111111']),
            (32768, ['00000000', '10000000', '00000000']),
            (32769, ['00000000', '10000000', '00000001']),
        ]
        for k, v in n:
            self.assertEqual(by.to_bit(by.int_to(k, 3)), v)

#
# test for bitutil
#

class Test_bitutil(unittest.TestCase):

    ## bit_get(ba, j, 6)
    def test_bit_get(self):
        n = [
            (0, [
                (0, "000000"),
                (1, "000000"),
                (2, "000000"),
                (3, "00000"),
                (4, "0000"),
                (5, "000"),
                (6, "00"),
                (7, "0"),
                ]),
            (1, [
                (0, "000000"),
                (1, "000000"),
                (2, "000001"),
                (3, "00001"),
                (4, "0001"),
                (5, "001"),
                (6, "01"),
                (7, "1"),
                ]),
            (0x8001, [
                ( 0, "100000"),
                ( 1, "000000"),
                ( 2, "000000"),
                ( 3, "000000"),
                ( 4, "000000"),
                ( 5, "000000"),
                ( 6, "000000"),
                ( 7, "000000"),
                ( 8, "000000"),
                ( 9, "000000"),
                (10, "000001"),
                (11, "00001"),
                (12, "0001"),
                (13, "001"),
                (14, "01"),
                (15, "1"),
                ])
            ]
        for k, v in n:
            ba = by.int_to(k)
            for i, j in v:
                self.assertEqual(bi.bit_get(ba, i, 6), j)

    ## bit_get(type=int)
    def test_bit_get_int(self):
        # 1101 0010 0010 0000
        ba = bytearray([0xd2, 0x20])
        n = [
            ( 0, 1, 1),
            ( 1, 2, 2),
            ( 3, 3, 4),
            ( 6, 4, 8),
            (10, 5, 16),
            ]
        for i, j, k in n:
            self.assertEqual(bi.bit_get(ba, i, j, ret_type=int), k)

    ## bit_get(type=hex)
    def test_bit_get_hex(self):
        # 1101 0010 0010 0000
        ba = bytearray([0xd2, 0x20])
        n = [
            ( 0,  1, "1"),
            ( 0,  2, "3"),
            ( 0,  8, "d2"),
            ( 0, 12, "d22"),
            ( 0, 16, "d220"),
            ]
        for i, j, k in n:
            self.assertEqual(bi.bit_get(ba, i, j, ret_type=hex), k)

    ## bit_get(type=bytes)
    def test_bit_get_bytes(self):
        # 1111 0010 0010 0010
        ba = bytearray([0xf2, 0x22])
        n = [
            ( 0, 1, bytearray([0x80])),       # 1000 0000
            ( 1, 2, bytearray([0xc0])),       # 1100 0000
            ( 3, 8, bytearray([0x91])),       # 1001 0001
            ( 3,12, bytearray([0x91, 0x10])), # 1001 0001 0001
            ]
        for i, j, k in n:
            self.assertEqual(bi.bit_get(ba, i, j, ret_type=bytes), k)

    ## bit_set()
    def test_bit_set(self):
        # 0010 0011 1100 0010
        ba0 = bytearray(2)
        bi.bit_set(ba0, 2)
        bi.bit_set(ba0, 6, "1111")
        bi.bit_set(ba0, 14)
        self.assertEqual(by.to_bit(ba0), ['00100011', '11000010'])
             
    ## bit_set() implicit")
    def test_bit_set_implicit(self):
        n = [
            ( 0, ['10000000', '00000000']),
            ( 1, ['01000000', '00000000']),
            ( 2, ['00100000', '00000000']),
            ( 3, ['00010000', '00000000']),
            ( 4, ['00001000', '00000000']),
            ( 5, ['00000100', '00000000']),
            ( 6, ['00000010', '00000000']),
            ( 7, ['00000001', '00000000']),
            ( 8, ['00000000', '10000000']),
            ( 9, ['00000000', '01000000']),
            (10, ['00000000', '00100000']),
            (11, ['00000000', '00010000']),
            (12, ['00000000', '00001000']),
            (13, ['00000000', '00000100']),
            (14, ['00000000', '00000010']),
            (15, ['00000000', '00000001']),
            (16, ['00000000', '00000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k)), v)

    ## bit_set(1)")
    def test_bit_set_1(self):
        n = [
            ( 0, ['10000000', '00000000']),
            ( 1, ['01000000', '00000000']),
            ( 2, ['00100000', '00000000']),
            ( 3, ['00010000', '00000000']),
            ( 4, ['00001000', '00000000']),
            ( 5, ['00000100', '00000000']),
            ( 6, ['00000010', '00000000']),
            ( 7, ['00000001', '00000000']),
            ( 8, ['00000000', '10000000']),
            ( 9, ['00000000', '01000000']),
            (10, ['00000000', '00100000']),
            (11, ['00000000', '00010000']),
            (12, ['00000000', '00001000']),
            (13, ['00000000', '00000100']),
            (14, ['00000000', '00000010']),
            (15, ['00000000', '00000001']),
            (16, ['00000000', '00000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, "1")), v)

    ## bit_set(10)")
    def test_bit_set_10(self):
        n = [
            ( 0, ['10000000', '00000000']),
            ( 1, ['01000000', '00000000']),
            ( 2, ['00100000', '00000000']),
            ( 3, ['00010000', '00000000']),
            ( 4, ['00001000', '00000000']),
            ( 5, ['00000100', '00000000']),
            ( 6, ['00000010', '00000000']),
            ( 7, ['00000001', '00000000']),
            ( 8, ['00000000', '10000000']),
            ( 9, ['00000000', '01000000']),
            (10, ['00000000', '00100000']),
            (11, ['00000000', '00010000']),
            (12, ['00000000', '00001000']),
            (13, ['00000000', '00000100']),
            (14, ['00000000', '00000010']),
            (15, ['00000000', '00000001']),
            (16, ['00000000', '00000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, "10")), v)

    ## bit_set(01)")
    def test_bit_set_01(self):
        n = [
            ( 0, ['01000000', '00000000']),
            ( 1, ['00100000', '00000000']),
            ( 2, ['00010000', '00000000']),
            ( 3, ['00001000', '00000000']),
            ( 4, ['00000100', '00000000']),
            ( 5, ['00000010', '00000000']),
            ( 6, ['00000001', '00000000']),
            ( 7, ['00000000', '10000000']),
            ( 8, ['00000000', '01000000']),
            ( 9, ['00000000', '00100000']),
            (10, ['00000000', '00010000']),
            (11, ['00000000', '00001000']),
            (12, ['00000000', '00000100']),
            (13, ['00000000', '00000010']),
            (14, ['00000000', '00000001']),
            (15, ['00000000', '00000000']),
            (16, ['00000000', '00000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, "01")), v)

    ## bit_set(110)")
    def test_bit_set_110(self):
        n = [
            ( 0, ['11000000', '00000000']),
            ( 1, ['01100000', '00000000']),
            ( 2, ['00110000', '00000000']),
            ( 3, ['00011000', '00000000']),
            ( 4, ['00001100', '00000000']),
            ( 5, ['00000110', '00000000']),
            ( 6, ['00000011', '00000000']),
            ( 7, ['00000001', '10000000']),
            ( 8, ['00000000', '11000000']),
            ( 9, ['00000000', '01100000']),
            (10, ['00000000', '00110000']),
            (11, ['00000000', '00011000']),
            (12, ['00000000', '00001100']),
            (13, ['00000000', '00000110']),
            (14, ['00000000', '00000011']),
            (15, ['00000000', '00000001']),
            (16, ['00000000', '00000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, "110")), v)

    ## bit_set(extend=True)")
    def test_bit_set_extend(self):
        n = [
            ( 0, ['10000000']),
            ( 1, ['01000000']),
            ( 2, ['00100000']),
            ( 3, ['00010000']),
            ( 4, ['00001000']),
            ( 5, ['00000100']),
            ( 6, ['00000010']),
            ( 7, ['00000001']),
            ( 8, ['00000000', '10000000']),
            ( 9, ['00000000', '01000000']),
            (10, ['00000000', '00100000']),
            (11, ['00000000', '00010000']),
            (12, ['00000000', '00001000']),
            (13, ['00000000', '00000100']),
            (14, ['00000000', '00000010']),
            (15, ['00000000', '00000001']),
            (16, ['00000000', '00000000', '10000000']),
        ]
        for k, v in n:
            ba0 = bytearray(1)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, extend=True)), v)

    ## bit_set(110, extend=True)")
    def test_bit_set_extend(self):
        n = [
            ( 0, ['11000000', '00000000']),
            ( 1, ['01100000', '00000000']),
            ( 2, ['00110000', '00000000']),
            ( 3, ['00011000', '00000000']),
            ( 4, ['00001100', '00000000']),
            ( 5, ['00000110', '00000000']),
            ( 6, ['00000011', '00000000']),
            ( 7, ['00000001', '10000000']),
            ( 8, ['00000000', '11000000']),
            ( 9, ['00000000', '01100000']),
            (10, ['00000000', '00110000']),
            (11, ['00000000', '00011000']),
            (12, ['00000000', '00001100']),
            (13, ['00000000', '00000110']),
            (14, ['00000000', '00000011', '00000000']),
            (15, ['00000000', '00000001', '10000000']),
            (16, ['00000000', '00000000', '11000000']),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(by.to_bit(bi.bit_set(ba0, k, "110",
                                                  extend=True)), v)

    ## int_to_bit(32)
    def test_int_to_bit_32(self):
        n = [
            ( 0, "00000000000000000000000000000000" ),
            ( 1, "00000000000000000000000000000001" ),
            ( 0xff, "00000000000000000000000011111111" ),
            ( 0x8000, "00000000000000001000000000000000" ),
            ( 0x8001, "00000000000000001000000000000001" ),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(bi.int_to_bit(k, 32), v)

    ## int_to_bit(8)
    def test_int_to_bit_8(self):
        n = [
            ( 0, "00000000" ),
            ( 1, "00000001" ),
            ( 0xff, "11111111" ),
            ( 0x8000, "00000000" ),
            ( 0x8001, "00000001" ),
        ]
        for k, v in n:
            ba0 = bytearray(2)
            self.assertEqual(bi.int_to_bit(k, 8), v)

    ## bit_find(size=16)
    def test_bit_find_16(self):
        n = [
            ( 0, (None, 0)),
            ( 1, (15, 0 )),
            ( 0xff, (8, 0x7f )),
            ( 0x8000, (0, 0 )),
            ( 0x8001, (0, 1 )),
        ]
        for k, v in n:
            self.assertEqual(bi.bit_find(k, 16), v)

    ## bit_find(size=8)
    def test_bit_find_8(self):
        n = [
            ( 0, (None, 0)),
            ( 1, (7, 0 )),
            ( 0xff, (0, 0x7f )),
            ( 0x8000, (None, 0x8000 )),
            ( 0x8001, (7, 0x8000 )),
        ]
        for k, v in n:
            self.assertEqual(bi.bit_find(k, 8), v)

    ## bit_find(size=implicit)
    def test_bit_find_implicit(self):
        n = [
            ( 0, (None, 0)),
            ( 1, (0, 0)),
            ( 0xff, (0, 0x7f)),
            ( 0x8000, (0, 0)),
            ( 0x8001, (0, 1)),
        ]
        for k, v in n:
            self.assertEqual(bi.bit_find(k), v)

    ## bit_count(32)
    def test_bit_count_32(self):
        n = [
            ( 0, 0 ),
            ( 1, 1 ),
            ( 255, 8 ),
            ( 32768, 1 ),
            ( 32769, 2 ),
        ]
        for k, v in n:
            bi.int_to_bit(k, 8)
            self.assertEqual(bi.bit_count(k, 32), v)

    ## bit_count(8True)
    def test_bit_count_zero_8(self):
        n = [
            ( 0, 0 ),
            ( 1, 1 ),
            ( 255, 8 ),
            ( 32768, 0 ),
            ( 32769, 1 ),
        ]
        for k, v in n:
            bi.int_to_bit(k, 8)
            self.assertEqual(bi.bit_count(k, 8), v)

    ## bit_count(32, zero=True)
    def test_bit_count_zero_32(self):
        n = [
            ( 0, 32 ),
            ( 1, 31 ),
            ( 255, 24 ),
            ( 32768, 31 ),
            ( 32769, 30 ),
        ]
        for k, v in n:
            bi.int_to_bit(k, 8)
            self.assertEqual(bi.bit_count(k, 32, zero=True), v)

    ## bit_count(8, zero=True)
    def test_bit_count_zero_8(self):
        n = [
            ( 0, 8 ),
            ( 1, 7 ),
            ( 255, 0 ),
            ( 32768, 8 ),
            ( 32769, 7 ),
        ]
        for k, v in n:
            bi.int_to_bit(k, 8)
            self.assertEqual(bi.bit_count(k, 8, zero=True), v)

if __name__ == '__main__':
    unittest.main()
