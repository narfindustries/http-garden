import dataclasses
import itertools

from typing import Self, Iterator, Iterable

from hpack import HPACKState

DEFAULT_FRAME_TYPES: dict[int, str] = {
    0: "H2FrameType.data",
    1: "H2FrameType.headers",
    2: "H2FrameType.priority",
    3: "H2FrameType.rst_stream",
    4: "H2FrameType.settings",
    5: "H2FrameType.push_promise",
    6: "H2FrameType.ping",
    7: "H2FrameType.goaway",
    8: "H2FrameType.windowupdate",
    9: "H2FrameType.continuation",
}


@dataclasses.dataclass
class H2FrameType:
    val: int

    @classmethod
    def data(cls) -> "H2FrameType":
        return H2FrameType(0)

    @classmethod
    def headers(cls) -> "H2FrameType":
        return H2FrameType(1)

    @classmethod
    def priority(cls) -> "H2FrameType":
        return H2FrameType(2)

    @classmethod
    def rst_stream(cls) -> "H2FrameType":
        return H2FrameType(3)

    @classmethod
    def settings(cls) -> "H2FrameType":
        return H2FrameType(4)

    @classmethod
    def push_promise(cls) -> "H2FrameType":
        return H2FrameType(5)

    @classmethod
    def ping(cls) -> "H2FrameType":
        return H2FrameType(6)

    @classmethod
    def goaway(cls) -> "H2FrameType":
        return H2FrameType(7)

    @classmethod
    def windowupdate(cls) -> "H2FrameType":
        return H2FrameType(8)

    @classmethod
    def continuation(cls) -> "H2FrameType":
        return H2FrameType(9)

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
        assert len(self.payload) < 1 << 24

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
        assert self.padding is None or len(self.padding) < 0x100

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2DataFrame":
        assert frame.typ == H2FrameType.data()
        length: int = len(frame.payload)
        flags: H2Flags = H2Flags(padded=frame.flags.padded, end_stream_or_ack=frame.flags.end_stream_or_ack)
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

    def to_h2frame(self: Self) -> H2Frame:
        payload: bytes = self.data
        if self.flags.padded:
            assert self.padding is not None
            payload = bytes([len(self.padding)]) + payload + self.padding
        return H2Frame(H2FrameType.data(), self.flags, False, self.stream_id, payload)


@dataclasses.dataclass
class H2HeadersFrame:
    """H2 headers frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    exclusive: bool | None = None
    stream_dependency: int | None = None
    weight: int | None = None
    field_block_fragment: bytes = b""
    padding: bytes | None = None

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        if self.flags.priority:
            assert self.exclusive is not None
            assert self.weight is not None and 0 <= self.weight < 0x100
            assert self.stream_dependency is not None and (0 <= self.stream_dependency < 1 << 31)
        else:
            assert self.exclusive is self.stream_dependency is self.weight is None
        assert self.padding is None or (len(self.padding) < 1 << 8 and self.flags.padded)

    @classmethod
    def from_h2frame(cls, frame: H2Frame, state: HPACKState | None = None) -> "H2HeadersFrame":
        assert frame.typ == H2FrameType.headers()
        if state is None:
            state = HPACKState()
        length: int = len(frame.payload)
        stream_id: int = frame.stream_id
        flags: H2Flags = H2Flags(priority=frame.flags.priority, padded=frame.flags.padded, end_headers=frame.flags.end_headers, end_stream_or_ack=frame.flags.end_stream_or_ack)
        inp: Iterator[int] = iter(frame.payload)
        pad_length: int | None = next(inp) if flags.padded else None
        raw_stream_dependency: int | None = int.from_bytes(bytes(itertools.islice(inp, 4)), "big") if flags.priority else None
        stream_dependency: int | None = None if raw_stream_dependency is None else raw_stream_dependency & ~(1 << 31)
        exclusive: bool | None = None if raw_stream_dependency is None else bool(raw_stream_dependency >> 31)
        weight: int | None = next(inp) if flags.priority else None
        field_block_fragment: bytes = bytes(itertools.islice(inp, length - (pad_length + 1 if pad_length is not None else 0) - (5 if flags.priority else 0)))
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

@dataclasses.dataclass
class H2RstStreamFrame:
    """H2 rst_stream frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    error_code: int = 0

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        assert 0 <= self.error_code < 1 << 32

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2RstStreamFrame":
        assert frame.typ == H2FrameType.rst_stream()
        assert len(frame.payload) == 4

        stream_id: int = frame.stream_id
        error_code: int = int.from_bytes(frame.payload, "big")

        return cls(
            stream_id=stream_id,
            error_code=error_code,
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.rst_stream(), H2Flags(), False, self.stream_id, self.error_code.to_bytes(4, "big"))

