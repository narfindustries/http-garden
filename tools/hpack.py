import itertools
import functools
import dataclasses
from collections import deque
from typing import Iterable, Self, Final, ClassVar
from enum import Enum

from util import to_bits


# From RFC 7541, Appendix B
HUFFMAN_CODEWORDS: Final[tuple[tuple[bool, ...], ...]] = tuple(
    tuple(bool(int(c)) for c in s)
    for s in (
        "1111111111000",
        "11111111111111111011000",
        "1111111111111111111111100010",
        "1111111111111111111111100011",
        "1111111111111111111111100100",
        "1111111111111111111111100101",
        "1111111111111111111111100110",
        "1111111111111111111111100111",
        "1111111111111111111111101000",
        "111111111111111111101010",
        "111111111111111111111111111100",
        "1111111111111111111111101001",
        "1111111111111111111111101010",
        "111111111111111111111111111101",
        "1111111111111111111111101011",
        "1111111111111111111111101100",
        "1111111111111111111111101101",
        "1111111111111111111111101110",
        "1111111111111111111111101111",
        "1111111111111111111111110000",
        "1111111111111111111111110001",
        "1111111111111111111111110010",
        "111111111111111111111111111110",
        "1111111111111111111111110011",
        "1111111111111111111111110100",
        "1111111111111111111111110101",
        "1111111111111111111111110110",
        "1111111111111111111111110111",
        "1111111111111111111111111000",
        "1111111111111111111111111001",
        "1111111111111111111111111010",
        "1111111111111111111111111011",
        "010100",
        "1111111000",
        "1111111001",
        "111111111010",
        "1111111111001",
        "010101",
        "11111000",
        "11111111010",
        "1111111010",
        "1111111011",
        "11111001",
        "11111111011",
        "11111010",
        "010110",
        "010111",
        "011000",
        "00000",
        "00001",
        "00010",
        "011001",
        "011010",
        "011011",
        "011100",
        "011101",
        "011110",
        "011111",
        "1011100",
        "11111011",
        "111111111111100",
        "100000",
        "111111111011",
        "1111111100",
        "1111111111010",
        "100001",
        "1011101",
        "1011110",
        "1011111",
        "1100000",
        "1100001",
        "1100010",
        "1100011",
        "1100100",
        "1100101",
        "1100110",
        "1100111",
        "1101000",
        "1101001",
        "1101010",
        "1101011",
        "1101100",
        "1101101",
        "1101110",
        "1101111",
        "1110000",
        "1110001",
        "1110010",
        "11111100",
        "1110011",
        "11111101",
        "1111111111011",
        "1111111111111110000",
        "1111111111100",
        "11111111111100",
        "100010",
        "111111111111101",
        "00011",
        "100011",
        "00100",
        "100100",
        "00101",
        "100101",
        "100110",
        "100111",
        "00110",
        "1110100",
        "1110101",
        "101000",
        "101001",
        "101010",
        "00111",
        "101011",
        "1110110",
        "101100",
        "01000",
        "01001",
        "101101",
        "1110111",
        "1111000",
        "1111001",
        "1111010",
        "1111011",
        "111111111111110",
        "11111111100",
        "11111111111101",
        "1111111111101",
        "1111111111111111111111111100",
        "11111111111111100110",
        "1111111111111111010010",
        "11111111111111100111",
        "11111111111111101000",
        "1111111111111111010011",
        "1111111111111111010100",
        "1111111111111111010101",
        "11111111111111111011001",
        "1111111111111111010110",
        "11111111111111111011010",
        "11111111111111111011011",
        "11111111111111111011100",
        "11111111111111111011101",
        "11111111111111111011110",
        "111111111111111111101011",
        "11111111111111111011111",
        "111111111111111111101100",
        "111111111111111111101101",
        "1111111111111111010111",
        "11111111111111111100000",
        "111111111111111111101110",
        "11111111111111111100001",
        "11111111111111111100010",
        "11111111111111111100011",
        "11111111111111111100100",
        "111111111111111011100",
        "1111111111111111011000",
        "11111111111111111100101",
        "1111111111111111011001",
        "11111111111111111100110",
        "11111111111111111100111",
        "111111111111111111101111",
        "1111111111111111011010",
        "111111111111111011101",
        "11111111111111101001",
        "1111111111111111011011",
        "1111111111111111011100",
        "11111111111111111101000",
        "11111111111111111101001",
        "111111111111111011110",
        "11111111111111111101010",
        "1111111111111111011101",
        "1111111111111111011110",
        "111111111111111111110000",
        "111111111111111011111",
        "1111111111111111011111",
        "11111111111111111101011",
        "11111111111111111101100",
        "111111111111111100000",
        "111111111111111100001",
        "1111111111111111100000",
        "111111111111111100010",
        "11111111111111111101101",
        "1111111111111111100001",
        "11111111111111111101110",
        "11111111111111111101111",
        "11111111111111101010",
        "1111111111111111100010",
        "1111111111111111100011",
        "1111111111111111100100",
        "11111111111111111110000",
        "1111111111111111100101",
        "1111111111111111100110",
        "11111111111111111110001",
        "11111111111111111111100000",
        "11111111111111111111100001",
        "11111111111111101011",
        "1111111111111110001",
        "1111111111111111100111",
        "11111111111111111110010",
        "1111111111111111101000",
        "1111111111111111111101100",
        "11111111111111111111100010",
        "11111111111111111111100011",
        "11111111111111111111100100",
        "111111111111111111111011110",
        "111111111111111111111011111",
        "11111111111111111111100101",
        "111111111111111111110001",
        "1111111111111111111101101",
        "1111111111111110010",
        "111111111111111100011",
        "11111111111111111111100110",
        "111111111111111111111100000",
        "111111111111111111111100001",
        "11111111111111111111100111",
        "111111111111111111111100010",
        "111111111111111111110010",
        "111111111111111100100",
        "111111111111111100101",
        "11111111111111111111101000",
        "11111111111111111111101001",
        "1111111111111111111111111101",
        "111111111111111111111100011",
        "111111111111111111111100100",
        "111111111111111111111100101",
        "11111111111111101100",
        "111111111111111111110011",
        "11111111111111101101",
        "111111111111111100110",
        "1111111111111111101001",
        "111111111111111100111",
        "111111111111111101000",
        "11111111111111111110011",
        "1111111111111111101010",
        "1111111111111111101011",
        "1111111111111111111101110",
        "1111111111111111111101111",
        "111111111111111111110100",
        "111111111111111111110101",
        "11111111111111111111101010",
        "11111111111111111110100",
        "11111111111111111111101011",
        "111111111111111111111100110",
        "11111111111111111111101100",
        "11111111111111111111101101",
        "111111111111111111111100111",
        "111111111111111111111101000",
        "111111111111111111111101001",
        "111111111111111111111101010",
        "111111111111111111111101011",
        "1111111111111111111111111110",
        "111111111111111111111101100",
        "111111111111111111111101101",
        "111111111111111111111101110",
        "111111111111111111111101111",
        "111111111111111111111110000",
        "11111111111111111111101110",
        "111111111111111111111111111111",
    )
)
EOS: Final[int] = 256

