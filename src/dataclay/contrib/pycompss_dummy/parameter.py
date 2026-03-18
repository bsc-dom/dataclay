#!/usr/bin/env python3
#
#  Copyright 2002-2026 Barcelona Supercomputing Center (www.bsc.es)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# -*- coding: utf-8 -*-

"""
PyCOMPSs API - Parameter definitions.

This file contains the classes needed for the parameter definition.
1. DIRECTION.
    - IN
    - OUT
    - INOUT
    - CONCURRENT
    - COMMUTATIVE
    - IN_DELETE
2. TYPE.
    - FILE
    - BOOLEAN
    - STRING
    - INT
    - LONG
    - FLOAT
    - OBJECT
    - COLLECTION
    - DICTIONARY
    - EXTERNAL_PSCO
    - EXTERNAL_STREAM
    - ... (check _DataType generated during installation)
3. IOSTREAM.
    - STDIN
    - STDOUT
    - STDERR
    - UNSPECIFIED
4. PREFIX.
5. ALIASES.
"""

# Numbers match both C and Java enums
class SupportedDirections:  # pylint: disable=too-few-public-methods
    """Used as enum for direction types."""

    IN = 0
    OUT = 1
    INOUT = 2
    CONCURRENT = 3
    COMMUTATIVE = 4
    IN_DELETE = 5


# Numbers match both C and Java enums
class SupportedIoStreams:  # pylint: disable=too-few-public-methods
    """Used as enum for stream types."""

    STDIN = 0
    STDOUT = 1
    STDERR = 2
    UNSPECIFIED = 3


# String that identifies the prefix
class SupportedPrefixes:  # pylint: disable=too-few-public-methods
    """Used as enum for prefix."""

    PREFIX = "null"  # NOSONAR

class SupportedFiles: # pylint: disable=too-few-public-methods
    """Used as enum for prefix."""

    FILE = None
    FILE_IN = None
    FILE_OUT = None
    FILE_INOUT = None
    FILE_CONCURRENT = None
    FILE_COMMUTATIVE = None

DIRECTION = SupportedDirections()
IOSTREAM = SupportedIoStreams()
PREFIX = SupportedPrefixes()
FILES = SupportedFiles()




# Aliases for objects (just direction)
IN = DIRECTION.IN
OUT = DIRECTION.OUT
INOUT = DIRECTION.INOUT
CONCURRENT = DIRECTION.CONCURRENT
COMMUTATIVE = DIRECTION.COMMUTATIVE
IN_DELETE = DIRECTION.IN_DELETE

# Aliases for files with direction
FILE = FILES.FILE
FILE_IN = FILES.FILE_IN
FILE_OUT = FILES.FILE_OUT
FILE_INOUT = FILES.FILE_INOUT
FILE_CONCURRENT = FILES.FILE_CONCURRENT
FILE_COMMUTATIVE = FILES.FILE_COMMUTATIVE

# Aliases for files with stream
FILE_STDIN = None
FILE_STDERR = None
FILE_STDOUT = None

# Aliases for files with direction and stream
FILE_IN_STDIN = None
FILE_IN_STDERR = None
FILE_IN_STDOUT =None
FILE_OUT_STDIN = None
FILE_OUT_STDERR = None
FILE_OUT_STDOUT = None
FILE_INOUT_STDIN = None
FILE_INOUT_STDERR = None
FILE_INOUT_STDOUT = None
FILE_CONCURRENT_STDIN = None
FILE_CONCURRENT_STDERR = None
FILE_CONCURRENT_STDOUT = None
FILE_COMMUTATIVE_STDIN = None
FILE_COMMUTATIVE_STDERR = None
FILE_COMMUTATIVE_STDOUT = None
# Aliases for dirs
DIRECTORY = None
DIRECTORY_IN = None
DIRECTORY_OUT = None
DIRECTORY_INOUT = None

# Aliases for collections
COLLECTION = None
COLLECTION_IN = None
COLLECTION_INOUT = None
COLLECTION_OUT = None
COLLECTION_IN_DELETE = None
COLLECTION_FILE = None
COLLECTION_FILE_IN = None
COLLECTION_FILE_INOUT = None
COLLECTION_FILE_OUT = None

# Aliases for dictionary collections
DICTIONARY = None
DICTIONARY_IN = None
DICTIONARY_INOUT = None
DICTIONARY_OUT = None
DICTIONARY_IN_DELETE = None

# Aliases for streams
STREAM_IN = None
STREAM_OUT = None

# Aliases for std IO streams (just stream direction)
STDIN = IOSTREAM.STDIN
STDOUT = IOSTREAM.STDOUT
STDERR = IOSTREAM.STDERR

# Aliases for parameter definition as dictionary
# - Parameter type
Type = None # pylint: disable=invalid-name
# - Parameter direction
Direction = None  # pylint: disable=invalid-name
# - Parameter stream
StdIOStream = None  # pylint: disable=invalid-name
# - Parameter prefix
Prefix = None # pylint: disable=invalid-name
# - Collection recursive depth
Depth = None # pylint: disable=invalid-name
# - Parameter weight
Weight = None  # pylint: disable=invalid-name
# - Parameter keep rename property
Keep_rename = None  # pylint: disable=invalid-name
# - Enable/disable store in cache
Cache = None  # pylint: disable=invalid-name

# Aliases for collection layout for native mpi tasks
block_count = None  # pylint: disable=invalid-name
block_length = None  # pylint: disable=invalid-name
stride = None # pylint: disable=invalid-name
