import dataclasses
import itertools

from typing import Callable, Self, Iterator, Iterable, ClassVar


class H2Error(Exception):
    pass


class H2ErrorCode(int):
    NO_ERROR: ClassVar[Self]
    PROTOCOL_ERROR: ClassVar[Self]
    INTERNAL_ERROR: ClassVar[Self]
    FLOW_CONTROL_ERROR: ClassVar[Self]
    SETTINGS_TIMEOUT: ClassVar[Self]
    STREAM_CLOSED: ClassVar[Self]
    FRAME_SIZE_ERROR: ClassVar[Self]
    REFUSED_STREAM: ClassVar[Self]
    CANCEL: ClassVar[Self]
    COMPRESSION_ERROR: ClassVar[Self]
    CONNECT_ERROR: ClassVar[Self]
    ENHANCE_YOUR_CALM: ClassVar[Self]
    INADEQUATE_SECURITY: ClassVar[Self]
    HTTP_1_1_REQUIRED: ClassVar[Self]

    def __repr__(self):
        match self:
            case self.NO_ERROR:
                return f"{self.__class__.__name__}.NO_ERROR"
            case self.PROTOCOL_ERROR:
                return f"{self.__class__.__name__}.PROTOCOL_ERROR"
            case self.INTERNAL_ERROR:
                return f"{self.__class__.__name__}.INTERNAL_ERROR"
            case self.FLOW_CONTROL_ERROR:
                return f"{self.__class__.__name__}.FLOW_CONTROL_ERROR"
            case self.SETTINGS_TIMEOUT:
                return f"{self.__class__.__name__}.SETTINGS_TIMEOUT"
            case self.STREAM_CLOSED:
                return f"{self.__class__.__name__}.STREAM_CLOSED"
            case self.FRAME_SIZE_ERROR:
                return f"{self.__class__.__name__}.FRAME_SIZE_ERROR"
            case self.REFUSED_STREAM:
                return f"{self.__class__.__name__}.REFUSED_STREAM"
            case self.CANCEL:
                return f"{self.__class__.__name__}.CANCEL"
            case self.COMPRESSION_ERROR:
                return f"{self.__class__.__name__}.COMPRESSION_ERROR"
            case self.CONNECT_ERROR:
                return f"{self.__class__.__name__}.CONNECT_ERROR"
            case self.ENHANCE_YOUR_CALM:
                return f"{self.__class__.__name__}.ENHANCE_YOUR_CALM"
            case self.INADEQUATE_SECURITY:
                return f"{self.__class__.__name__}.INADEQUATE_SECURITY"
            case self.HTTP_1_1_REQUIRED:
                return f"{self.__class__.__name__}.HTTP_1_1_REQUIRED"
        return f"{self.__class__.__name__}({hex(self)})"

H2ErrorCode.NO_ERROR = H2ErrorCode(0x0)
H2ErrorCode.PROTOCOL_ERROR = H2ErrorCode(0x1)
H2ErrorCode.INTERNAL_ERROR = H2ErrorCode(0x2)
H2ErrorCode.FLOW_CONTROL_ERROR = H2ErrorCode(0x3)
H2ErrorCode.SETTINGS_TIMEOUT = H2ErrorCode(0x4)
H2ErrorCode.STREAM_CLOSED = H2ErrorCode(0x5)
H2ErrorCode.FRAME_SIZE_ERROR = H2ErrorCode(0x6)
H2ErrorCode.REFUSED_STREAM = H2ErrorCode(0x7)
H2ErrorCode.CANCEL = H2ErrorCode(0x8)
H2ErrorCode.COMPRESSION_ERROR = H2ErrorCode(0x9)
H2ErrorCode.CONNECT_ERROR = H2ErrorCode(0xa)
H2ErrorCode.ENHANCE_YOUR_CALM = H2ErrorCode(0xb)
H2ErrorCode.INADEQUATE_SECURITY = H2ErrorCode(0xc)
H2ErrorCode.HTTP_1_1_REQUIRED = H2ErrorCode(0xd)

