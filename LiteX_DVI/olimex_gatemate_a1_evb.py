#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2024-2025 Gwenhael Goavec-merou<gwenhael.goavec-merou@trabucayre.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.build.generic_platform import *

from litex_boards.platforms import olimex_gatemate_a1_evb

from litex.build.io import CRG

from litex.soc.cores.clock.colognechip import GateMatePLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex.build.generic_platform import Pins

from litex.soc.cores.led import LedChaser
from litex.soc.cores.video import VideoVGAPHY

from intergalaktik_ulx5m_gs import divide_5

# Customs IOs --------------------------------------------------------------------------------------

_custom_io = [
    # HDMI
    # https://github.com/intergalaktik/Extension_Boards_for_Olimex_GateMate/tree/main/dvi
    ("gpdi", 0,
        Subsignal("buck_en", Pins( f"bank_nb1:4")),#,  Misc("LVDS_BOOST=true")),
        Subsignal("clk_p",   Pins(f"bank_nb1:11")),#, Misc("LVDS_BOOST=true")),
        Subsignal("clk_n",   Pins(f"bank_nb1:12")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data0_p", Pins( f"bank_nb1:9")),#,  Misc("LVDS_BOOST=true")),
        Subsignal("data0_n", Pins(f"bank_nb1:10")),#, Misc("LVDS_BOOST=true")),
        Subsignal("data1_p", Pins( f"bank_nb1:7")),#,  Misc("LVDS_BOOST=true")),
        Subsignal("data1_n", Pins( f"bank_nb1:8")),#,  Misc("LVDS_BOOST=true")),
        Subsignal("data2_p", Pins( f"bank_nb1:5")),#,  Misc("LVDS_BOOST=true")),
        Subsignal("data2_n", Pins( f"bank_nb1:6")),#,  Misc("LVDS_BOOST=true")),
    )
]

# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq, with_video_terminal=False, video_mode="vga"):
        self.rst    = Signal()
        rst_n       = Signal()
        self.cd_sys = ClockDomain()
        if with_video_terminal:
            self.cd_vga = ClockDomain()

        # # #

        # Clk / Rst
        clk10    = platform.request("clk0")
        self.rst = ~platform.request("user_btn_n", 0)

        self.specials += Instance("CC_USR_RSTN", o_USR_RSTN = rst_n)

        # PLL
        self.pll = pll = GateMatePLL(perf_mode="economy")
        self.comb += pll.reset.eq(~rst_n | self.rst)
        pll.register_clkin(clk10, 10e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        platform.add_period_constraint(self.cd_sys.clk, 1e9/sys_clk_freq)

        if with_video_terminal:
            if video_mode == "vga":
                self.pll_video = pll_video = GateMatePLL(perf_mode="economy")
                self.comb += pll_video.reset.eq(~rst_n | self.rst)
                pll_video.register_clkin(clk10, 10e6)
                pll_video.create_clkout(self.cd_vga, 65e6)
                platform.add_period_constraint(self.cd_vga.clk, 1e9/65e6)
            else:
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
    def __init__(self, sys_clk_freq=24e6, toolchain="colognechip",
        with_video_terminal = False,
        video_mode          = "gpdi",
        video_serializer    = "custom",
        with_ethernet       = False,
        with_etherbone      = False,
        eth_ip              = "192.168.1.50",
        remote_ip           = None,
        with_led_chaser     = True,
        **kwargs):
        platform = olimex_gatemate_a1_evb.Platform(toolchain)
        platform.add_extension(_custom_io)

        # CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq, with_video_terminal, video_mode = video_mode)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on GateMate EVB", **kwargs)

        # Video Terminal ---------------------------------------------------------------------------
        if with_video_terminal:
            if video_mode == "vga":
                vga_pads = platform.request("vga")
                self.videophy = VideoVGAPHY(vga_pads, clock_domain="vga")
                self.add_video_terminal(phy=self.videophy, timings="1024x768@60Hz", clock_domain="vga")
                #self.add_video_colorbars(phy=self.videophy, timings="1024x768@60Hz", clock_domain="vga")
            else:
                from gateware.video_colognechip_hdmi_phy import VideoCologneChipHDMIPHY
                hdmi_pads     = platform.request("gpdi")
                self.videophy = VideoCologneChipHDMIPHY(hdmi_pads, clock_domain="hdmi", serializer_mode=video_serializer)
                self.add_video_colorbars(phy=self.videophy, timings="640x480@60Hz", clock_domain="hdmi")
                #self.add_video_terminal(phy=self.videophy, timings="1024x768@60Hz", clock_domain="hdmi")
                self.comb += hdmi_pads.buck_en.eq(1)

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.leds = LedChaser(
                pads         = platform.request_all("user_led_n"),
                sys_clk_freq = sys_clk_freq)

        # Ethernet / Etherbone ---------------------------------------------------------------------
        if with_ethernet or with_etherbone:
            from litex.build.generic_platform import Subsignal
            def eth_lan8720_rmii_pmod_io(pmod):
                # Lan8720 RMII PHY "PMOD": To be used as a PMOD, MDIO should be disconnected and TX1 connected to PMOD8 IO.
                return [
                    ("eth_rmii_clocks", 0,
                        Subsignal("ref_clk", Pins(f"{pmod}:6")),
                    ),
                    ("eth_rmii", 0,
                        Subsignal("rx_data", Pins(f"{pmod}:5 {pmod}:1")),
                        Subsignal("crs_dv",  Pins(f"{pmod}:2")),
                        Subsignal("tx_en",   Pins(f"{pmod}:4")),
                        Subsignal("tx_data", Pins(f"{pmod}:0 {pmod}:7")),
                    ),
                ]
            platform.add_extension(eth_lan8720_rmii_pmod_io("PMOD"))

            from liteeth.phy.rmii import LiteEthPHYRMII
            self.ethphy = LiteEthPHYRMII(
                clock_pads = platform.request("eth_rmii_clocks"),
                pads       = platform.request("eth_rmii"),
                refclk_cd  = None
            )

        if with_ethernet:
            self.add_ethernet(phy=self.ethphy, local_ip=eth_ip, remote_ip=remote_ip, software_debug=False)
        if with_etherbone:
            self.add_etherbone(phy=self.ethphy, ip_address=eth_ip)

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=olimex_gatemate_a1_evb.Platform, description="LiteX SoC on Olimex Gatemate A1 EVB")
    parser.add_target_argument("--sys-clk-freq",        default=24e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--with-video-terminal", action="store_true",      help="Enable Video Terminal (VGA/HDMI).")
    parser.add_target_argument("--video-mode",          default="vga",            help="Video Serializer to use (vga or gpdi).")
    parser.add_target_argument("--video-serializer",    default="custom",         help="Video Serializer to use (custom, v2, litex).")
    parser.add_target_argument("--flash",               action="store_true",      help="Flash bitstream.")
    pmodopts = parser.target_group.add_mutually_exclusive_group()
    pmodopts.add_argument("--with-spi-sdcard",          action="store_true",      help="Enable SPI-mode SDCard support.")
    pmodopts.add_argument("--with-sdcard",              action="store_true",      help="Enable SDCard support.")
    pmodopts.add_argument("--with-ethernet",            action="store_true",      help="Enable Ethernet support.")
    pmodopts.add_argument("--with-etherbone",           action="store_true",      help="Enable Etherbone support.")
    parser.add_target_argument("--eth-ip",              default="192.168.1.50",   help="Ethernet/Etherbone IP address.")
    parser.add_target_argument("--remote-ip",           default="192.168.1.100",  help="Remote IP address of TFTP server.")

    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq        = args.sys_clk_freq,
        toolchain           = args.toolchain,
        with_video_terminal = args.with_video_terminal,
        video_mode          = args.video_mode,
        video_serializer    = args.video_serializer,
        with_ethernet       = args.with_ethernet,
        with_etherbone      = args.with_etherbone,
        eth_ip              = args.eth_ip,
        remote_ip           = args.remote_ip,
        **parser.soc_argdict)

    soc.platform.add_extension(olimex_gatemate_a1_evb._pmods_io)
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
        prog = soc.platform.create_programmer()
        prog.flash(0, builder.get_bitstream_filename(mode="flash"))

if __name__ == "__main__":
    main()
