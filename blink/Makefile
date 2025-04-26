TGT       ?= gatemate
TOOLCHAIN ?= colognechip
TOP        = blinky
CCF        = $(TOP)_$(TGT).ccf
OBJS       = blinky.v

ifeq ($(TGT), olimex)
BOARD           = olimex_gatemateevb
YS_SYNTH_PARAMS = -DN_LEDS=1
else
BOARD           = gatemate_evb_jtag
YS_SYNTH_PARAMS = -DN_LEDS=8
endif


ifeq ($(TOOLCHAIN), colognechip)
-include ../cc_toolchain.mk
else
-include ../nextpnr_mk
endif

test:
	echo $(N_LEDS)
	echo $(YS_SYNTH_PARAMS)
	echo $(CCF)
