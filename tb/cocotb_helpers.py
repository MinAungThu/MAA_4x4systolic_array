"""cocotb_helpers.py -- pack/unpack signed lanes into flattened buses."""


def pack(values, width):
    """Pack a list of signed ints into one big int, lane i at bit i*width."""
    mask = (1 << width) - 1
    out = 0
    for i, v in enumerate(values):
        out |= (int(v) & mask) << (i * width)
    return out


def unpack(bus_int, n, width):
    """Unpack n signed lanes of `width` bits from a big int."""
    mask = (1 << width) - 1
    vals = []
    for i in range(n):
        raw = (bus_int >> (i * width)) & mask
        if raw >> (width - 1):           # sign bit set
            raw -= (1 << width)
        vals.append(raw)
    return vals


def read_int(handle):
    """Read a cocotb signal as an unsigned python int (X -> raises)."""
    return int(handle.value)
