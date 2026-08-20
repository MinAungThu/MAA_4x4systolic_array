# cocotb + Verilator test runner.
#   make ws   -> weight-stationary array test
# Dimensions overridable: make ws R=8 C=8 M=10

TOPLEVEL_LANG = verilog
SIM ?= icarus
WAVES ?= 0

RTL = $(CURDIR)/../rtl
export PYTHONPATH := $(CURDIR):$(CURDIR)/../model:$(PYTHONPATH)

ifeq ($(SIM),icarus)
    COMPILE_ARGS += -g2012
endif
ifeq ($(WAVES),1)
    EXTRA_ARGS += --trace --trace-structs
endif

.PHONY: ws clean

ws:
	$(MAKE) sim_ws

R ?= 4
C ?= 4
DATA_W ?= 8
ACC_W ?= 32

sim_ws: VERILOG_SOURCES = $(CURDIR)/_timescale.v $(RTL)/pe_ws.v $(RTL)/array_ws.v
sim_ws: TOPLEVEL = array_ws
sim_ws: MODULE   = test_ws
sim_ws: COMPILE_ARGS += -Parray_ws.R=$(R) -Parray_ws.C=$(C) -Parray_ws.DATA_W=$(DATA_W) -Parray_ws.ACC_W=$(ACC_W)
sim_ws: run


run:
	rm -rf sim_build results.xml
	$(MAKE) -f $(shell cocotb-config --makefiles)/Makefile.sim \
		SIM=$(SIM) TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
		VERILOG_SOURCES="$(VERILOG_SOURCES)" \
		TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) \
		COMPILE_ARGS="$(COMPILE_ARGS)" \
		EXTRA_ARGS="$(EXTRA_ARGS)"

clean:
	rm -rf sim_build results.xml __pycache__ dump.vcd
