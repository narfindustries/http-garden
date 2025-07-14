import dataclasses
import itertools

from typing import Callable, Self, Iterator, Iterable, ClassVar

import hpack


class H2Error(Exception):
    pass


def bslice(it: Iterable[int], length: int) -> bytes:
    assert 0 <= length
    it = iter(it)
    result: bytes = bytes(itertools.islice(it, length))
    if len(result) != length:
        raise H2Error("Not enough data in iterator")
    return result


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
H2ErrorCode.CONNECT_ERROR = H2ErrorCode(0xA)
H2ErrorCode.ENHANCE_YOUR_CALM = H2ErrorCode(0xB)
H2ErrorCode.INADEQUATE_SECURITY = H2ErrorCode(0xC)
H2ErrorCode.HTTP_1_1_REQUIRED = H2ErrorCode(0xD)


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
            if len(data) != 1:
                raise H2Error("H2Flag parser input too long")
            data = data[0]
        if not 0 <= data < 2**8:
            raise H2Error("H2Flag value doesn't fit in a byte")
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
class H2State:
    hpack_state: hpack.HPACKState = dataclasses.field(default_factory=hpack.HPACKState)
    window_size: int = 65535


def check_stream_id(stream_id: int, can_be_zero: bool = True, must_be_zero: bool = False) -> None:
    if (not can_be_zero and stream_id == 0) or (must_be_zero and stream_id != 0) or (not 0 <= stream_id < 1 << 31):
        raise H2Error("Invalid stream ID")


def check_frame_type(frame_type: H2FrameType, expected: H2FrameType) -> None:
    if frame_type != expected:
        raise H2Error("Unexpected frame type")


def check_error_code(error_code: int) -> None:
    if not 0 <= error_code < 1 << 32:
        raise H2Error("Error code out of range")


def check_pad_length(pad_length: int | None) -> None:
    if pad_length is None:
        return
    if not 0 <= pad_length < 0x100:
        raise H2Error("Padding length out of range")


def check_padding(padding: bytes, pad_length: int) -> None:
    check_pad_length(pad_length)
    if len(padding) != pad_length:
        raise H2Error("Padding doesn't match pad length")


def check_priority(exclusive: bool | None, stream_dependency: int | None, weight: int | None) -> None:
    if (exclusive is None) != (weight is None) != (stream_dependency is None):
        raise H2Error("Either all or none of exclusive, weight, and stream_dependency fields must be present")
    if weight is not None and not 0 <= weight < 0x100:
        raise H2Error("Invalid weight")
    if stream_dependency is not None:
        check_stream_id(stream_dependency)


@dataclasses.dataclass
class H2GenericFrame:
    """Generic H2 Frame class. Should be able to represent any frame, valid or invalid."""

    typ: H2FrameType
    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    reserved: bool = False
    stream_id: int = 0
    payload: bytes = b""

    def __post_init__(self: Self):
        check_stream_id(self.stream_id)
        if len(self.payload) >= 1 << 24:
            raise H2Error("Payload too long")

    @classmethod
    def parse(cls, inp: Iterable[int]) -> "H2GenericFrame":
        inp = iter(inp)
        first_byte: int = next(inp)  # To deliberately throw StopIteration
        inp = itertools.chain(iter([first_byte]), inp)
        length: int = int.from_bytes(bslice(inp, 3), "big")
        try:
            typ: H2FrameType = H2FrameType(next(inp))
            flags: H2Flags = H2Flags.parse(next(inp))
        except StopIteration as e:
            raise H2Error("Frame incomplete") from e
        raw_stream_id: int = int.from_bytes(bslice(inp, 4), "big")
        reserved: bool = bool(raw_stream_id >> 31)
        payload: bytes = bslice(inp, length)
        return cls(
            typ=typ,
            flags=flags,
            reserved=reserved,
            stream_id=raw_stream_id & ~(1 << 31),
            payload=payload,
        )

    def to_generic(self: Self) -> Self:
        return self

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

        try:
            return fn(self) if fn is not None else self
        except H2Error:
            return self


