#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2023-2025 Gwenhael Goavec-merou<gwenhael.goavec-merou@trabucayre.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.build.generic_platform import *

from litex_boards.platforms import colognechip_gatemate_evb

from litex.build.io import CRG

from litex.soc.cores.clock.colognechip import GateMatePLL
from litex.soc.cores.hyperbus import HyperRAM

from litex.soc.interconnect import wishbone

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.integration.soc import SoCRegion

from litex.build.generic_platform import Pins

from litex.soc.cores.led import LedChaser

from intergalaktik_ulx5m_gs import divide_5

# Customs IOs --------------------------------------------------------------------------------------

_custom_io = [
    # HDMI (Sipeed DVI_PMOD)
    ("hdmi", 0,
        Subsignal("clk_p",   Pins("PMODA:3"), Misc("LVDS_BOOST=true")),
        Subsignal("clk_n",   Pins("PMODA:7"), Misc("LVDS_BOOST=true")),
        Subsignal("data0_p", Pins("PMODA:2"), Misc("LVDS_BOOST=true")),
        Subsignal("data0_n", Pins("PMODA:6"), Misc("LVDS_BOOST=true")),
        Subsignal("data1_p", Pins("PMODA:1"), Misc("LVDS_BOOST=true")),
        Subsignal("data1_n", Pins("PMODA:5"), Misc("LVDS_BOOST=true")),
        Subsignal("data2_p", Pins("PMODA:0"), Misc("LVDS_BOOST=true")),
        Subsignal("data2_n", Pins("PMODA:4"), Misc("LVDS_BOOST=true")),
    ),
]

# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq, with_video_pll=False):
        self.rst    = Signal()
        rst_n       = Signal()
        self.cd_sys = ClockDomain()

        # # #

        # Clk / Rst
        clk10 = platform.request("clk10")
        self.rst = ~platform.request("user_btn_n", 0)

        self.specials += Instance("CC_USR_RSTN", o_USR_RSTN = rst_n)

        # PLL
        self.pll = pll = GateMatePLL(perf_mode="economy")
        self.comb += pll.reset.eq(~rst_n | self.rst)
        pll.register_clkin(clk10, 10e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        platform.add_period_constraint(self.cd_sys.clk, 1e9/sys_clk_freq)

        if with_video_pll:
            self.cd_hdmi   = ClockDomain()
            self.cd_hdmi5x = ClockDomain()

            self.hdmi_pll = hdmi_pll = GateMatePLL(perf_mode="speed")
            self.comb += hdmi_pll.reset.eq(~rst_n | self.rst)

            hdmi_pll.register_clkin(clk10,          10e6)
            hdmi_pll.create_clkout(self.cd_hdmi5x, 125e6)

            self.div5 = ClockDomainsRenamer("hdmi5x")(divide_5("hdmi5x"))
            self.comb += self.cd_hdmi.clk.eq(self.div5.clk_o)
            self.specials += AsyncResetSynchronizer(self.cd_hdmi, ~hdmi_pll.locked)

            platform.add_period_constraint(self.cd_hdmi5x.clk, 1e9/125e6)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=48e6, toolchain="colognechip",
        with_l2_cache       = False,
        with_spi_flash      = False,
        with_video_terminal = False,
        video_mode          = "vga",
        video_serializer    = "custom",
        with_led_chaser     = True,
        **kwargs):

        # Platform ---------------------------------------------------------------------------------
        platform = colognechip_gatemate_evb.Platform(toolchain)
        platform.add_extension(_custom_io)

        # USBUART PMOD as Serial--------------------------------------------------------------------
        platform.add_extension(colognechip_gatemate_evb.usb_pmod_io("PMODB"))
        kwargs["uart_name"] = "usb_uart"

        # CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq, with_video_pll=with_video_terminal)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on GateMate EVB", **kwargs)

        # Video ------------------------------------------------------------------------------------
        if with_video_terminal:
            from gateware.video_colognechip_hdmi_phy import VideoCologneChipHDMIPHY
            hdmi_pads     = platform.request("hdmi")
            self.videophy = VideoCologneChipHDMIPHY(hdmi_pads, clock_domain="hdmi", serializer_mode=video_serializer)
            self.add_video_colorbars(phy=self.videophy, timings="640x480@60Hz", clock_domain="hdmi")
            #self.add_video_terminal(phy=self.videophy, timings="640x480@75Hz", clock_domain="hdmi")

        # HyperRAM ---------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            # HyperRAM Parameters.
            hyperram_device     = "W958D6NW"
            hyperram_size       =  8 * MEGABYTE
            hyperram_cache_size = 16 * KILOBYTE

            # HyperRAM Bus/Slave Interface.
            hyperram_bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
            self.bus.add_slave(name="main_ram", slave=hyperram_bus, region=SoCRegion(origin=self.mem_map["main_ram"], size=hyperram_size, mode="rwx"))

            # HyperRAM L2 Cache.
            if with_l2_cache:
                hyperram_cache = wishbone.Cache(
                    cachesize = hyperram_cache_size//4,
                    master    = hyperram_bus,
                    slave     = wishbone.Interface(data_width=32, address_width=32, addressing="word")
                )
                hyperram_cache = FullMemoryWE()(hyperram_cache)
                self.hyperram_cache = hyperram_cache
                self.add_config("L2_SIZE", hyperram_cache_size)

            # HyperRAM Core.
            self.hyperram = HyperRAM(
                pads         = platform.request("hyperram"),
                latency      = 7,
                latency_mode = "variable",
                sys_clk_freq = sys_clk_freq,
                clk_ratio    = "4:1",
            )
            if with_l2_cache:
                self.comb += self.hyperram_cache.slave.connect(self.hyperram.bus)
            else:
                self.comb += hyperram_bus.connect(self.hyperram.bus)
        # SPI Flash --------------------------------------------------------------------------------
        if with_spi_flash:
            from litespi.modules import MX25R6435F
            from litespi.opcodes import SpiNorFlashOpCodes as Codes
            self.add_spi_flash(mode="4x", module=MX25R6435F(Codes.READ_1_1_1), with_master=False)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.leds = LedChaser(
                pads         = platform.request_all("user_led_n"),
                sys_clk_freq = sys_clk_freq)

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=colognechip_gatemate_evb.Platform, description="LiteX SoC on Gatemate EVB")
    parser.add_target_argument("--sys-clk-freq",        default=24e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--flash",               action="store_true",      help="Flash bitstream.")
    parser.add_target_argument("--with-spi-flash",      action="store_true",      help="Enable SPI Flash (MMAPed).")
    parser.add_target_argument("--with-video-terminal", action="store_true",      help="Enable Video Terminal (HDMI).")
    parser.add_target_argument("--video-serializer",    default="custom",         help="Video Serializer to use (custom, v2, litex).")
    sdopts = parser.target_group.add_mutually_exclusive_group()
    sdopts.add_argument("--with-spi-sdcard",            action="store_true",       help="Enable SPI-mode SDCard support.")
    sdopts.add_argument("--with-sdcard",                action="store_true",       help="Enable SDCard support.")
    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq        = args.sys_clk_freq,
        toolchain           = args.toolchain,
        with_spi_flash      = args.with_spi_flash,
        with_video_terminal = args.with_video_terminal,
        video_serializer    = args.video_serializer,
        **parser.soc_argdict)

    soc.platform.add_extension(colognechip_gatemate_evb.pmods_sdcard_io("PMODA"))
    if args.with_spi_sdcard:
        soc.add_spi_sdcard()
    if args.with_sdcard:
        soc.add_sdcard()

    builder = Builder(soc, **parser.builder_argdict)
    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

    if args.flash:
        from litex.build.openfpgaloader import OpenFPGALoader
        prog = OpenFPGALoader("gatemate_evb_spi")
        prog.flash(0, builder.get_bitstream_filename(mode="flash"))

if __name__ == "__main__":
    main()
