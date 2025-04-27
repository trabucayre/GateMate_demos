VGA       ?= digilent
TGT        = $(VGA)
TOOLCHAIN ?= colognechip
TOP        = colorBarVGA
CCF        = $(TOP)_$(VGA).ccf

OBJS += $(TOP).v
OBJS += ../libs/graphics/vga_core.v
OBJS += ../libs/graphics/color_bar.v
OBJS += ../libs/clocks/gatemate_25MHz_pll.v

YS_OPTS= -D DISP_640x480_60Hz=1

ifeq ($(VGA), olimex)
BOARD=olimex_gatemateevb
else
BOARD=gatemate_evb_jtag
endif

ifeq ($(TOOLCHAIN), colognechip)
-include ../cc_toolchain.mk
else
-include ../nextpnr_mk
endif