class H2Setting(int):
    HEADER_TABLE_SIZE: ClassVar[Self]
    ENABLE_PUSH: ClassVar[Self]
    MAX_CONCURRENT_STREAMS: ClassVar[Self]
    INITIAL_WINDOW_SIZE: ClassVar[Self]
    MAX_FRAME_SIZE: ClassVar[Self]
    MAX_HEADER_LIST_SIZE: ClassVar[Self]

    def __repr__(self):
        match self:
            case self.HEADER_TABLE_SIZE:
                return f"{self.__class__.__name__}.HEADER_TABLE_SIZE"
            case self.ENABLE_PUSH:
                return f"{self.__class__.__name__}.ENABLE_PUSH"
            case self.MAX_CONCURRENT_STREAMS:
                return f"{self.__class__.__name__}.MAX_CONCURRENT_STREAMS"
            case self.INITIAL_WINDOW_SIZE:
                return f"{self.__class__.__name__}.INITIAL_WINDOW_SIZE"
            case self.MAX_FRAME_SIZE:
                return f"{self.__class__.__name__}.MAX_FRAME_SIZE"
            case self.MAX_HEADER_LIST_SIZE:
                return f"{self.__class__.__name__}.MAX_HEADER_LIST_SIZE"
        return f"{self.__class__.__name__}({hex(self)})"


H2Setting.HEADER_TABLE_SIZE = H2Setting(1)
H2Setting.ENABLE_PUSH = H2Setting(2)
H2Setting.MAX_CONCURRENT_STREAMS = H2Setting(3)
H2Setting.INITIAL_WINDOW_SIZE = H2Setting(4)
H2Setting.MAX_FRAME_SIZE = H2Setting(5)
H2Setting.MAX_HEADER_LIST_SIZE = H2Setting(6)


class H2FrameType(int):
    DATA: ClassVar[Self]
    HEADERS: ClassVar[Self]
    PRIORITY: ClassVar[Self]
    RST_STREAM: ClassVar[Self]
    SETTINGS: ClassVar[Self]
    PUSH_PROMISE: ClassVar[Self]
    PING: ClassVar[Self]
    GOAWAY: ClassVar[Self]
    WINDOW_UPDATE: ClassVar[Self]
    CONTINUATION: ClassVar[Self]

    def __repr__(self):
        match self:
            case self.DATA:
                return f"{self.__class__.__name__}.DATA"
            case self.HEADERS:
                return f"{self.__class__.__name__}.HEADERS"
            case self.PRIORITY:
                return f"{self.__class__.__name__}.PRIORITY"
            case self.RST_STREAM:
                return f"{self.__class__.__name__}.RST_STREAM"
            case self.SETTINGS:
                return f"{self.__class__.__name__}.SETTINGS"
            case self.PUSH_PROMISE:
                return f"{self.__class__.__name__}.PUSH_PROMISE"
            case self.PING:
                return f"{self.__class__.__name__}.PING"
            case self.GOAWAY:
                return f"{self.__class__.__name__}.GOAWAY"
            case self.WINDOW_UPDATE:
                return f"{self.__class__.__name__}.WINDOW_UPDATE"
            case self.CONTINUATION:
                return f"{self.__class__.__name__}.CONTINUATION"
        return f"{self.__class__.__name__}({hex(self)})"