_huffman_tree_t = None | int | list["_huffman_tree_t"]
_huffman_tree: _huffman_tree_t = [None, None]


def _build_huffman_tree() -> None:
    for i, codeword in enumerate(HUFFMAN_CODEWORDS):
        path: _huffman_tree_t = _huffman_tree
        for bit in codeword[:-1]:
            assert isinstance(path, list)
            if path[bit] is None:
                path[bit] = [None, None]
            path = path[bit]
        last_bit: bool = codeword[-1]
        assert isinstance(path, list)
        path[last_bit] = i


_build_huffman_tree()


STATIC_TABLE: Final[tuple[tuple[bytes, bytes], ...]] = (
    (b":authority", b""),
    (b":method", b"GET"),
    (b":method", b"POST"),
    (b":path", b"/"),
    (b":path", b"/index.html"),
    (b":scheme", b"http"),
    (b":scheme", b"https"),
    (b":status", b"200"),
    (b":status", b"204"),
    (b":status", b"206"),
    (b":status", b"304"),
    (b":status", b"400"),
    (b":status", b"404"),
    (b":status", b"500"),
    (b"accept-charset", b""),
    (b"accept-encoding", b"gzip, deflate"),
    (b"accept-language", b""),
    (b"accept-ranges", b""),
    (b"accept", b""),
    (b"access-control-allow-origin", b""),
    (b"age", b""),
    (b"allow", b""),
    (b"authorization", b""),
    (b"cache-control", b""),
    (b"content-disposition", b""),
    (b"content-encoding", b""),
    (b"content-language", b""),
    (b"content-length", b""),
    (b"content-location", b""),
    (b"content-range", b""),
    (b"content-type", b""),
    (b"cookie", b""),
    (b"date", b""),
    (b"etag", b""),
    (b"expect", b""),
    (b"expires", b""),
    (b"from", b""),
    (b"host", b""),
    (b"if-match", b""),
    (b"if-modified-since", b""),
    (b"if-none-match", b""),
    (b"if-range", b""),
    (b"if-unmodified-since", b""),
    (b"last-modified", b""),
    (b"link", b""),
    (b"location", b""),
    (b"max-forwards", b""),
    (b"proxy-authenticate", b""),
    (b"proxy-authorization", b""),
    (b"range", b""),
    (b"referer", b""),
    (b"refresh", b""),
    (b"retry-after", b""),
    (b"server", b""),
    (b"set-cookie", b""),
    (b"strict-transport-security", b""),
    (b"transfer-encoding", b""),
    (b"user-agent", b""),
    (b"vary", b""),
    (b"via", b""),
    (b"www-authenticate", b""),
)


