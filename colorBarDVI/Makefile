OFL   = openFPGALoader
RM    = rm -rf

CC_TOOL_DIR=$(CC_TOOL)
YOSYS = $(CC_TOOL)/bin/yosys/yosys
P_R   = $(CC_TOOL)/bin/p_r/p_r

YS_OPTS = -nomx8
PRFLAGS = --verbose
PRFLAGS += -cCP

TOP    = colorBarDVI
CONSTR = $(TOP).ccf

OBJS += $(TOP).v
OBJS += ../libs/graphics/color_bar_shade.v
OBJS += ../libs/clocks/gatemate_25MHz_125MHz_pll.v
OBJS += ../libs//graphics/vga_core.v
OBJS += ../libs//graphics/dvi_core.v
OBJS += ../libs//graphics/tmds_encoder.v
OBJS += ../libs//ios/serializer_gatemate_10_to_1_generic_ddr.v

YS_OPTS = -D DISP_640x480_60Hz=1

all:impl
synth: $(TOP)_synth.v
$(TOP)_synth.v: $(OBJS)
	$(YOSYS) -ql synth.log $(YS_OPTS) -p 'read -sv $^; synth_gatemate -top $(TOP) -nomx8 -vlog $(TOP)_synth.v'

$(TOP)_00.cfg: $(TOP)_synth.v $(CONSTR)
	$(P_R) -i $(TOP)_synth.v -ccf $(CONSTR) -o $(TOP) $(PRFLAGS) > $@.log
impl:$(TOP)_00.cfg

jtag: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b gatemate_evb_jtag $^

jtag-flash: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b gatemate_evb_jtag -f --verify $^

clean:
	$(RM) *.log *_synth.v *.history *.txt *.refwire *.refparam
	$(RM) *.refcomp *.pos *.pathes *.path_struc *.net *.id *.prn
	$(RM) *_00.v *.used *.sdf *.place *.pin *.cfg* *.cdf *.idh
