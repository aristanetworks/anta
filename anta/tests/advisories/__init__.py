# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Security advisory tests and their built-in ANTA catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta.catalog import AntaCatalog
from anta.tests.advisories.sa_117 import SA117
from anta.tests.advisories.sa_140 import SA140
from anta.tests.advisories.sa_142 import SA142
from anta.tests.advisories.sa_146 import SA146
from anta.tests.advisories.sa_147 import SA147
from anta.tests.advisories.sa_149 import SA149
from anta.tests.advisories.sa_150 import SA150
from anta.tests.advisories.sa_151 import SA151
from anta.tests.advisories.sa_152 import SA152
from anta.tests.advisories.sa_153 import SA153
from anta.tests.advisories.sa_154 import SA154
from anta.tests.advisories.sa_155 import SA155
from anta.tests.advisories.sa_156 import SA156
from anta.tests.advisories.sa_157 import SA157
from anta.tests.advisories.sa_158 import SA158
from anta.tests.advisories.sa_159 import SA159
from anta.tests.advisories.sa_160 import SA160
from anta.tests.advisories.sa_161 import SA161
from anta.tests.advisories.sa_162 import SA162
from anta.tests.advisories.sa_163 import SA163
from anta.tests.advisories.sa_164 import SA164
from anta.tests.advisories.sa_165 import SA165
from anta.tests.advisories.sa_166 import SA166
from anta.tests.advisories.sa_167 import SA167
from anta.tests.advisories.sa_168 import SA168
from anta.tests.advisories.sa_169 import SA169
from anta.tests.advisories.sa_170 import SA170
from anta.tests.advisories.sa_171 import SA171
from anta.tests.advisories.sa_172 import SA172
from anta.tests.advisories.sa_173 import SA173
from anta.tests.advisories.sa_174 import SA174
from anta.tests.advisories.sa_175 import SA175
from anta.tests.advisories.sa_176 import SA176
from anta.tests.advisories.sa_177 import SA177
from anta.tests.advisories.sa_178 import SA178
from anta.tests.advisories.sa_201 import SA201
from anta.tests.advisories.sa_205 import SA205
from anta.tests.advisories.sa_206 import SA206
from anta.tests.advisories.sa_207 import SA207
from anta.tests.advisories.sa_208 import SA208
from anta.tests.advisories.sa_209 import SA209
from anta.tests.advisories.sa_210 import SA210
from anta.tests.advisories.sa_211 import SA211
from anta.tests.advisories.sa_212 import SA212
from anta.tests.advisories.sa_213 import SA213
from anta.tests.advisories.sa_214 import SA214
from anta.tests.advisories.sa_215 import SA215
from anta.tests.advisories.sa_216 import SA216
from anta.tests.advisories.sa_217 import SA217
from anta.tests.advisories.sa_218 import SA218
from anta.tests.advisories.sa_219 import SA219
from anta.tests.advisories.sa_220 import SA220
from anta.tests.advisories.sa_221 import SA221
from anta.tests.advisories.sa_222 import SA222
from anta.tests.advisories.sa_223 import SA223
from anta.tests.advisories.sa_224 import SA224
from anta.tests.advisories.sa_225 import SA225

if TYPE_CHECKING:
    from anta._advisory.base import _AntaAdvisoryTest

# Keep this registry explicit: adding an advisory module also requires adding its
# test class here. The default ``anta psirt`` catalog is built from every entry.
_ADVISORY_TESTS: tuple[type[_AntaAdvisoryTest], ...] = tuple(
    cast("type[_AntaAdvisoryTest]", test)
    for test in (
        SA117,
        SA140,
        SA142,
        SA146,
        SA147,
        SA149,
        SA150,
        SA151,
        SA152,
        SA153,
        SA154,
        SA155,
        SA156,
        SA157,
        SA158,
        SA159,
        SA160,
        SA161,
        SA162,
        SA163,
        SA164,
        SA165,
        SA166,
        SA167,
        SA168,
        SA169,
        SA170,
        SA171,
        SA172,
        SA173,
        SA174,
        SA175,
        SA176,
        SA177,
        SA178,
        SA201,
        SA205,
        SA206,
        SA207,
        SA208,
        SA209,
        SA210,
        SA211,
        SA212,
        SA213,
        SA214,
        SA215,
        SA216,
        SA217,
        SA218,
        SA219,
        SA220,
        SA221,
        SA222,
        SA223,
        SA224,
        SA225,
    )
)


def get_catalog() -> AntaCatalog:
    """Return the catalog containing every advisory test installed with ANTA."""
    return AntaCatalog.from_list([(test, None) for test in _ADVISORY_TESTS])


# Public re-exports allow advisory catalogs to use the shorter
# ``anta.tests.advisories`` module path.
__all__ = [
    "SA117",
    "SA140",
    "SA142",
    "SA146",
    "SA147",
    "SA149",
    "SA150",
    "SA151",
    "SA152",
    "SA153",
    "SA154",
    "SA155",
    "SA156",
    "SA157",
    "SA158",
    "SA159",
    "SA160",
    "SA161",
    "SA162",
    "SA163",
    "SA164",
    "SA165",
    "SA166",
    "SA167",
    "SA168",
    "SA169",
    "SA170",
    "SA171",
    "SA172",
    "SA173",
    "SA174",
    "SA175",
    "SA176",
    "SA177",
    "SA178",
    "SA201",
    "SA205",
    "SA206",
    "SA207",
    "SA208",
    "SA209",
    "SA210",
    "SA211",
    "SA212",
    "SA213",
    "SA214",
    "SA215",
    "SA216",
    "SA217",
    "SA218",
    "SA219",
    "SA220",
    "SA221",
    "SA222",
    "SA223",
    "SA224",
    "SA225",
    "get_catalog",
]