@dataclasses.dataclass(frozen=True)
class H2DataFrame:
    """H2 DATA frame class. Only needs to represent valid frames."""

    end_stream: bool = True
    stream_id: int = 0
    data: bytes = b""
    pad_length: int | None = None

    def __post_init__(self: Self):
        check_pad_length(self.pad_length)
        check_stream_id(self.stream_id, can_be_zero=False)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2DataFrame":
        check_frame_type(frame.typ, H2FrameType.DATA)
        length: int = len(frame.payload)
        stream_id: int = frame.stream_id
        if frame.flags.padded and len(frame.payload) == 0:
            raise H2Error("DATA frame is padded, but its payload is only 1 byte long")
        inp: Iterator[int] = iter(frame.payload)
        pad_length: int | None = next(inp) if frame.flags.padded else None
        data: bytes = bslice(inp, length - (pad_length + 1 if pad_length is not None else 0))
        if pad_length is not None:
            check_padding(bslice(inp, pad_length), pad_length)
        if len(bytes(inp)) != 0:
            raise H2Error("Trailing data")

        return cls(
            end_stream=frame.flags.end_stream_or_ack,
            stream_id=stream_id,
            data=data,
            pad_length=pad_length,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = self.data
        if self.pad_length is not None:
            payload = b"".join((self.pad_length.to_bytes(1), payload, bytes(self.pad_length)))
        return H2GenericFrame(H2FrameType.DATA, H2Flags(end_stream_or_ack=self.end_stream, padded=self.pad_length is not None), False, self.stream_id, payload)


@dataclasses.dataclass(frozen=True)
class H2HeadersFrame:
    """H2 HEADERS frame class. Only needs to represent valid frames."""

    end_headers: bool = True
    end_stream: bool = False
    stream_id: int = 0
    exclusive: bool | None = None
    stream_dependency: int | None = None
    weight: int | None = None
    field_block_fragment: bytes = b""
    pad_length: int | None = None

    def __post_init__(self: Self):
        check_stream_id(self.stream_id, can_be_zero=False)
        check_priority(self.exclusive, self.stream_dependency, self.weight)
        check_pad_length(self.pad_length)

    @property
    def priority(self: Self) -> bool:
        return self.exclusive is not None and self.stream_dependency is not None and self.weight is not None

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2HeadersFrame":
        check_frame_type(frame.typ, H2FrameType.HEADERS)
        length: int = len(frame.payload)
        stream_id: int = frame.stream_id
        inp: Iterator[int] = iter(frame.payload)
        payload_prefix_len: int = 0
        pad_length: int | None = None
        if frame.flags.padded:
            payload_prefix_len += 1
            if payload_prefix_len > len(frame.payload):
                raise H2Error("Padded payload can't fit padding length")
            pad_length = next(inp)

        stream_dependency: int | None = None
        exclusive: bool | None = None
        weight: int | None = None
        if frame.flags.priority:
            payload_prefix_len += 5
            if payload_prefix_len > len(frame.payload):
                raise H2Error("Priority payload can't fit priority data")
            raw_stream_dependency: int = int.from_bytes(bslice(inp, 4), "big")
            stream_dependency = raw_stream_dependency & ~(1 << 31)
            exclusive = bool(raw_stream_dependency >> 31)
            weight = next(inp)

        fbf_len: int = length - payload_prefix_len - (pad_length if pad_length is not None else 0)
        field_block_fragment: bytes = bslice(inp, fbf_len)

        if pad_length is not None:
            check_padding(bslice(inp, pad_length), pad_length)
        if len(bytes(inp)) > 0:
            raise H2Error("Trailing data")

        return cls(
            end_headers=frame.flags.end_headers,
            end_stream=frame.flags.end_stream_or_ack,
            stream_id=stream_id,
            exclusive=exclusive,
            stream_dependency=stream_dependency,
            weight=weight,
            field_block_fragment=field_block_fragment,
            pad_length=pad_length,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = self.field_block_fragment
        if self.priority:
            assert self.exclusive is not None
            assert self.stream_dependency is not None
            assert self.weight is not None
            payload = b"".join(
                (
                    ((self.exclusive << 31) | self.stream_dependency).to_bytes(4, "big"),
                    self.weight.to_bytes(1),
                    payload,
                )
            )

        if self.pad_length is not None:
            payload = b"".join(((self.pad_length.to_bytes(1), payload, bytes(self.pad_length))))

        return H2GenericFrame(
            H2FrameType.HEADERS,
            H2Flags(priority=self.priority, padded=self.pad_length is not None, end_stream_or_ack=self.end_stream, end_headers=self.end_headers),
            False,
            self.stream_id,
            payload,
        )


@dataclasses.dataclass(frozen=True)
class H2PriorityFrame:
    """H2 PRIORITY frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    exclusive: bool = False
    stream_dependency: int = 0
    weight: int = 0

    def __post_init__(self: Self):
        check_stream_id(self.stream_id, can_be_zero=False)
        check_priority(self.exclusive, self.stream_dependency, self.weight)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PriorityFrame":
        check_frame_type(frame.typ, H2FrameType.PRIORITY)
        if len(frame.payload) != 5:
            raise H2Error("Invalid priority payload length")

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

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.PRIORITY, H2Flags(), False, self.stream_id, ((self.exclusive << 31) | self.stream_dependency).to_bytes(4, "big") + bytes([self.weight]))


@dataclasses.dataclass(frozen=True)
class H2RstStreamFrame:
    """H2 RST_STREAM frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    error_code: H2ErrorCode = H2ErrorCode.NO_ERROR

    def __post_init__(self: Self):
        check_stream_id(self.stream_id, can_be_zero=False)
        check_error_code(self.error_code)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2RstStreamFrame":
        check_frame_type(frame.typ, H2FrameType.RST_STREAM)
        if len(frame.payload) != 4:
            raise H2Error("Invalid RST_STREAM payload length")

        stream_id: int = frame.stream_id
        error_code: H2ErrorCode = H2ErrorCode.from_bytes(frame.payload, "big")

        return cls(
            stream_id=stream_id,
            error_code=error_code,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.RST_STREAM, H2Flags(), False, self.stream_id, self.error_code.to_bytes(4, "big"))


@dataclasses.dataclass(frozen=True)
class H2SettingsFrame:
    """H2 SETTINGS frame class. Only needs to represent valid frames."""

    ack: bool = False
    settings: list[tuple[int, int]] = dataclasses.field(default_factory=list)

    def __post_init__(self: Self) -> None:
        if self.ack and len(self.settings) > 0:
            raise H2Error("ACK flag is set, but settings frame is nonempty")

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2SettingsFrame":
        check_frame_type(frame.typ, H2FrameType.SETTINGS)
        check_stream_id(frame.stream_id, must_be_zero=True)

        if len(frame.payload) % 6 != 0:
            raise H2Error("SETTINGS frame payload length is not a multiple of 6")
        return cls(
            ack=frame.flags.end_stream_or_ack,
            settings=[(H2Setting(int.from_bytes(frame.payload[i : i + 2], "big")), int.from_bytes(frame.payload[i + 2 : i + 6], "big")) for i in range(0, len(frame.payload), 6)],
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.SETTINGS, H2Flags(end_stream_or_ack=self.ack), False, 0, b"".join(map(lambda s: s[0].to_bytes(2, "big") + s[1].to_bytes(4, "big"), self.settings)))


@dataclasses.dataclass(frozen=True)
class H2PushPromiseFrame:
    """H2 PUSH_PROMISE frame class. Only needs to represent valid frames."""

    end_headers: bool = True
    stream_id: int = 0
    promised_stream_id: int = 0
    field_block_fragment: bytes = b""
    pad_length: int | None = None

    def __post_init__(self: Self) -> None:
        check_pad_length(self.pad_length)
        check_stream_id(self.stream_id, can_be_zero=False)
        check_stream_id(self.promised_stream_id, can_be_zero=False)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PushPromiseFrame":
        check_frame_type(frame.typ, H2FrameType.PUSH_PROMISE)
        length: int = len(frame.payload)
        stream_id: int = frame.stream_id
        inp: Iterator[int] = iter(frame.payload)
        payload_prefix_len: int = 4
        pad_length: int | None = None
        if frame.flags.padded:
            payload_prefix_len += 1
            if payload_prefix_len > len(frame.payload):
                raise H2Error("Padded payload can't fit padding length")
            pad_length = next(inp)

        raw_promised_stream_id: bytes = bslice(inp, 4)
        promised_stream_id: int = int.from_bytes(raw_promised_stream_id, "big") & ~(1 << 31)

        fbf_len: int = length - payload_prefix_len - (pad_length if pad_length is not None else 0)
        field_block_fragment: bytes = bslice(inp, fbf_len)

        if pad_length is not None:
            check_padding(bslice(inp, pad_length), pad_length)

        if len(bytes(inp)) > 0:
            raise H2Error("Trailing data")

        return cls(
            end_headers=frame.flags.end_headers,
            stream_id=stream_id,
            promised_stream_id=promised_stream_id,
            field_block_fragment=field_block_fragment,
            pad_length=pad_length,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        payload: bytes = b"".join((self.promised_stream_id.to_bytes(4, "big"), self.field_block_fragment))
        if self.pad_length is not None:
            payload = b"".join((self.pad_length.to_bytes(1), payload, bytes(self.pad_length)))

        return H2GenericFrame(
            H2FrameType.PUSH_PROMISE,
            H2Flags(end_headers=self.end_headers, padded=self.pad_length is not None),
            False,
            self.stream_id,
            payload,
        )


@dataclasses.dataclass(frozen=True)
class H2PingFrame:
    """H2 PING frame class. Only needs to represent valid frames."""

    ack: bool
    opaque_data: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00"

    def __post_init__(self: Self) -> None:
        if len(self.opaque_data) != 8:
            raise H2Error("Invalid PING payload length")

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2PingFrame":
        check_frame_type(frame.typ, H2FrameType.PING)
        check_stream_id(frame.stream_id, must_be_zero=True)

        return cls(
            frame.flags.end_stream_or_ack,
            opaque_data=frame.payload,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.PING, H2Flags(end_stream_or_ack=self.ack), False, 0, self.opaque_data)


@dataclasses.dataclass(frozen=True)
class H2GoAwayFrame:
    """H2 GOAWAY frame class. Only needs to represent valid frames."""

    last_stream_id: int = 0
    error_code: H2ErrorCode = H2ErrorCode.NO_ERROR
    additional_debug_data: bytes = b""

    def __post_init__(self: Self):
        check_stream_id(self.last_stream_id)
        check_error_code(self.error_code)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2GoAwayFrame":
        check_frame_type(frame.typ, H2FrameType.GOAWAY)
        check_stream_id(frame.stream_id, must_be_zero=True)
        minimum_payload_len: int = 8
        if len(frame.payload) < minimum_payload_len:
            raise H2Error("GOAWAY frame payload too short")

        last_stream_id: int = int.from_bytes(frame.payload[:4], "big") & ~(1 << 31)
        error_code: H2ErrorCode = H2ErrorCode.from_bytes(frame.payload[4:8], "big")
        additional_debug_data: bytes = frame.payload[8:]

        return cls(
            last_stream_id=last_stream_id,
            error_code=error_code,
            additional_debug_data=additional_debug_data,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.GOAWAY, H2Flags(), False, 0, self.last_stream_id.to_bytes(4, "big") + self.error_code.to_bytes(4, "big") + self.additional_debug_data)


@dataclasses.dataclass
class H2WindowUpdateFrame:
    """H2 WINDOW_UPDATE frame class. Only needs to represent valid frames."""

    stream_id: int = 0
    window_size_increment: int = 0

    def __post_init__(self: Self) -> None:
        check_stream_id(self.stream_id)
        if not 0 < self.window_size_increment < 1 << 31:
            raise H2Error("Invalid window size increment")

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2WindowUpdateFrame":
        check_frame_type(frame.typ, H2FrameType.WINDOW_UPDATE)
        if len(frame.payload) != 4:
            raise H2Error("WINDOW_UPDATE frame payload too short")

        return cls(
            stream_id=frame.stream_id,
            window_size_increment=int.from_bytes(frame.payload, "big") & ~(1 << 31),
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.WINDOW_UPDATE, H2Flags(), False, self.stream_id, self.window_size_increment.to_bytes(4, "big"))


@dataclasses.dataclass
class H2ContinuationFrame:
    """H2 CONTINUATION frame class. Only needs to represent valid frames."""

    end_headers: bool = False
    stream_id: int = 0
    field_block_fragment: bytes = b""

    def __post_init__(self: Self) -> None:
        check_stream_id(self.stream_id, can_be_zero=False)

    @classmethod
    def from_h2frame(cls, frame: H2GenericFrame) -> "H2ContinuationFrame":
        check_frame_type(frame.typ, H2FrameType.CONTINUATION)
        return cls(
            end_headers=frame.flags.end_headers,
            stream_id=frame.stream_id,
            field_block_fragment=frame.payload,
        )

    def to_bytes(self: Self) -> bytes:
        return self.to_generic().to_bytes()

    def to_generic(self: Self) -> H2GenericFrame:
        return H2GenericFrame(H2FrameType.CONTINUATION, H2Flags(end_headers=self.end_headers), False, self.stream_id, self.field_block_fragment)


H2Frame = (
    H2GenericFrame | H2ContinuationFrame | H2WindowUpdateFrame | H2GoAwayFrame | H2PingFrame | H2PushPromiseFrame | H2SettingsFrame | H2RstStreamFrame | H2PriorityFrame | H2HeadersFrame | H2DataFrame
)


def parse_generic_frames(data: Iterable[int]) -> list[H2GenericFrame]:
    data = iter(data)
    result: list[H2GenericFrame] = []
    while True:
        try:
            result.append(H2GenericFrame.parse(data))
        except StopIteration:
            break
    return result


def parse_frames(data: Iterable[int]) -> list[H2Frame]:
    return [f.specialize() for f in parse_generic_frames(data)]
