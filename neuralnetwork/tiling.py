"""tiling.py -- decompose a large GEMM into array-sized tiles.

The array computes one R x C tile; the host sequences tiles and accumulates
across the K dimension. This is exactly what an on-chip controller would do
(left as future work in RTL); here we use the cycle-accurate WS model, which
is verified equal to the RTL by the cocotb tests.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from funcsim import ws_systolic, ws_tile_cycles  # noqa: E402


def _ceil_div(a, b):
    return -(-a // b)


def gemm_tiled(X, W, A):
    """Integer Y = X@W using A x A weight-stationary tiles. Exact."""
    X = np.asarray(X, np.int64); W = np.asarray(W, np.int64)
    M, K = X.shape; K2, N = W.shape
    assert K == K2
    Y = np.zeros((M, N), np.int64)
    for n0 in range(0, N, A):
        n1 = min(n0 + A, N)
        for k0 in range(0, K, A):
            k1 = min(k0 + A, K)
            Xt = X[:, k0:k1]
            Wt = W[k0:k1, n0:n1]
            # pad tile to A x A (zeros don't affect the sum)
            Xp = np.zeros((M, A), np.int64); Xp[:, :k1 - k0] = Xt
            Wp = np.zeros((A, A), np.int64); Wp[:k1 - k0, :n1 - n0] = Wt
            Yt = ws_systolic(Xp, Wp)            # verified == RTL
            Y[:, n0:n1] += Yt[:, :n1 - n0]
    return Y


def gemm_cycles(M, K, N, A):
    """Total cycles for Y[M,N]=X[M,K]@W[K,N] on an A x A weight-stationary array."""
    return _ceil_div(K, A) * _ceil_div(N, A) * ws_tile_cycles(M, A, A)


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    X = rng.integers(-127, 128, (10, 20)); W = rng.integers(-127, 128, (20, 12))
    ok = np.array_equal(gemm_tiled(X, W, 4), X.astype(np.int64) @ W)
    print("tiled GEMM (20-deep reduction over 4x4 array) exact:", ok)
