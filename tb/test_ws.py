import os, sys
import numpy as np
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.dirname(__file__))
from golden import gemm_int                         # noqa: E402
from funcsim import ws_systolic                      # noqa: E402
from cocotb_helpers import pack, unpack              # noqa: E402

R = int(os.environ.get("R", 4))
C = int(os.environ.get("C", 4))
M = int(os.environ.get("M", 6))
DATA_W = int(os.environ.get("DATA_W", 8))
ACC_W = int(os.environ.get("ACC_W", 32))


async def reset(dut):
    dut.rst_n.value = 0
    dut.load_w.value = 0
    dut.w_bus.value = 0
    dut.west_bus.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def ws_matches_golden(dut):
    rng = np.random.default_rng(int(os.environ.get("SEED", 2)))
    X = rng.integers(-127, 128, (M, R), dtype=np.int64)
    W = rng.integers(-127, 128, (R, C), dtype=np.int64)
    Y_gold = gemm_int(X, W)
    _, south_expected = ws_systolic(X, W, trace=True)

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    # Preload all weights in parallel (one load_w pulse).
    dut.w_bus.value = pack(W.flatten(order="C"), DATA_W)   # PE(r,c) at r*C+c
    dut.load_w.value = 1
    dut.west_bus.value = 0
    await RisingEdge(dut.clk)
    dut.load_w.value = 0
    dut.w_bus.value = 0

    # Stream skewed activations; capture south each cycle.
    T = len(south_expected)
    south_rtl = []
    for t in range(T + 2):
        west = [int(X[t - r, r]) if 0 <= t - r < M else 0 for r in range(R)]
        dut.west_bus.value = pack(west, DATA_W)
        await RisingEdge(dut.clk)
        south_rtl.append(unpack(int(dut.south_bus.value), C, ACC_W))

    exp = [list(v) for v in south_expected]

    # Find constant pipeline offset where RTL trace == expected trace.
    offset = None
    for off in range(0, 4):
        ok = all(south_rtl[t + off] == exp[t] for t in range(T)
                 if t + off < len(south_rtl))
        if ok:
            offset = off
            break
    assert offset is not None, (
        "RTL south trace never matched the cycle model.\n"
        f"expected[:6]={exp[:6]}\n got[:8]={south_rtl[:8]}"
    )
    dut._log.info(f"WS south trace matches funcsim at pipeline offset {offset}")

    # Reconstruct Y from the (offset-aligned) RTL trace and compare to golden.
    Y_rtl = np.zeros((M, C), np.int64)
    for t in range(T):
        for c in range(C):
            m = t - R - c
            if 0 <= m < M:
                Y_rtl[m, c] = south_rtl[t + offset][c]
    assert np.array_equal(Y_rtl, Y_gold), (
        f"Y mismatch.\nRTL=\n{Y_rtl}\nGOLD=\n{Y_gold}"
    )
    dut._log.info(f"WS {R}x{C}, M={M}: Y matches numpy golden exactly.")
