"""golden.py -- numpy reference: int8 quantization + integer GEMM.

The single source of truth for *what the right answer is*. Hardware (RTL) and
the cycle model (funcsim) are both checked against this.
"""
import numpy as np


def quantize_per_tensor_sym(x):
    """Per-tensor symmetric int8. Returns (q_int8, scale)."""
    x = np.asarray(x, dtype=np.float64)
    s = np.max(np.abs(x)) / 127.0
    s = s if s != 0 else 1.0
    q = np.clip(np.round(x / s), -127, 127).astype(np.int64)
    return q, s


def gemm_int(Xq, Wq):
    """Exact integer GEMM (int32-range accumulation)."""
    return np.asarray(Xq, np.int64) @ np.asarray(Wq, np.int64)


def dequant(Y_int, sx, sw):
    return Y_int.astype(np.float64) * sx * sw


def quant_gemm(Xf, Wf):
    """Full quantized matmul: quantize -> int GEMM -> dequantize."""
    Xq, sx = quantize_per_tensor_sym(Xf)
    Wq, sw = quantize_per_tensor_sym(Wf)
    return dequant(gemm_int(Xq, Wq), sx, sw)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    Xf = rng.standard_normal((6, 4)).astype(np.float32)
    Wf = rng.standard_normal((4, 4)).astype(np.float32)
    Yq = quant_gemm(Xf, Wf)
    Yf = Xf @ Wf
    rel = np.linalg.norm(Yq - Yf) / np.linalg.norm(Yf)
    print(f"int8 vs fp32 relative error: {rel:.4%}")
