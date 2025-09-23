#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2025 Miodrag Milanovic <mmicko@gmail.com>
#
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.generic_platform import *
from litex.build.colognechip.platform import CologneChipPlatform
from litex.build.openfpgaloader import OpenFPGALoader

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk25", 0, Pins("IO_SB_A8"), Misc("SCHMITT_TRIGGER=true")),

    # Leds
    ("user_led_n", 0, Pins("IO_SB_A0")),
    ("user_led_n", 1, Pins("IO_SB_B0")),
    ("user_led_n", 2, Pins("IO_SB_A1")),
    ("user_led_n", 3, Pins("IO_SB_B1")),

    # Button
    ("user_btn", 0, Pins("IO_EA_B4")),
    ("user_btn", 1, Pins("IO_EA_A4")),
    ("user_btn", 2, Pins("IO_EA_B3")),

    # SDRAM
    ("sdram_clock", 0, Pins("IO_WC_A1"), Misc("SLEW=fast")),
    ("sdram", 0,
        Subsignal("a",     Pins(
            "IO_WB_B8 IO_NA_A0 IO_NA_B0 IO_WB_A1 IO_WC_B8 IO_WC_B7 IO_WB_B7 IO_WC_B6",
            "IO_WC_A7 IO_WC_B0 IO_NA_B1 IO_WC_A0 IO_WC_A8")),
        Subsignal("ba",    Pins("IO_WB_A7 IO_WB_A8")),
        Subsignal("cs_n",  Pins("IO_WB_A0")),
        Subsignal("cke",   Pins("IO_WC_B1")),
        Subsignal("ras_n", Pins("IO_WB_A6")),
        Subsignal("cas_n", Pins("IO_WB_B6")),
        Subsignal("we_n",  Pins("IO_WB_B0")),
        Subsignal("dq",    Pins(
            "IO_WB_B4 IO_WB_B2 IO_WB_A4 IO_WB_A2 IO_WB_A5 IO_WB_B5 IO_WB_B1 IO_WB_B3",
            "IO_WC_A6 IO_WC_B4 IO_WC_A5 IO_WC_A4 IO_WC_B3 IO_WC_B2 IO_WC_A2 IO_WC_A3")),
        Subsignal("dm",    Pins("IO_WB_A3 IO_WC_B5"))
    ),

    # SPIFlash
    ("spiflash", 0,
        Subsignal("cs_n", Pins("IO_WA_A8")),
        Subsignal("clk",  Pins("IO_WA_B8"), Misc("SLEW=fast")),
        Subsignal("miso", Pins("IO_WA_B7")),
        Subsignal("mosi", Pins("IO_WA_A7")),
        Subsignal("wp",   Pins("IO_WA_B6")),
        Subsignal("hold", Pins("IO_WA_A6")),
    ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("IO_WA_A8")),
        Subsignal("clk",  Pins("IO_WA_B8"), Misc("SLEW=fast")),
        Subsignal("dq",   Pins("IO_WA_B7 IO_WA_A7 IO_WA_B6 IO_WA_A6")),
    ),

    # SD card w/ SPI interface
    ("spisdcard", 0,
        Subsignal("clk",  Pins("IO_NA_A3")),
        Subsignal("mosi", Pins("IO_NA_B3"), Misc("PULLUP=true")),
        Subsignal("cs_n", Pins("IO_NA_A2"), Misc("PULLUP=true")),
        Subsignal("miso", Pins("IO_NA_A1"), Misc("PULLUP=true")),
    ),

    ("sdcard", 0,
        Subsignal("data", Pins("IO_NA_A1 IO_NB_A5 IO_NA_B2 IO_NA_A2"), Misc("PULLUP=true")),
        Subsignal("cmd",  Pins("IO_NA_B3"), Misc("PULLUP=true")),
        Subsignal("clk",  Pins("IO_NA_A3")),
    ),

    ("eth_refclk", 0, Pins("IO_EB_A3")),

    ("eth_clk", 0,
        Subsignal("tx", Pins(f"IO_EB_B2"), Misc("slew=fast")),
        Subsignal("rx", Pins(f"IO_EB_A7")),
    ),
    ("eth", 0,
        Subsignal("rx_ctl",  Pins(f"IO_EB_A8")),
        Subsignal("rx_data", Pins(f"IO_EB_A0 IO_EB_B0 IO_EB_A1 IO_EB_B1")),
        Subsignal("tx_ctl",  Pins(f"IO_EB_A2"), Misc("slew=fast")),
        Subsignal("tx_data", Pins(f"IO_EB_B5 IO_EB_A5 IO_EB_B4 IO_EB_A4"), Misc("slew=fast")),
        Subsignal("rst_n",   Pins(f"IO_EB_B3")),
        Subsignal("mdc",     Pins(f"IO_EB_B6")),
        Subsignal("mdio",    Pins(f"IO_EB_A6"), Misc("PULLUP=true")),
    ),

    # HDMI
    ("hdmi", 0,
        Subsignal("clk_p",   Pins("IO_SB_A7")),#, Misc("LVDS_BOOST=true")),
        Subsignal("clk_n",   Pins("IO_SB_B7")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data0_p", Pins("IO_SB_A4")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data0_n", Pins("IO_SB_B4")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data1_p", Pins("IO_SB_A5")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data1_n", Pins("IO_SB_B5")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data2_p", Pins("IO_SB_A6")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data2_n", Pins("IO_SB_B6")),#, Misc("LVDS_BOOST=true")),
    ),
]

_io_v0_2 = [
    ("user_led_n", 4, Pins("IO_SB_A2")),
    ("user_led_n", 5, Pins("IO_SB_B2")),
    ("user_led_n", 6, Pins("IO_SB_A3")),
    ("user_led_n", 7, Pins("IO_SB_B3")),

    # Serial.
    ("serial", 0,
        Subsignal("tx", Pins("IO_NB_B5")),
        Subsignal("rx", Pins("IO_NA_B6"))
    ),
]

_io_v0_3 = [
    ("user_led_n", 4, Pins("IO_SB_B2")),
    ("user_led_n", 5, Pins("IO_SB_A2")),
    ("user_led_n", 6, Pins("IO_SB_B3")),
    ("user_led_n", 7, Pins("IO_SB_A3")),

    # Serial.
    ("serial", 0,
        Subsignal("tx", Pins("IO_NA_A4")),
        Subsignal("rx", Pins("IO_NA_B4"))
    ),
]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
]

# Platform -----------------------------------------------------------------------------------------

class Platform(CologneChipPlatform):
    default_clk_name   = "clk25"
    default_clk_period = 1e9/25e6

    def __init__(self, revision="0.3", toolchain="colognechip"):
        assert revision in ["0.2", "0.3"]
        io = _io + {"0.2": _io_v0_2, "0.3": _io_v0_3}[revision]
        CologneChipPlatform.__init__(self, "CCGM1A1", io, _connectors, toolchain=toolchain)

    def create_programmer(self):
        return OpenFPGALoader(cable="dirtyJtag")

    def do_finalize(self, fragment):
        CologneChipPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk25", loose=True), 1e9/25e6)
