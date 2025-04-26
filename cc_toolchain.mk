OFL         = openFPGALoader
RM          = rm -rf
CC_TOOL_DIR = $(CC_TOOL)
YOSYS       = $(CC_TOOL)/bin/yosys/yosys
P_R         = $(CC_TOOL)/bin/p_r/p_r

YS_PARAMS += -nomx8
PRFLAGS   += --verbose
PRFLAGS   += -cCP

all: impl

synth: $(TOP)_synth.v
$(TOP)_synth.v: $(OBJS)
	$(YOSYS) -ql synth.log $(YS_OPTS) -p 'read_verilog $(YS_SYNTH_PARAMS) -sv $^; synth_gatemate $(YS_PARAMS) -top $(TOP) -vlog $(TOP)_synth.v'

impl: $(TOP)_00.cfg
$(TOP)_00.cfg: $(TOP)_synth.v $(CCF)
	$(P_R) -i $(TOP)_synth.v -ccf $(CCF) -o $(TOP) $(PRFLAGS) > $@.log

load: jtag
jtag: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b $(BOARD) $^

jtag-flash: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b $(BOARD) -f --verify $^

clean:
	$(RM) *.log *_synth.v *.history *.txt *.refwire *.refparam
	$(RM) *.refcomp *.pos *.pathes *.path_struc *.net *.id *.prn
	$(RM) *_00.v *.used *.sdf *.place *.pin *.cfg* *.cdf *.idh
	$(RM) *.bit *.json