class HPACKError(Exception):
    pass


def _parse_hpack_int(data: Iterable[int], prefix_len: int) -> int:
    assert 1 <= prefix_len <= 8
    data = iter(data)
    try:
        prefix_byte: int = next(data)
    except StopIteration as e:
        raise HPACKError("Unexpected end of HPACKInt data") from e
    prefix_mask: int = (1 << prefix_len) - 1
    result: int = prefix_byte & prefix_mask
    if result != prefix_mask:
        return result

    m: int = 0
    for b in data:
        result += (b & 0x7F) * (1 << m)
        m += 7
        if ((b >> 7) & 1) == 0:
            break
    else:
        raise HPACKError("Unexpected end of HPACKInt data")
    return result


@dataclasses.dataclass
class HPACKInt:
    val: int
    prefix_len: ClassVar[int]
    padding_amount: int

    def __post_init__(self: Self):
        assert False # This is never to be constructed

    def to_bytes(self: Self, preprefix: int = 0) -> bytes:
        if not 0 <= preprefix < (1 << (8 - self.prefix_len)):
            raise HPACKError("Invalid HPACKInt preprefix")

        val: int = self.val
        if val < ((1 << self.prefix_len) - 1):
            if self.padding_amount != 0:
                raise HPACKError("Cannot zero-pad an HPACKInt that fits in the prefix")
            return bytes([(preprefix << self.prefix_len) | val])

        result: list[int] = [(preprefix << self.prefix_len) | ((1 << self.prefix_len) - 1)]
        val -= (1 << self.prefix_len) - 1
        while val >= 128:
            result.append(0x80 | (val & 0x7F))
            val //= 128
        result.append(val)
        if self.padding_amount != 0:
            result[-1] |= 0x80
            result += [0x80] * (self.padding_amount - 1) + [0]
        return bytes(result)


