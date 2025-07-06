import dataclasses
import itertools

from typing import Self, Iterator, Iterable

from hpack import HPACKState

DEFAULT_FRAME_TYPES: dict[int, str] = {
    0x00: "H2FrameType.data",
    0x01: "H2FrameType.headers",
    0x02: "H2FrameType.priority",
    0x03: "H2FrameType.rst_stream",
    0x04: "H2FrameType.settings",
    0x05: "H2FrameType.push_promise",
    0x06: "H2FrameType.ping",
    0x07: "H2FrameType.goaway",
    0x08: "H2FrameType.windowupdate",
    0x09: "H2FrameType.continuation",
}


@dataclasses.dataclass
class H2FrameType:
    val: int

    @classmethod
    def data(cls) -> "H2FrameType":
        return H2FrameType(0x00)

    @classmethod
    def headers(cls) -> "H2FrameType":
        return H2FrameType(0x01)

    @classmethod
    def priority(cls) -> "H2FrameType":
        return H2FrameType(0x02)

    @classmethod
    def rst_stream(cls) -> "H2FrameType":
        return H2FrameType(0x03)

    @classmethod
    def settings(cls) -> "H2FrameType":
        return H2FrameType(0x04)

    @classmethod
    def push_promise(cls) -> "H2FrameType":
        return H2FrameType(0x05)

    @classmethod
    def ping(cls) -> "H2FrameType":
        return H2FrameType(0x06)

    @classmethod
    def goaway(cls) -> "H2FrameType":
        return H2FrameType(0x07)

    @classmethod
    def windowupdate(cls) -> "H2FrameType":
        return H2FrameType(0x08)

    @classmethod
    def continuation(cls) -> "H2FrameType":
        return H2FrameType(0x09)

    def __post_init__(self: Self):
        assert 0 <= self.val < 1 << 8

    def __repr__(self: Self):
        return DEFAULT_FRAME_TYPES[self.val] if self.val in DEFAULT_FRAME_TYPES else f"H2FrameType({hex(self.val)})"

    @classmethod
    def deserialize(cls, data: bytes | int) -> Self:
        if isinstance(data, bytes):
            assert len(data) == 1
            data = data[0]
        assert isinstance(data, int) and 0 <= data < 2**8
        return cls(data)

    def serialize(self: Self) -> bytes:
        return bytes([self.val])

    def supports_padding(self: Self) -> bool:
        return any(self == t for t in (H2FrameType.data(), H2FrameType.headers(), H2FrameType.push_promise()))


