# Top-level regression for the weight-stationary GEMM accelerator.
#   make test    -> model check + RTL cocotb tests (4x4 and 8x8)
#   make exp     -> tiling check + int8 control-policy workload
#   make all     -> everything
#   make clean

.PHONY: all test rtl model exp clean

all: test exp

model:
	@echo "== functional model vs numpy golden =="
	python3 model/golden.py
	python3 model/funcsim.py

rtl:
	@echo "== RTL cocotb tests (Icarus) =="
	$(MAKE) -C tb ws
	$(MAKE) -C tb ws R=8 C=8 M=12

test: model rtl

exp:
	@echo "== host tiling / int8 MLP inference =="
	python3 exp/tiling.py
	python3 exp/run_inference.py


clean:
	$(MAKE) -C tb clean
	rm -rf model/__pycache__ exp/__pycache__ tb/__pycache__
