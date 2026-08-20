"""run_inference.py -- run a small neural network on the int8 accelerator.

A representative multi-layer perceptron (the kind used for edge inference and
lightweight control) is run with every layer as an int8 GEMM on the systolic
array, and the int8 output is compared to fp32. This measures the numerical cost
of int8 inference on the accelerator, independent of any particular workload.

Each fully-connected layer is a GEMM (what the array does); the ReLU/tanh
nonlinearity between layers is a non-GEMM op done in the host (a special-function
unit in a real chip). Weights are a fixed representative init -- drop in any
trained network and the pipeline is unchanged.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.dirname(__file__))
from golden import quantize_per_tensor_sym, dequant   # noqa: E402
from tiling import gemm_tiled                          # noqa: E402


def make_mlp(dims, seed=0):
    rng = np.random.default_rng(seed)
    layers = []
    for i in range(len(dims) - 1):
        W = (rng.standard_normal((dims[i], dims[i + 1])) / np.sqrt(dims[i])).astype(np.float32)
        b = np.zeros(dims[i + 1], np.float32)
        layers.append((W, b))
    return layers


def mlp_fp(x, layers):
    for i, (W, b) in enumerate(layers):
        x = x @ W + b
        x = np.maximum(x, 0) if i < len(layers) - 1 else np.tanh(x)  # ReLU hidden, tanh out
    return x


def mlp_int8(x, layers, A=4):
    """Every layer's GEMM on the int8 array; bias + nonlinearity in host."""
    for i, (W, b) in enumerate(layers):
        xq, sx = quantize_per_tensor_sym(x)
        Wq, sw = quantize_per_tensor_sym(W)
        x = dequant(gemm_tiled(xq, Wq, A), sx, sw) + b
        x = np.maximum(x, 0) if i < len(layers) - 1 else np.tanh(x)
    return x


def main():
    dims = [16, 32, 16, 4]          # representative small edge-inference MLP
    batch, A = 16, 4
    rng = np.random.default_rng(1)
    x = rng.standard_normal((batch, dims[0])).astype(np.float32)
    layers = make_mlp(dims)

    y_fp = mlp_fp(x, layers)
    y_i8 = mlp_int8(x, layers, A)
    rel = np.linalg.norm(y_i8 - y_fp) / (np.linalg.norm(y_fp) + 1e-9)
    maxerr = np.max(np.abs(y_i8 - y_fp))
    arch = "->".join(map(str, dims))
    print(f"small MLP inference  {arch}  (batch {batch})  on {A}x{A} int8 array")
    print(f"  each layer runs as a GEMM on the array; ReLU/tanh = host SFU")
    print(f"  int8 vs fp32 output relative error : {rel:.4%}")
    print(f"  int8 vs fp32 output max abs error  : {maxerr:.5f}")


if __name__ == "__main__":
    main()