H2FrameType.DATA = H2FrameType(0)
H2FrameType.HEADERS = H2FrameType(1)
H2FrameType.PRIORITY = H2FrameType(2)
H2FrameType.RST_STREAM = H2FrameType(3)
H2FrameType.SETTINGS = H2FrameType(4)
H2FrameType.PUSH_PROMISE = H2FrameType(5)
H2FrameType.PING = H2FrameType(6)
H2FrameType.GOAWAY = H2FrameType(7)
H2FrameType.WINDOW_UPDATE = H2FrameType(8)
H2FrameType.CONTINUATION = H2FrameType(9)


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
    def parse(cls, data: bytes | int) -> Self:
        if isinstance(data, bytes):
            assert len(data) == 1
            data = data[0]
        assert isinstance(data, int) and 0 <= data < 2**8
        return cls(*(bool((data >> i) & 1) for i in reversed(range(8))))

    def to_bytes(self: Self) -> bytes:
        return bytes(
            [
                sum(
                    b << (7 - i)
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
class H2GenericFrame:
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
    def parse(cls, inp: Iterable[int]) -> "H2GenericFrame":
        inp = iter(inp)
        length: int = int.from_bytes(bytes(itertools.islice(inp, 3)), "big")
        typ: H2FrameType = H2FrameType(next(inp))
        flags: H2Flags = H2Flags.parse(next(inp))
        raw_stream_id: int = int.from_bytes(bytes(itertools.islice(inp, 4)), "big")
        reserved: bool = bool(raw_stream_id >> 31)
        payload: bytes = bytes(itertools.islice(inp, length))
        if len(payload) != length:
            raise H2Error(f"len({payload!r}) != {length}")
        return cls(
            typ=typ,
            flags=flags,
            reserved=reserved,
            stream_id=raw_stream_id & ~(1 << 31),
            payload=payload,
        )

    def to_bytes(self: Self) -> bytes:
        return len(self.payload).to_bytes(3, "big") + self.typ.to_bytes() + self.flags.to_bytes() + ((self.reserved << 31) | self.stream_id).to_bytes(4, "big") + self.payload

    def specialize(self: Self):
        fn: Callable | None = None
        if self.typ == H2FrameType.DATA:
            fn = H2DataFrame.from_h2frame
        elif self.typ == H2FrameType.HEADERS:
            fn = H2HeadersFrame.from_h2frame
        elif self.typ == H2FrameType.PRIORITY:
            fn = H2PriorityFrame.from_h2frame
        elif self.typ == H2FrameType.RST_STREAM:
            fn = H2RstStreamFrame.from_h2frame
        elif self.typ == H2FrameType.SETTINGS:
            fn = H2SettingsFrame.from_h2frame
        elif self.typ == H2FrameType.PUSH_PROMISE:
            fn = H2PushPromiseFrame.from_h2frame
        elif self.typ == H2FrameType.PING:
            fn = H2PingFrame.from_h2frame
        elif self.typ == H2FrameType.GOAWAY:
            fn = H2GoAwayFrame.from_h2frame
        elif self.typ == H2FrameType.WINDOW_UPDATE:
            fn = H2WindowUpdateFrame.from_h2frame
        elif self.typ == H2FrameType.CONTINUATION:
            fn = H2ContinuationFrame.from_h2frame

        return fn(self) if fn is not None else self


@dataclasses.dataclass
class H2DataFrame:
    """H2 DATA frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    data: bytes = b""
    padding: bytes | None = None

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        assert self.padding is None or len(self.padding) < 0x100

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2DataFrame":
        assert frame.typ == H2FrameType.DATA
        length: int = len(frame.payload)
        flags: H2Flags = H2Flags(padded=frame.flags.padded, end_stream_or_ack=frame.flags.end_stream_or_ack)
        stream_id: int = frame.stream_id
        if flags.padded:
            assert len(frame.payload) >= 1
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

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = self.data
        if self.flags.padded:
            assert self.padding is not None
            payload = bytes([len(self.padding)]) + payload + self.padding
        return H2GenericFrame(H2FrameType.DATA, self.flags, False, self.stream_id, payload)


@dataclasses.dataclass
class H2HeadersFrame:
    """H2 HEADERS frame class. Only needs to represent valid frames."""

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
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2HeadersFrame":
        assert frame.typ == H2FrameType.HEADERS
        # TODO: Add assertion about frame payload length
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
        assert len(bytes(inp)) == 0

        return cls(
            flags=flags,
            stream_id=stream_id,
            exclusive=exclusive,
            stream_dependency=stream_dependency,
            weight=weight,
            field_block_fragment=field_block_fragment,
            padding=padding,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = self.field_block_fragment
        if self.flags.priority:
            assert self.exclusive is not None and self.stream_dependency is not None and self.weight is not None
            payload = b"".join((((self.exclusive << 31) | self.stream_dependency).to_bytes(4, "big"), bytes([self.weight]), payload))

        if self.padding is not None:
            payload = b"".join(((bytes([len(self.padding)]), payload, self.padding)))

        return H2GenericFrame(
            H2FrameType.HEADERS,
            self.flags,
            False,
            self.stream_id,
            payload,
        )


@dataclasses.dataclass
class H2PriorityFrame:
    """H2 PRIORITY frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    exclusive: bool = False
    stream_dependency: int = 0
    weight: int = 0

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        assert 0 <= self.stream_dependency < 1 << 31
        assert 0 <= self.weight < 1 << 8

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PriorityFrame":
        assert frame.typ == H2FrameType.PRIORITY
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

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.PRIORITY, H2Flags(), False, self.stream_id, ((self.exclusive << 31) | self.stream_dependency).to_bytes(4, "big") + bytes([self.weight]))


@dataclasses.dataclass
class H2RstStreamFrame:
    """H2 RST_STREAM frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    error_code: H2ErrorCode = H2ErrorCode.NO_ERROR

    def __post_init__(self: Self):
        assert 0 <= self.stream_id < 1 << 31
        assert 0 <= self.error_code < 1 << 32

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2RstStreamFrame":
        assert frame.typ == H2FrameType.RST_STREAM
        assert len(frame.payload) == 4

        stream_id: int = frame.stream_id
        error_code: H2ErrorCode = H2ErrorCode.from_bytes(frame.payload, "big")

        return cls(
            stream_id=stream_id,
            error_code=error_code,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.RST_STREAM, H2Flags(), False, self.stream_id, self.error_code.to_bytes(4, "big"))


@dataclasses.dataclass
class H2SettingsFrame:
    """H2 SETTINGS frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    settings: list[tuple[int, int]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2SettingsFrame":
        assert frame.typ == H2FrameType.SETTINGS
        assert frame.stream_id == 0
        assert len(frame.payload) % 6 == 0
        if frame.flags.end_stream_or_ack:
            assert len(frame.payload) == 0
        return cls(
            flags=H2Flags(end_stream_or_ack=frame.flags.end_stream_or_ack),
            settings=[(H2Setting(int.from_bytes(frame.payload[i : i + 2], "big")), int.from_bytes(frame.payload[i + 2 : i + 6], "big")) for i in range(0, len(frame.payload), 6)],
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.SETTINGS, self.flags, False, 0, b"".join(map(lambda s: s[0].to_bytes(2, "big") + s[1].to_bytes(4, "big"), self.settings)))


@dataclasses.dataclass
class H2PushPromiseFrame:
    """H2 PUSH_PROMISE frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    promised_stream_id: int = 0
    field_block_fragment: bytes = b""
    padding: bytes | None = None

    def __post_init__(self: Self) -> None:
        assert 0 <= self.promised_stream_id
        assert 0 <= self.stream_id

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PushPromiseFrame":
        assert frame.typ == H2FrameType.PUSH_PROMISE
        assert len(frame.payload) >= 4 + frame.flags.padded
        it: Iterator[int] = iter(frame.payload)
        pad_length: int | None = next(it) if frame.flags.padded else None
        promised_stream_id: int = int.from_bytes(bytes(itertools.islice(it, 4))) & ~(1 << 31)
        field_block_fragment: bytes = bytes(itertools.islice(it, len(frame.payload) - frame.flags.padded - (pad_length if pad_length is not None else 0)))
        padding: bytes | None = bytes(it) if frame.flags.padded else None
        if padding is not None:
            assert len(padding) == pad_length
        return cls(
            H2Flags(padded=frame.flags.padded, end_headers=frame.flags.end_headers),
            stream_id=frame.stream_id,
            promised_stream_id=promised_stream_id,
            field_block_fragment=field_block_fragment,
            padding=padding,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = b"".join((self.promised_stream_id.to_bytes(4, "big"), self.field_block_fragment))
        if self.padding is not None:
            payload = b"".join((bytes([len(self.padding)]), payload, self.padding))

        return H2GenericFrame(
            H2FrameType.PUSH_PROMISE,
            self.flags,
            False,
            self.stream_id,
            payload,
        )


@dataclasses.dataclass
class H2PingFrame:
    """H2 PING frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    opaque_data: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00"

    def __post_init__(self: Self) -> None:
        assert len(self.opaque_data) == 8

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PingFrame":
        assert frame.typ == H2FrameType.PING
        assert frame.stream_id == 0

        return cls(
            flags=H2Flags(end_stream_or_ack=frame.flags.end_stream_or_ack),
            opaque_data=frame.payload,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.PING, self.flags, False, 0, self.opaque_data)


@dataclasses.dataclass
class H2GoAwayFrame:
    """H2 GOAWAY frame class. Only needs to represent valid frames."""

    last_stream_id: int = 0
    error_code: H2ErrorCode = H2ErrorCode.NO_ERROR
    additional_debug_data: bytes = b""

    def __post_init__(self: Self):
        assert 0 <= self.last_stream_id < 1 << 31
        assert 0 <= self.error_code < 1 << 32

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2GoAwayFrame":
        assert frame.typ == H2FrameType.GOAWAY
        assert frame.stream_id == 0
        assert len(frame.payload) >= 8

        last_stream_id: int = int.from_bytes(frame.payload[:4], "big") & ~(1 << 31)
        error_code: H2ErrorCode = H2ErrorCode.from_bytes(frame.payload[4:8], "big")
        additional_debug_data: bytes = frame.payload[8:]

        return cls(
            last_stream_id=last_stream_id,
            error_code=error_code,
            additional_debug_data=additional_debug_data,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.GOAWAY, H2Flags(), False, 0, self.last_stream_id.to_bytes(4, "big") + self.error_code.to_bytes(4, "big") + self.additional_debug_data)


@dataclasses.dataclass
class H2WindowUpdateFrame:
    """H2 WINDOW_UPDATE frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    window_size_increment: int = 0

    def __post_init__(self: Self) -> None:
        assert 0 <= self.stream_id
        assert 0 <= self.window_size_increment

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2WindowUpdateFrame":
        assert frame.typ == H2FrameType.WINDOW_UPDATE
        assert len(frame.payload) == 4

        return cls(
            stream_id=frame.stream_id,
            window_size_increment=int.from_bytes(frame.payload, "big") & ~(1 << 31),
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.WINDOW_UPDATE, H2Flags(), False, self.stream_id, self.window_size_increment.to_bytes(4, "big"))


@dataclasses.dataclass
class H2ContinuationFrame:
    """H2 CONTINUATION frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    field_block_fragment: bytes = b""

    def __post_init__(self: Self) -> None:
        assert 0 <= self.stream_id

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2ContinuationFrame":
        assert frame.typ == H2FrameType.CONTINUATION
        return cls(
            H2Flags(end_headers=frame.flags.end_headers),
            stream_id=frame.stream_id,
            field_block_fragment=frame.payload,
        )

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.CONTINUATION, self.flags, False, self.stream_id, self.field_block_fragment)


H2Frame = (
    H2GenericFrame | H2ContinuationFrame | H2WindowUpdateFrame | H2GoAwayFrame | H2PingFrame | H2PushPromiseFrame | H2SettingsFrame | H2RstStreamFrame | H2PriorityFrame | H2HeadersFrame | H2DataFrame
)


def parse_frames(data: Iterable[int]) -> list[H2Frame]:
    data = iter(data)
    result: list[H2Frame] = []
    while True:
        try:
            result.append(H2GenericFrame.parse(data).specialize())
        except StopIteration:
            break
    return result