@dataclasses.dataclass
class HPACKInt4(HPACKInt):
    val: int
    padding_amount: int = 0
    prefix_len: ClassVar[int] = 4

    @classmethod
    def parse(cls, data: Iterable[int]) -> "Self":
        return cls(_parse_hpack_int(data, cls.prefix_len))

    def __post_init__(self) -> None:
        assert self.prefix_len == 4

@dataclasses.dataclass
class HPACKInt5(HPACKInt):
    val: int
    padding_amount: int = 0
    prefix_len: ClassVar[int] = 5

    @classmethod
    def parse(cls, data: Iterable[int]) -> "Self":
        return cls(_parse_hpack_int(data, cls.prefix_len))

    def __post_init__(self) -> None:
        assert self.prefix_len == 5

@dataclasses.dataclass
class HPACKInt6(HPACKInt):
    val: int
    padding_amount: int = 0
    prefix_len: ClassVar[int] = 6

    @classmethod
    def parse(cls, data: Iterable[int]) -> "Self":
        return cls(_parse_hpack_int(data, cls.prefix_len))

    def __post_init__(self) -> None:
        assert self.prefix_len == 6

@dataclasses.dataclass
class HPACKInt7(HPACKInt):
    val: int
    padding_amount: int = 0
    prefix_len: ClassVar[int] = 7

    @classmethod
    def parse(cls, data: Iterable[int]) -> "Self":
        return cls(_parse_hpack_int(data, cls.prefix_len))

    def __post_init__(self) -> None:
        assert self.prefix_len == 7

