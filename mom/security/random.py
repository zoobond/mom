#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Trevor Perrin <trevp@trevp.net>
# Copyright (C) 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: mom.security.random
:synopsis: Random number, string, and bytearray generation utilities.

Bytes and byte arrays
---------------------
.. autofunction:: generate_random_bytes
.. autofunction:: generate_random_bytearray

Numbers
-------
.. autofunction:: generate_random_long

Strings
-------
.. autofunction:: generate_random_uint_string
.. autofunction:: generate_random_hex_string
"""

from __future__ import absolute_import

import os
from mom.builtins import long_byte_count, long_bit_length
from mom._types.bytearray import \
    bytearray_to_long, bytes_to_bytearray
from mom.codec import \
    bytes_to_bin, \
    bytes_to_base64, \
    bytes_to_decimal, \
    bytes_to_hex


try:
    # Operating system unsigned random.
    os.urandom(1)
    def generate_random_bytes(count):
        """
        Generates a random byte string with ``count`` bytes.

        :param count:
            Number of bytes.
        :returns:
            Random byte string.
        """
        return os.urandom(count)
except AttributeError:
    try:
        __urandom_device__ = open("/dev/urandom", "rb")
        def generate_random_bytes(count):
            """
            Generates a random byte string with ``count`` bytes.

            :param count:
                Number of bytes.
            :returns:
                Random byte string.
            """
            return __urandom_device__.read(count)
    except IOError:
        #Else get Win32 CryptoAPI PRNG
        try:
            import win32prng
            def generate_random_bytes(count):
                """
                Generates a random byte string with ``count`` bytes.

                :param count:
                    Number of bytes.
                :returns:
                    Random byte string.
                """
                random_bytes = win32prng.generate_random_bytes(count)
                assert len(random_bytes) == count
                return random_bytes
        except ImportError:
            # What the fuck?!
            def generate_random_bytes(_):
                """
                WTF.

                :returns:
                    WTF.
                """
                raise NotImplementedError("What the fuck?! No PRNG available.")


def generate_random_long(low, high):
    """
    Generates a random long integer.

    :param low:
        Low
    :param high:
        High
    :returns:
        Random long integer value.
    """
    if low >= high:
        raise ValueError("High must be greater than low.")
    num_bits = long_bit_length(high)
    num_bytes = long_byte_count(high)
    last_bits = num_bits % 8
    while 1:
        byte_array = generate_random_bytearray(num_bytes)
        if last_bits:
            byte_array[0] = byte_array[0] % (1 << last_bits)
        num = bytearray_to_long(byte_array)
        if num >= low and num < high:
            return num


_BYTE_BASE_ENCODING_MAP = {
    2:  bytes_to_bin,
    10: bytes_to_decimal,
    16: bytes_to_hex,
    64: bytes_to_base64,
}
def generate_random_uint_string(bit_strength=64, base=10):
    """
    Generates an ASCII-encoded base-representation of a randomly-generated
    unsigned integral number.

    :param bit_strength:
        Bit strength.
    :param base:
        One of:
            1. 2
            2. 10 (default)
            3. 16
            4. 64
    :returns:
        An ASCII-encoded base representation of a randomly-generated
        unsigned integral number based on the bit strength.
    """
    if bit_strength % 8 or bit_strength <= 0:
        raise ValueError(
            "This function expects a bit strength: got `%r`." % bit_strength)
    random_bytes = generate_random_bytes(bit_strength // 8)
    try:
        return _BYTE_BASE_ENCODING_MAP[base](random_bytes)
    except KeyError:
        raise ValueError(
            "Base must be one of %r" % _BYTE_BASE_ENCODING_MAP.keys())


def generate_random_hex_string(length=8):
    """
    Generates a random ASCII-encoded hexadecimal string of an even length.

    :param length:
        Length of the string to be returned. Default 32.
        The length MUST be a positive even number.
    :returns:
        A string representation of a randomly-generated hexadecimal string.
    """
    #if length % 2 or length <= 0:
    if length & 1 or length <= 0:
        raise ValueError(
            "This function expects a positive even number "\
            "length: got length `%r`." % length)
    return bytes_to_hex(generate_random_bytes(length/2))


def generate_random_bytearray(count):
    """
    Generates a random byte array.

    :param count:
        The number of bytes.
    :returns:
        A random byte array.
    """
    return bytes_to_bytearray(generate_random_bytes(count))