#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2
from mom.builtins import unicode_to_utf8, b
from mom.codec.json import encode, decode


class Test_json_decode(unittest2.TestCase):
    def test_json_decode(self):
        # json_decode accepts both bytes and unicode, but strings it returns
        # are always unicode.
        self.assertEqual(decode(b('"foo"')), u"foo")
        self.assertEqual(decode(u'"foo"'), u"foo")

        # Non-ascii bytes are interpreted as utf8
        self.assertEqual(decode(unicode_to_utf8(u'"\u00e9"')), u"\u00e9")


class Test_json_encode(unittest2.TestCase):
    def test_json_encode(self):
        # json deals with strings, not bytes, but our encoding function should
        # accept bytes as well as long as they are utf8.
        self.assertEqual(decode(encode(u"\u00e9")), u"\u00e9")
        self.assertEqual(decode(encode(unicode_to_utf8(u"\u00e9"))), u"\u00e9")
        self.assertRaises(UnicodeDecodeError, encode, b("\xe9"))

if __name__ == "__main__":
    unittest2.main()