@dataclasses.dataclass
class H2Flags:
    unused7: bool = False
    unused6: bool = False
    priority: bool = False
    unused4: bool = False
    padded: bool = False
    end_headers: bool = False
    unused1: bool = False
    end_stream_or_ack: bool = False

    @classmethod
    def deserialize(cls, data: bytes | int) -> Self:
        if isinstance(data, bytes):
            assert len(data) == 1
            data = data[0]
        assert isinstance(data, int) and 0 <= data < 2**8
        return cls(*(bool((data >> i) & 1) for i in reversed(range(8))))

    def serialize(self: Self) -> bytes:
        return bytes(
            [
                sum(
                    b << i
                    for i, b in enumerate(
                        (
                            self.unused7,
                            self.unused6,
                            self.priority,
                            self.unused4,
                            self.padded,
                            self.end_headers,
                            self.unused1,
                            self.end_stream_or_ack,
                        )
                    )
                )
            ]
        )

    def __repr__(self: Self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{k}={v}' for k, v in self.__dict__.items() if v)})"

    def __bool__(self: Self) -> bool:
        return self.unused7 or self.unused6 or self.priority or self.unused4 or self.padded or self.end_headers or self.unused1 or self.end_stream_or_ack


@dataclasses.dataclass
class H2Frame:
    """Generic H2 Frame class. Should be able to represent any frame, valid or invalid."""

    typ: H2FrameType
    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    reserved: bool = False
    stream_id: int = 0
    payload: bytes = b""

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31

    @classmethod
    def deserialize(cls, inp: Iterable[int]) -> "H2Frame":
        inp = iter(inp)
        length: int = int.from_bytes(bytes(itertools.islice(inp, 3)), "big")
        typ: H2FrameType = H2FrameType.deserialize(next(inp))
        flags: H2Flags = H2Flags.deserialize(next(inp))
        raw_stream_id: int = int.from_bytes(bytes(itertools.islice(inp, 4)), "big")
        reserved: bool = bool(raw_stream_id >> 31)
        payload: bytes = bytes(itertools.islice(inp, length))
        return cls(
            typ=typ,
            flags=flags,
            reserved=reserved,
            stream_id=raw_stream_id & ~(1 << 31),
            payload=payload,
        )

    def serialize(self: Self) -> bytes:
        return len(self.payload).to_bytes(3, "big") + self.typ.serialize() + self.flags.serialize() + ((self.reserved << 31) | self.stream_id).to_bytes(4, "big") + self.payload


@dataclasses.dataclass
class H2DataFrame:
    """H2 data frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    data: bytes = b""
    padding: bytes | None = None

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2DataFrame":
        assert frame.typ == H2FrameType.data()
        length: int = len(frame.payload)
        typ: H2FrameType = frame.typ
        assert typ == H2FrameType.data()
        flags: H2Flags = frame.flags
        stream_id: int = frame.stream_id
        inp: Iterator[int] = iter(frame.payload)
        pad_length: int | None = next(inp) if flags.padded else None
        data: bytes = bytes(itertools.islice(inp, length - (pad_length + 1 if pad_length is not None else 0)))
        padding: bytes | None = bytes(itertools.islice(inp, pad_length)) if pad_length is not None else None

        return cls(
            flags=flags,
            stream_id=stream_id,
            data=data,
            padding=padding,
        )

    def serialize(self: Self) -> bytes:
        payload_len: int = len(self.data)
        if self.padding is not None:
            assert self.flags.padded
            payload_len += 1 + len(self.padding)
        return payload_len.to_bytes(3, "big") + H2FrameType.data().serialize() + self.flags.serialize() + self.stream_id.to_bytes(4, "big") + (bytes([len(self.padding)]) if self.padding is not None else b"") + self.data + (self.padding if self.padding is not None else b"")


@dataclasses.dataclass
class H2HeadersFrame:
    """H2 headers frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    exclusive: bool | None = None
    stream_dependency: int | None = None
    weight: int | None = None
    field_block_fragment: list[tuple[bytes, bytes]] = dataclasses.field(default_factory=list)
    padding: bytes | None = None

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31 and (self.stream_dependency is None or 0 <= self.stream_dependency < 1 << 31) and (self.padding is None or 0 <= len(self.padding) < 1 << 8)

    @classmethod
    def from_h2frame(cls, frame: H2Frame, state: HPACKState | None = None) -> "H2HeadersFrame":
        assert frame.typ == H2FrameType.headers()
        if state is None:
            state = HPACKState()
        length: int = len(frame.payload)
        stream_id: int = frame.stream_id
        flags: H2Flags = frame.flags
        inp: Iterator[int] = iter(frame.payload)
        pad_length: int | None = next(inp) if flags.padded else None
        raw_stream_dependency: int | None = int.from_bytes(bytes(itertools.islice(inp, 4)), "big") if flags.priority else None
        stream_dependency: int | None = None if raw_stream_dependency is None else raw_stream_dependency & ~(1 << 31)
        exclusive: bool | None = None if raw_stream_dependency is None else bool(raw_stream_dependency >> 31)
        weight: int | None = next(inp) if flags.priority else None
        raw_field_block_fragment: bytes = bytes(itertools.islice(inp, length - (pad_length + 1 if pad_length is not None else 0) - (5 if flags.priority else 0)))
        field_block_fragment: list[tuple[bytes, bytes]] = []

        it: Iterator[int] = iter(raw_field_block_fragment)
        while True:
            try:
                entry: tuple[bytes, bytes] | None = state.handle_entry(it)
            except StopIteration:
                break
            if entry is not None:
                field_block_fragment.append(entry)
        padding: bytes | None = bytes(itertools.islice(inp, pad_length)) if pad_length is not None else None

        return cls(
            flags=flags,
            stream_id=stream_id,
            exclusive=exclusive,
            stream_dependency=stream_dependency,
            weight=weight,
            field_block_fragment=field_block_fragment,
            padding=padding,
        )