@dataclasses.dataclass
class HPACKString:
    data: bytes
    compressed: bool = False
    length: HPACKInt7 | None = None
    padding: list[bool] | None = None  # None -> pad with 1s until len % 8 == 0

    @classmethod
    def parse(cls, data: Iterable[int]) -> "HPACKString":
        data = iter(data)
        try:
            prefix_byte: int = next(data)
        except StopIteration as e:
            raise HPACKError("Unexpected end of data in HPACKString") from e
        data = itertools.chain(iter([prefix_byte]), data)

        compressed: bool = bool(prefix_byte & 0x80)
        length: int = HPACKInt7.parse(data).val
        raw_result: bytes = bytes(itertools.islice(data, length))
        if len(raw_result) != length:
            raise HPACKError("Unexpected end of HPACKString data")
        if not compressed:
            return cls(raw_result)

        result: list[int] = []
        path: _huffman_tree_t = _huffman_tree
        codeword: list[bool] = []  # We only track this to check padding
        for byte in raw_result:
            for bit in to_bits(byte):
                codeword.append(bit)
                assert isinstance(path, list)
                path = path[bit]
                if isinstance(path, int):
                    # A Huffman-encoded string literal containing the EOS symbol
                    # MUST be treated as a decoding error.
                    if path == EOS:
                        raise HPACKError("Encountered EOS during Huffman decoding")
                    result.append(path)
                    path = _huffman_tree
                    codeword = []
        #   As the Huffman-encoded data doesn't always end at an octet boundary,
        #   some padding is inserted after it, up to the next octet boundary.  To
        #   prevent this padding from being misinterpreted as part of the string
        #   literal, the most significant bits of the code corresponding to the
        #   EOS (end-of-string) symbol are used.
        if not all(b for b in codeword) and len(codeword) <= 7:
            raise HPACKError("Invalid EOS padding")
        return cls(bytes(result), compressed, HPACKInt7(len(result)))

    def to_bytes(self: Self) -> bytes:
        bitstring: list[bool] = []
        for code_point in self.data:
            if self.compressed:
                if not 0 <= code_point <= EOS:
                    raise HPACKError("Invalid code point in compressed HPACKString")
                bitstring.extend(HUFFMAN_CODEWORDS[code_point])
            else:
                if not 0 <= code_point < EOS:
                    raise HPACKError("Invalid code point in uncompressed HPACKString")
                bitstring.extend(to_bits(code_point))
        if self.padding is None:
            while len(bitstring) % 8 > 0:
                bitstring.append(True)
        else:
            bitstring.extend(self.padding)
            while len(bitstring) % 8 > 0:
                bitstring.pop()

        string: bytes = bytes(functools.reduce(int.__or__, (bitstring[i * 8 + j] << (7 - j) for j in range(8))) for i in range(len(bitstring) // 8))
        length: HPACKInt7 = HPACKInt7(len(string)) if self.length is None else self.length
        assert length.val == len(string)
        return length.to_bytes(preprefix=int(self.compressed)) + string


@dataclasses.dataclass
class HPACKIndexedHeaderField:
    index: HPACKInt7

    @classmethod
    def from_int(cls, i: int) -> "HPACKIndexedHeaderField":
        return cls(HPACKInt7(i))

    def to_bytes(self: Self) -> bytes:
        return self.index.to_bytes(preprefix=1)


class HPACKHeaderFieldProperty(Enum):
    WITH_DYNAMIC_TABLE = 0
    WITHOUT_DYNAMIC_TABLE = 1
    VERBATIM = 2


@dataclasses.dataclass
class HPACKPartialIndexedHeaderField:
    index: HPACKInt6 | HPACKInt4
    val: HPACKString
    prop: HPACKHeaderFieldProperty

    def __post_init__(self: Self) -> None:
        match self.prop:
            case HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE:
                assert isinstance(self.index, HPACKInt6)
            case HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE | HPACKHeaderFieldProperty.VERBATIM:
                assert isinstance(self.index, HPACKInt4)

    def to_bytes(self: Self) -> bytes:
        match self.prop:
            case HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE:
                return b"".join((self.index.to_bytes(preprefix=0b01), self.val.to_bytes()))
            case HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE:
                return b"".join((self.index.to_bytes(preprefix=0b0000), self.val.to_bytes()))
            case HPACKHeaderFieldProperty.VERBATIM:
                return b"".join((self.index.to_bytes(preprefix=0b0001), self.val.to_bytes()))
        assert False


@dataclasses.dataclass
class HPACKLiteralHeaderField:
    key: HPACKString
    val: HPACKString
    prop: HPACKHeaderFieldProperty = HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE

    def to_bytes(self: Self) -> bytes:
        match self.prop:
            case HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE:
                return b"".join((b"\x40", self.key.to_bytes(), self.val.to_bytes()))
            case HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE:
                return b"".join((b"\x00", self.key.to_bytes(), self.val.to_bytes()))
            case HPACKHeaderFieldProperty.VERBATIM:
                return b"".join((b"\x10", self.key.to_bytes(), self.val.to_bytes()))
        assert False


@dataclasses.dataclass
class HPACKDynamicTableSizeUpdateField:
    size: HPACKInt5

    @classmethod
    def from_int(cls, i: int) -> "HPACKDynamicTableSizeUpdateField":
        return cls(HPACKInt5(i))

    def to_bytes(self: Self) -> bytes:
        return self.size.to_bytes(preprefix=1)


HPACKField = HPACKIndexedHeaderField | HPACKPartialIndexedHeaderField | HPACKLiteralHeaderField | HPACKDynamicTableSizeUpdateField


def parse_hpack_field(data: Iterable[int]) -> HPACKField:
    data = iter(data)
    prefix_byte: int = next(data)
    data = itertools.chain(iter([prefix_byte]), data)

    if prefix_byte & 0b10000000 == 0b10000000:
        return HPACKIndexedHeaderField(HPACKInt7.parse(data))
    if prefix_byte & 0b11000000 == 0b01000000:
        index6: HPACKInt6 = HPACKInt6.parse(data)
        if index6.val == 0:
            return HPACKLiteralHeaderField(HPACKString.parse(data), HPACKString.parse(data), HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE)
        return HPACKPartialIndexedHeaderField(index6, HPACKString.parse(data), HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE)
    if prefix_byte & 0b11110000 == 0b00000000:
        index4:HPACKInt4 = HPACKInt4.parse(data)
        if index4.val == 0:
            return HPACKLiteralHeaderField(HPACKString.parse(data), HPACKString.parse(data), HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE)
        return HPACKPartialIndexedHeaderField(index4, HPACKString.parse(data), HPACKHeaderFieldProperty.WITHOUT_DYNAMIC_TABLE)
    if prefix_byte & 0b11110000 == 0b00010000:
        index4 = HPACKInt4.parse(data)
        if index4.val == 0:
            return HPACKLiteralHeaderField(HPACKString.parse(data), HPACKString.parse(data), HPACKHeaderFieldProperty.VERBATIM)
        return HPACKPartialIndexedHeaderField(index4, HPACKString.parse(data), HPACKHeaderFieldProperty.VERBATIM)
    if prefix_byte & 0b11100000 == 0b00100000:
        return HPACKDynamicTableSizeUpdateField(HPACKInt5.parse(data))
    assert False


def parse_field_block(data: Iterable[int]) -> list[HPACKField]:
    """Consumes the whole iterator."""

    result: list[HPACKField] = []
    it = iter(data)
    while True:
        try:
            result.append(parse_hpack_field(it))
        except StopIteration:
            break
    return result


@dataclasses.dataclass
class HPACKState:
    table_capacity: int = 4096  # How many bytes to use in the dynamic table before eviction happens.
    max_table_capacity: int = 4096  # The maximum allowable value for table_capacity.
    dynamic_table: deque[tuple[bytes, bytes]] = dataclasses.field(default_factory=deque)

    def __post_init__(self: Self) -> None:
        assert 0 <= self.table_size() <= self.table_capacity <= self.max_table_capacity

    def maybe_evict_from_table(self: Self) -> None:
        while self.table_size() > self.table_capacity:
            self.dynamic_table.pop()

    def add_header_to_dynamic_table(self: Self, header: tuple[bytes, bytes]) -> None:
        self.dynamic_table.appendleft(header)
        self.maybe_evict_from_table()

    def get_header(self: Self, index: int) -> tuple[bytes, bytes]:
        assert index > 0
        index -= 1
        if index < len(STATIC_TABLE):
            return STATIC_TABLE[index]
        index -= len(STATIC_TABLE)
        assert index < len(self.dynamic_table)
        return self.dynamic_table[index]

    def get_header_name(self: Self, index: int) -> bytes:
        return self.get_header(index)[0]

    def update_table_capacity(self: Self, val: int) -> None:
        self.table_capacity = val
        self.maybe_evict_from_table()
        self.__post_init__()

    def table_size(self: Self) -> int:
        return sum(len(k) + len(v) + 32 for k, v in self.dynamic_table)

    def process_field_block(self: Self, field_block: list[HPACKField]) -> list[tuple[bytes, bytes]]:
        result: list[tuple[bytes, bytes]] = []
        for field in field_block:
            if isinstance(field, HPACKIndexedHeaderField):
                result.append(self.get_header(field.index.val))
            elif isinstance(field, HPACKLiteralHeaderField):
                result.append((field.key.data, field.val.data))
                if field.prop == HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE:
                    self.add_header_to_dynamic_table((field.key.data, field.val.data))
            elif isinstance(field, HPACKPartialIndexedHeaderField):
                result.append((self.get_header_name(field.index.val), field.val.data))
                if field.prop == HPACKHeaderFieldProperty.WITH_DYNAMIC_TABLE:
                    self.add_header_to_dynamic_table((self.get_header_name(field.index.val), field.val.data))
            elif isinstance(field, HPACKDynamicTableSizeUpdateField):
                self.update_table_capacity(field.size.val)
        return result
