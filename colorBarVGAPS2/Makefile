OFL   = openFPGALoader
RM    = rm -rf

CC_TOOL_DIR=$(CC_TOOL)
YOSYS = $(CC_TOOL)/bin/yosys/yosys
P_R   = $(CC_TOOL)/bin/p_r/p_r

PRFLAGS = --verbose -cCP

VGA    = olimex
TOP    = colorBarVGAPS2
CONSTR = $(TOP)_$(VGA).ccf

OBJS += $(TOP).v
OBJS += ../libs/hdl/ps2kbd.v
OBJS += ../libs/hdl/vga.v
OBJS += ../libs/hdl/hex_decoder_v.v
OBJS += ../libs/hdl/ps2mouse.v
OBJS += ../libs/hdl/mousem_v.v
OBJS += ../libs/graphics/vga_core.v
OBJS += ../libs/graphics/color_bar.v
OBJS += ../libs/clocks/gatemate_25MHz_pll.v

YS_OPTS = -D DISP_640x480_60Hz=1

BOARD=olimex_gatemateevb

all:impl
synth: $(TOP)_synth.v
$(TOP)_synth.v: $(OBJS)
	$(YOSYS) -l synth.log $(YS_OPTS) -p 'read -sv $^; synth_gatemate -top $(TOP) -nomx8 -dff -vlog $(TOP)_synth.v'

$(TOP)_00.cfg: $(TOP)_synth.v $(CONSTR)
	$(P_R) -v -i $(TOP)_synth.v -ccf $(CONSTR) -o $(TOP) $(PRFLAGS) > $@.log
impl:$(TOP)_00.cfg

jtag: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b $(BOARD) $^

jtag-flash: $(TOP)_00.cfg
	$(OFL) $(OFLFLAGS) -b $(BOARD) -f --verify $^

clean:
	$(RM) *.log *_synth.v *.history *.txt *.refwire *.refparam
	$(RM) *.refcomp *.pos *.pathes *.path_struc *.net *.id *.prn
	$(RM) *_00.v *.used *.sdf *.place *.pin *.cfg* *.cdf
