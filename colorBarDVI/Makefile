DVI   ?= colognechip
TOOLCHAIN ?= nextpnr
TOP    = colorBarDVI
CCF    = $(DVI).ccf

OBJS += $(TOP).v
OBJS += ../libs/graphics/color_bar_shade.v
OBJS += ../libs/clocks/gatemate_25MHz_125MHz_pll.v
OBJS += ../libs/graphics/vga_core.v
OBJS += ../libs/graphics/dvi_core.v
OBJS += ../libs/graphics/tmds_encoder.v
OBJS += ../libs/ios/serializer_gatemate_10_to_1_generic_ddr.v

YS_OPTS = -D DISP_640x480_60Hz=1
NEXTPNR_OPTS = --freq 125

# Machdyne DDMI Pmod have _p/_n opposite to PMOD
ifeq ($(DVI), machdyne)
	YS_OPTS += -D PN_SWAP=1
endif

BOARD=gatemate_evb_jtag

ifeq ($(TOOLCHAIN), colognechip)
-include ../cc_toolchain.mk
else
-include ../nextpnr_mk
endif
