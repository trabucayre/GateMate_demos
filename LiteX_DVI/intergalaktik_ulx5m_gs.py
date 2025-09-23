#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2025 Miodrag Milanovic <mmicko@gmail.com>
#
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

import intergalaktik_ulx5m_gs_platform

from litex.build.generic_platform import *

from litex.soc.cores.clock.colognechip import GateMatePLL
from litex.soc.cores.video import *

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.build.io import DDROutput

from litex.soc.cores.led import LedChaser

from litedram.modules import IS42S16160, IS42S16320

from litedram.phy import GENSDRPHY

from gateware.video_colognechip_hdmi_phy import VideoCologneChipHDMIPHY


# Division by 5 module -----------------------------------------------------------------------------

class divide_5(LiteXModule):
    def __init__(self, clock_domain="sys"):
        self.clk_o = Signal()

        # # #

        d    = Signal(3)
        qbar = Signal(3)

        q      = Signal(3)
        qtemp  = Signal(reset_less=True)

        self.comb += [
            qbar[0].eq(~q[2]),
            qbar[1].eq(~q[1]),
            qbar[2].eq(~q[0]),

            d[0].eq(qbar[2] & qbar[0]),
            d[1].eq((q[1] & qbar[0]) | (qbar[1] & q[0])),
            d[2].eq(q[1] & q[0]),
        ]

        self.sync += q.eq(d)

        self.specials += Instance("CC_DFF",
            p_CLK_INV = 1,
            p_EN_INV  = 0,
            p_SR_INV  = 0,
            p_SR_VAL  = 0,
            i_D       = q[1],
            i_CLK     = ClockSignal(clock_domain),
            i_EN      = 1,
            i_SR      = 0,
            o_Q       = qtemp,
        )

        self.comb += self.clk_o.eq(q[1] | qtemp)


# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq, with_eth, with_video_pll=False):
        self.rst       = Signal()
        rst_n          = Signal()
        self.cd_sys    = ClockDomain()
        self.cd_sys_ps = ClockDomain()

        # # #

        # Clk / Rst
        clk25    = platform.request("clk25")
        self.rst = ~platform.request("user_btn", 0)

        self.specials += Instance("CC_USR_RSTN", o_USR_RSTN = rst_n)

        # PLL
        self.pll = pll = GateMatePLL(perf_mode="speed")
        self.comb += pll.reset.eq(~rst_n | self.rst)

        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)
        platform.add_period_constraint(self.cd_sys.clk, 1e9/sys_clk_freq)
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys_ps"))

        if with_eth:
            self.comb += platform.request("eth_refclk" ).eq(clk25)

        if with_video_pll:
            self.cd_hdmi   = ClockDomain()
            self.cd_hdmi5x = ClockDomain()

            self.hdmi_pll = hdmi_pll = GateMatePLL(perf_mode="speed")
            self.comb += hdmi_pll.reset.eq(~rst_n | self.rst)

            hdmi_pll.register_clkin(clk25,          25e6)
            hdmi_pll.create_clkout(self.cd_hdmi5x, 125e6)

            self.div5 = ClockDomainsRenamer("hdmi5x")(divide_5("hdmi5x"))
            self.comb += self.cd_hdmi.clk.eq(self.div5.clk_o)
            self.specials += AsyncResetSynchronizer(self.cd_hdmi, ~hdmi_pll.locked)

            platform.add_period_constraint(self.cd_hdmi.clk,   1e9/25e6)
            platform.add_period_constraint(self.cd_hdmi5x.clk, 1e9/125e6)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, revision="0.3", sys_clk_freq=20e6, toolchain="colognechip",
        with_spi_flash      = False,
        with_ethernet       = False,
        with_etherbone      = False,
        eth_ip              = "192.168.1.50",
        remote_ip           = "192.168.1.4",
        with_video_terminal = False,
        video_serializer    = "custom",
        with_led_chaser     = True,
        **kwargs):
        platform = intergalaktik_ulx5m_gs_platform.Platform(revision, toolchain)

        # CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq, with_ethernet or with_etherbone, with_video_pll=with_video_terminal)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on ULX5M-GS", **kwargs)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.leds = LedChaser(
                pads         = platform.request_all("user_led_n"),
                sys_clk_freq = sys_clk_freq)

        # DRAM -------------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            self.sdrphy = GENSDRPHY(platform.request("sdram"), sys_clk_freq)

            self.add_sdram("sdram",
                phy           = self.sdrphy,
                module        = IS42S16160(sys_clk_freq, "1:1"),
                l2_cache_size = kwargs.get("l2_size", 0)
            )

        # SPI Flash --------------------------------------------------------------------------------
        if with_spi_flash:
            from litespi.modules import IS25LP128
            from litespi.opcodes import SpiNorFlashOpCodes as Codes
            self.add_spi_flash(mode="4x", module=IS25LP128(Codes.READ_1_1_4), with_master=False)

        # Video ------------------------------------------------------------------------------------
        if with_video_terminal:
            hdmi_pads     = platform.request("hdmi")
            self.videophy = VideoCologneChipHDMIPHY(hdmi_pads, clock_domain="hdmi", serializer_mode=video_serializer)
            self.add_video_colorbars(phy=self.videophy, timings="640x480@60Hz", clock_domain="hdmi")
            #self.add_video_terminal(phy=self.videophy, timings="640x480@75Hz", clock_domain="hdmi")


        if with_ethernet or with_etherbone:
            from gatematergmii import LiteEthPHYRGMII
            self.ethphy = LiteEthPHYRGMII(
                clock_pads         = platform.request("eth_clk"),
                pads               = platform.request("eth"),
                with_hw_init_reset = True,
            )

            if with_ethernet:
                self.add_ethernet(phy=self.ethphy, local_ip=eth_ip, remote_ip=remote_ip, software_debug=True)
            if with_etherbone:
                self.add_etherbone(phy=self.ethphy, ip_address=eth_ip)

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=intergalaktik_ulx5m_gs_platform.Platform, description="LiteX SoC on ULX5M-GS")
    parser.add_target_argument("--sys-clk-freq",   default=20e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--revision",       default="0.3",            help="Board revision (0.2 or 0.3).")
    parser.add_target_argument("--with-spi-flash", action="store_true",      help="Enable SPI Flash (MMAPed).")
    parser.add_target_argument("--with-video-terminal", action="store_true",      help="Enable Video Terminal (HDMI).")
    parser.add_target_argument("--video-serializer",    default="custom",         help="Video Serializer to use (custom, v2, litex).")
    sdopts = parser.target_group.add_mutually_exclusive_group()
    sdopts.add_argument("--with-spi-sdcard",       action="store_true",      help="Enable SPI-mode SDCard support.")
    sdopts.add_argument("--with-sdcard",           action="store_true",      help="Enable SDCard support.")

    parser.set_defaults(cpu_type="femtorv")
    args = parser.parse_args()

    soc = BaseSoC(
        revision            = args.revision,
        sys_clk_freq        = args.sys_clk_freq,
        toolchain           = args.toolchain,
        with_spi_flash      = args.with_spi_flash,
        with_video_terminal = args.with_video_terminal,
        video_serializer    = args.video_serializer,
        **parser.soc_argdict)

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

if __name__ == "__main__":
    main()
