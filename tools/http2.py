import dataclasses

from typing import Self, Final

from hpack import FieldBlockFragment


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
        assert self.val in range(2**8)
        self.DEFAULT_TYPES: dict[int, str] = {
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

    def __repr__(self: Self):
        return self.DEFAULT_TYPES[self.val] if self.val in self.DEFAULT_TYPES else f"H2FrameType({hex(self.val)})"

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        assert len(data) == 1
        return cls(data[0])

    def serialize(self: Self) -> bytes:
        return bytes([self.val])


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
    def deserialize(cls, data: bytes) -> Self:
        assert len(data) == 1
        return cls(*(bool((data[0] >> i) & 1) for i in reversed(range(8))))

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
        assert self.stream_id in range(2**31)

    @classmethod
    def deserialize(cls, data: bytes) -> "H2Frame":
        assert len(data) >= 9
        length: int = int.from_bytes(data[0:3], "big")
        return cls(
            typ=H2FrameType(data[3]),
            flags=H2Flags.deserialize(data[4:5]),
            reserved=bool(data[5] >> 7),
            stream_id=int.from_bytes(data[6:9], "big") & ~(1 << 31),
            payload=data[9 : 9 + length],
        )

    def serialize(self: Self) -> bytes:
        return len(self.payload).to_bytes(3, "big") + self.typ.serialize() + self.flags.serialize() + ((self.reserved << 31) | self.stream_id).to_bytes(4, "big") + self.payload


@dataclasses.dataclass
class H2DataFrame:
    """H2 data frame class. Only needs to represent valid frames."""

    flags: H2Flags = dataclasses.field(default_factory=H2Flags)
    stream_id: int = 0
    data: bytes = b""
    padding: bytes = b""

    def __post_init__(self: Self):
        assert self.stream_id in range(2**31) and len(self.padding) <= 255

    @classmethod
    def deserialize(cls, data: bytes) -> "H2DataFrame":
        assert len(data) >= 9
        length: int = int.from_bytes(data[0:3], "big")
        flags: H2Flags = H2Flags.deserialize(data[4:5])
        padding: bytes = data[9 + length - data[9] : 9 + length] if flags.padded else b""

        return cls(
            flags=flags,
            stream_id=int.from_bytes(data[6:9], "big") & ~(1 << 31),
            data=data[9 : 9 + length],
            padding=padding,
        )

    def serialize(self: Self) -> bytes:
        payload_len: int = len(self.data)
        if self.flags.padded:
            payload_len += 1 + len(self.padding)
        return payload_len.to_bytes(3, "big") + H2FrameType.data().serialize() + self.flags.serialize() + self.stream_id.to_bytes(4, "big") + (bytes([len(self.padding)]) if self.flags.padded else b"") + self.data + self.padding