@dataclasses.dataclass
class H2PriorityFrame:
    """H2 priority frame class. Only needs to represent valid frames."""
    stream_id: int = 0
    exclusive: bool = False
    stream_dependency: int = 0
    weight: int = 0

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        assert 0 <= self.stream_dependency < 1 << 31
        assert 0 <= self.weight < 1 << 8

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2PriorityFrame":
        assert frame.typ == H2FrameType.priority()
        assert len(frame.payload) == 5

        stream_id: int = frame.stream_id
        exclusive: bool = bool(frame.payload[0] >> 7)
        stream_dependency: int = int.from_bytes(frame.payload[:4], "big") & ~(1 << 31)
        weight: int = frame.payload[4]

        return cls(
            stream_id=stream_id,
            exclusive=exclusive,
            stream_dependency=stream_dependency,
            weight=weight,
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.priority(), H2Flags(), False, self.stream_id, ((self.exclusive << 31) | self.stream_dependency).to_bytes(4, "big") + bytes([self.weight]))

@dataclasses.dataclass
class H2PingFrame:
    """H2 ping frame class. Only needs to represent valid frames."""
    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    opaque_data: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00"

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2PingFrame":
        assert frame.typ == H2FrameType.ping()
        assert len(frame.payload) == 8
        assert frame.stream_id == 0

        return cls(
            flags=H2Flags(end_stream_or_ack=frame.flags.end_stream_or_ack),
            opaque_data=frame.payload,
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.ping(), self.flags, False, 0, self.opaque_data)

@dataclasses.dataclass
class H2GoAwayFrame:
    """H2 goaway frame class. Only needs to represent valid frames."""
    last_stream_id: int = 0
    error_code: int = 0
    additional_debug_data: bytes = b""

    def __post_init__(self: Self):
        assert 0 <= self.last_stream_id < 1 << 31
        assert 0 <= self.error_code < 1 << 32

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2GoAwayFrame":
        assert frame.typ == H2FrameType.goaway()
        assert frame.stream_id == 0
        assert len(frame.payload) >= 8

        last_stream_id: int = int.from_bytes(frame.payload[:4], "big") & ~(1 << 31)
        error_code: int = int.from_bytes(frame.payload[4:8], "big")
        additional_debug_data: bytes = frame.payload[8:]

        return cls(
            last_stream_id=last_stream_id,
            error_code=error_code,
            additional_debug_data=additional_debug_data,
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.goaway(), H2Flags(), False, 0, self.last_stream_id.to_bytes(4, "big") + self.error_code.to_bytes(4, "big") + self.additional_debug_data)

@dataclasses.dataclass
class H2WindowUpdateFrame:
    """H2 windowupdate frame class. Only needs to represent valid frames."""
    stream_id: int = 0
    window_size_increment: int = 0

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2WindowUpdateFrame":
        assert frame.typ == H2FrameType.windowupdate()
        assert len(frame.payload) == 4

        return cls(
            stream_id=frame.stream_id,
            window_size_increment=int.from_bytes(frame.payload, "big") & ~(1 << 31),
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.windowupdate(), H2Flags(), False, self.stream_id, self.window_size_increment.to_bytes(4, "big"))

@dataclasses.dataclass
class H2SettingsFrame:
    """H2 settings frame class. Only needs to represent valid frames."""
    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    settings: list[tuple[int, int]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_h2frame(cls, frame: H2Frame) -> "H2SettingsFrame":
        assert frame.typ == H2FrameType.settings()
        assert frame.stream_id == 0
        assert len(frame.payload) % 6 == 0
        return cls(
            flags=H2Flags(end_stream_or_ack=frame.flags.end_stream_or_ack),
            settings=[(int.from_bytes(frame.payload[i : i + 2], "big"), int.from_bytes(frame.payload[i + 2 : i + 6], "big")) for i in range(0, len(frame.payload), 6)],
        )

    def to_h2frame(self: Self) -> H2Frame:
        return H2Frame(H2FrameType.settings(), self.flags, False, 0, b"".join(map(lambda s: s[0].to_bytes(2, "big") + s[1].to_bytes(4, "big"), self.settings)))
