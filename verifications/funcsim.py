"""funcsim.py -- cycle-accurate functional model of the weight-stationary systolic array.

Register semantics match the RTL exactly (update-at-edge), so these models
serve two roles:
  1. Final results are checked against golden.py (numpy).
  2. The per-cycle edge traces are the expected sequences the cocotb tests
     compare the RTL against, cycle for cycle.
"""
import numpy as np


def ws_systolic(X, W, trace=False):
    """Weight-stationary. Y = X@W, X:[M,R], W:[R,C]. Array is R x C.

    Host drives west input skewed: row r delayed by r cycles.
    Returns Y[M,C]; if trace, also a list of south-edge vectors per cycle.
    """
    X = np.asarray(X, np.int64); W = np.asarray(W, np.int64)
    M, R = X.shape; R2, C = W.shape
    assert R == R2
    a_reg = np.zeros((R, C), np.int64)
    ps_reg = np.zeros((R, C), np.int64)

    def west_in(r, t):
        m = t - r
        return int(X[m, r]) if 0 <= m < M else 0

    Y = np.zeros((M, C), np.int64)
    south_trace = []
    T = M + R + C + 4
    for t in range(T):
        # south edge available this cycle = bottom-row partial sums (registered)
        south = ps_reg[R - 1, :].copy()
        south_trace.append(south)
        for c in range(C):
            m = t - R - c
            if 0 <= m < M:
                Y[m, c] = ps_reg[R - 1, c]
        # compute next-state
        na = np.zeros_like(a_reg); nps = np.zeros_like(ps_reg)
        for r in range(R):
            for c in range(C):
                a_in = west_in(r, t) if c == 0 else a_reg[r, c - 1]
                psum_in = 0 if r == 0 else ps_reg[r - 1, c]
                na[r, c] = a_in
                nps[r, c] = psum_in + int(W[r, c]) * a_in
        a_reg, ps_reg = na, nps
    return (Y, south_trace) if trace else Y



# --- cycle-count helper ---------------------------------------------------
def ws_tile_cycles(M, R, C):
    """Cycles to stream one M-row tile through an R x C WS array
    (weight load + stream + drain)."""
    return 1 + M + (R + C)        # 1 load pulse + M tokens + fill/drain



if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from golden import gemm_int
    rng = np.random.default_rng(1)
    X = rng.integers(-8, 8, (6, 4)); W = rng.integers(-8, 8, (4, 4))
    print("WS matches golden:", np.array_equal(ws_systolic(X, W), gemm_int(X, W)))
