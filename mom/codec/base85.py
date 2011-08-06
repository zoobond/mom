#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: mom.codec.base85
:synopsis: ASCII-85 and RFC1924 Base85 encoding and decoding functions.
:see: http://en.wikipedia.org/wiki/Ascii85

Functions
---------
.. autofunction:: b85encode
.. autofunction:: b85decode
.. autofunction:: rfc1924_b85encode
.. autofunction:: rfc1924_b85decode
.. autofunction:: ipv6_b85encode
.. autofunction:: ipv6_b85decode
"""

from __future__ import absolute_import, division

import re
import string
from struct import unpack, pack
from mom.builtins import is_bytes
from mom._compat import range


__all__ = [
    "b85encode",
    "b85decode",
    "rfc1924_b85encode",
    "rfc1924_b85decode",
    "ADOBE_PREFIX",
    "ADOBE_SUFFIX",
    "WHITESPACE_PATTERN",
    "ipv6_b85encode",
    "ipv6_b85decode",
]

# Use this if you want the base85 codec to encode/decode including
# Adobe's prefixes/suffixes.
ADOBE_PREFIX = '<~'
ADOBE_SUFFIX = '~>'

WHITESPACE_PATTERN = re.compile(r'(\s)*', re.MULTILINE)


def _ascii85_chr(num):
    """
    Converts an ordinal into its ASCII85 character.

    :param num:
        Ordinal value.
    :returns:
        base85 character.
    """
    return chr(num + 33)


def _ascii85_ord(char):
    """
    Converts an ASCII85 character into its ordinal.

    :param char:
        Base85 character
    :returns:
        Ordinal value.
    """
    return ord(char) - 33


# ASCII85 characters.
ASCII85_CHARS = "".join(map(_ascii85_chr, range(85)))
ASCII85_ORDS = dict((x, _ascii85_ord(x)) for x in ASCII85_CHARS)

# http://tools.ietf.org/html/rfc1924
RFC1924_CHARS = string.digits + \
                string.uppercase + \
                string.lowercase +  "!#$%&()*+-;<=>?@^_`{|}~"
WHITESPACE_CHARS = string.whitespace
RFC1924_ORDS = dict((x, i) for i, x in enumerate(RFC1924_CHARS))


def b85encode(raw_bytes,
              prefix=None,
              suffix=None,
              _padding=False,
              _base85_chars=ASCII85_CHARS):
    """
    ASCII-85 encodes a sequence of raw bytes.

    If the number of raw bytes is not divisible by 4, the byte sequence
    is padded with up to 3 null bytes before encoding. After encoding,
    as many bytes as were added as padding are removed from the end of the
    encoded sequence if ``padding`` is ``False`` (default).

    Encodes a zero-group (\x00\x00\x00\x00) as 'z' instead of '!!!!!'.

    The resulting encoded ASCII string is *not URL-safe* nor is it
    safe to include within SGML/XML/HTML documents. You will need to escape
    special characters if you decide to include such an encoded string
    within these documents.

    :param raw_bytes:
        Raw bytes.
    :param prefix:
        The prefix used by the encoded text. None by default.
    :param suffix:
        The suffix used by the encoded text. None by default.
    :param _padding:
        (Internal) ``True`` if padding should be included; ``False`` (default)
        otherwise. You should not need to use this--the default value is
        usually the expected value. If you find a need to use this more
        often than not, *tell us* so that we can make this argument public.
    :param _base85_chars:
        (Internal) Character set to use.
    :returns:
        ASCII-85 encoded bytes.
    """
    prefix = prefix or ''
    suffix = suffix or ''

    if not is_bytes(raw_bytes):
        raise TypeError("argument must be raw bytes: got %r" %
                        type(raw_bytes).__name__)

    # We need chunks of 32-bit (4 bytes chunk size) unsigned integers,
    # which means the length of the byte sequence must be divisible by 4.
    # Ensures length by appending additional padding zero bytes if required.
    # ceil_div(length, 4).
    num_uint32, remainder = divmod(len(raw_bytes), 4)
    if remainder:
        padding_size = 4 - remainder
        raw_bytes += '\x00' * padding_size
        num_uint32 += 1
    else:
        padding_size = 0

    ascii_chars = []
    # Ascii85 uses a big-endian convention.
    # See: http://en.wikipedia.org/wiki/Ascii85
    for x in unpack('>' + 'L' * num_uint32, raw_bytes):
#        chars = list(range(5))
#        for i in reversed(chars):
#            chars[i] = _base85_chars[x % 85]
#            x //= 85
#        ascii_chars.extend(chars)
        # Above loop unrolled:
        ascii_chars.extend((
            _base85_chars[x // 52200625],      # 85**4 = 52200625
            _base85_chars[(x // 614125) % 85], # 85**3 = 614125
            _base85_chars[(x // 7225) % 85],   # 85**2 = 7225
            _base85_chars[(x // 85) % 85],     # 85**1 = 85
            _base85_chars[x % 85],             # 85**0 = 1
        ))
    if padding_size and not _padding:
        # Only as much padding added before encoding is removed after encoding.
        ascii_chars = ascii_chars[:-padding_size]
    encoded = ''.join(ascii_chars).replace('!!!!!', 'z')
    return prefix + encoded + suffix


def b85decode(encoded,
              prefix=None,
              suffix=None,
              _ignore_pattern=WHITESPACE_PATTERN,
              _base85_ords=ASCII85_ORDS):
    """
    Decodes a base85 encoded string into raw bytes.

    :param encoded:
        Encoded ASCII string.
    :param prefix:
        The prefix used by the encoded text. None by default.
    :param suffix:
        The suffix used by the encoded text. None by default.
    :param _ignore_pattern:
        (Internal) By default all whitespace is ignored. This must be an
        ``re.compile()`` instance. You should not need to use this.
    :param _base85_ords:
        (Internal) A function to convert a base85 character to its ordinal
        value. You should not need to use this.
    :returns:
        Base85-decoded raw bytes.
    """
    prefix = prefix or ""
    suffix = suffix or ""

    # Must be US-ASCII, not Unicode.
    encoded = encoded.encode("latin1")

    # ASCII-85 ignores whitespace.
    if _ignore_pattern:
        encoded = re.sub(_ignore_pattern, '', encoded)

    # Strip the prefix and suffix.
    if prefix and encoded.startswith(prefix):
        encoded = encoded[len(prefix):]
    if suffix and encoded.endswith(suffix):
        encoded = encoded[:-len(suffix)]

    # Replace all the 'z' occurrences with '!!!!!'
    encoded = encoded.replace('z', '!!!!!')

    # We want 5-tuple chunks, so pad with as many 'u' characters as
    # required to satisfy the length.
    length = len(encoded)
    num_uint32s, remainder = divmod(length, 5)
    if remainder:
        padding_size = 5 - remainder
        encoded += 'u' * padding_size
        num_uint32s += 1
        length += padding_size
    else:
        padding_size = 0

    uint32s = []
    #for chunk in chunks(encoded, 5):
    for i in range(0, length, 5):
        a, b, c, d, e = chunk = encoded[i:i+5]
        #uint32_value = 0
        #for char in chunk:
        #    uint32_value = uint32_value * 85 + _base85_ord(char)
        # Above loop unrolled:
        try:
            uint32_value = ((((_base85_ords[a] *
                            85 + _base85_ords[b]) *
                            85 + _base85_ords[c]) *
                            85 + _base85_ords[d]) *
                            85 + _base85_ords[e])
        except KeyError:
            raise OverflowError("Cannot decode chunk `%r`" % chunk)
        # Groups of characters that decode to a value greater than 2**32 − 1
        # (encoded as "s8W-!") will cause a decoding error.
        #if uint32_value > 4294967295: # 2**32 - 1
        #    raise OverflowError("Cannot decode chunk `%r`" % chunk)
        # Disabled because the KeyError above is raised when there is an
        # overflow anyway. See tests.
        uint32s.append(uint32_value)


    raw_bytes = pack(">" + "L" * num_uint32s, *uint32s)
    if padding_size:
        # Only as much padding added before decoding is removed after decoding.
        raw_bytes = raw_bytes[:-padding_size]
    return raw_bytes


def rfc1924_b85encode(raw_bytes):
    """
    Base85 encodes using the RFC1924 character set.

    This is the encoding used by Mercurial, for example. They chose the IPv6
    character set and encode using the Adobe encoding method.

    :see: http://tools.ietf.org/html/rfc1924
    :param raw_bytes:
        Raw bytes.
    :returns:
        RFC1924 base85 encoded string.
    """
    return b85encode(raw_bytes, _base85_chars=RFC1924_CHARS)


def rfc1924_b85decode(encoded):
    """
    Base85 decodes using the RFC1924 character set.

    This is the encoding used by Mercurial, for example. They chose the IPv6
    character set and encode using the Adobe encoding method.

    :see: http://tools.ietf.org/html/rfc1924
    :param encoded:
        RFC1924 Base85 encoded string.
    :returns:
        Decoded bytes.
    """
    return b85decode(encoded, _base85_ords=RFC1924_ORDS)


def ipv6_b85encode(uint128,
                   _base85_chars=RFC1924_CHARS):
    """
    Encodes a 128-bit unsigned integer using the RFC 1924 base-85 encoding.
    Used to encode IPv6 addresses or 128-bit chunks.

    :param uint128:
        A 128-bit unsigned integer to be encoded.
    :param _base85_chars:
        (Internal) Base85 encoding charset lookup table.
    :returns:
        RFC1924 Base85-encoded string.
    """
    if uint128 < 0:
        raise ValueError("Number is not a 128-bit unsigned integer: got %d" %
                         uint128)
    if uint128 > 340282366920938463463374607431768211455L: # 2**128 - 1
        raise OverflowError("Number is not a 128-bit unsigned integer: %d" %
                            uint128)
    encoded = list(range(20))
    for i in reversed(encoded):
        encoded[i] = _base85_chars[uint128 % 85]
        uint128 //= 85
    return ''.join(encoded)


def ipv6_b85decode(encoded,
                   _base85_ords=RFC1924_ORDS,
                   _whitespace=WHITESPACE_CHARS):
    """
    Decodes an RFC1924 Base-85 encoded string to its 128-bit unsigned integral
    representation. Used to base85-decode IPv6 addresses or 128-bit chunks.

    :param encoded:
        RFC1924 Base85-encoded string.
    :param _base85_ords:
        (Internal) Look up table.
    :param _whitespace:
        (Internal) Whitespace characters.
    :returns:
        A 128-bit unsigned integer.
    """
    encoded = encoded.encode("latin1")
    if len(encoded) != 20:
        raise ValueError(
            "Encoded IPv6 value must be exactly 20 characters long: got %r" %
            encoded
        )
    uint128 = 0L
    for char in encoded:
        if char in _whitespace:
            raise ValueError("Whitespace is not allowed in encoded strings.")
        uint128 = uint128 * 85 + _base85_ords[char]
    return uint128
