#
# This file is part of LiteEth.
#
# Copyright (c) 2025 Patrick Urban <support@colognechip.com>
# Based on ecp5rgmii:
#   Copyright (c) 2019-2023 Florent Kermarrec <florent@enjoy-digital.fr>
#   Copyright (c) 2020 Shawn Hoffman <godisgovernment@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

# RGMII PHY for Cologne Chip GateMate FPGA

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.gen import *

from litex.build.io import DDROutput, DDRInput
from litex.soc.cores.clock.colognechip import GateMatePLL

from liteeth.common import *
from liteeth.phy.common import *


# Timing data for each performance mode
iodly_timing = {
    "speed":    {"best": 30e-12, "typ": 38e-12, "worst": 50e-12},
    "economy":  {"best": 38e-12, "typ": 50e-12, "worst": 65e-12},
    "lowpower": {"best": 50e-12, "typ": 65e-12, "worst": 85e-12},
}

class LiteEthPHYRGMIITX(LiteXModule):
    def __init__(self, pads):
        self.sink = sink = stream.Endpoint(eth_phy_description(8))

        tx_ctl_h = Signal()
        tx_ctl_l = Signal()
        tx_ctl_oddr = Signal()

        tx_ctl_hold = Signal()

        self.sync += [
            tx_ctl_h.eq(sink.valid),
            tx_ctl_l.eq(sink.valid),
        ]

        self.specials += [
            DDROutput(
                clk = ClockSignal("eth_tx"),
                i1  = tx_ctl_h,
                i2  = tx_ctl_l,
                o   = tx_ctl_oddr,
            ),
            Instance("CC_OBUF",
                p_DELAY_OBF = 0,
                p_SLEW      = "fast",
                i_A         = tx_ctl_oddr,
                o_O         = pads.tx_ctl,
            )
        ]

        tx_data_h = Signal(4)
        tx_data_l = Signal(4)
        tx_data_oddr = Signal(4)

        for i in range(4):
            self.sync += [
                tx_data_h[i].eq(sink.data[i + 0]),
                tx_data_l[i].eq(sink.data[i + 4]),
            ]

        for i in range(4):
            self.specials += [
                DDROutput(
                    clk = ClockSignal("eth_tx"),
                    i1  = tx_data_h[i],
                    i2  = tx_data_l[i],
                    o   = tx_data_oddr[i],
                ),
                Instance("CC_OBUF",
                    p_DELAY_OBF = 0,
                    p_SLEW      = "fast",
                    i_A         = tx_data_oddr[i],
                    o_O         = pads.tx_data[i],
                )
            ]

        self.comb += sink.ready.eq(1)

class LiteEthPHYRGMIIRX(LiteXModule):
    def __init__(self, pads, rx_delay=0e-9, perf_mode="speed", corner="worst", with_inband_status=True):
        self.source = source = stream.Endpoint(eth_phy_description(8))

        if with_inband_status:
            self.inband_status = CSRStatus(fields=[
                CSRField("link_status", size=1, values=[
                    ("``0b0``", "Link down."),
                    ("``0b1``", "Link up."),
                ]),
                CSRField("clock_speed", size=2, values=[
                    ("``0b00``", "2.5MHz   (10Mbps)."),
                    ("``0b01``", "25MHz   (100MBps)."),
                    ("``0b10``", "125MHz (1000MBps)."),
                ]),
                CSRField("duplex_status", size=1, values=[
                    ("``0b0``", "Half-duplex."),
                    ("``0b1``", "Full-duplex."),
                ]),
            ])

        self._iodly = iodly_timing[perf_mode.lower()][corner.lower()]
        rx_delay_taps = int(rx_delay/self._iodly)
        assert rx_delay_taps <= 16

        rx_ctl = Signal(2)
        rx_ctl_delayf  = Signal()

        self.specials += [
            Instance("CC_IBUF",
                p_DELAY_IBF = rx_delay_taps,
                i_I         = pads.rx_ctl,
                o_Y         = rx_ctl_delayf,
            ),
            DDRInput(
                clk = ClockSignal("eth_rx"),
                i   = rx_ctl_delayf,
                o1  = rx_ctl[0],
                o2  = rx_ctl[1]
            )
        ]
        self.comb += rx_ctl.eq(rx_ctl_delayf)

        rx_ctl_d = Signal()
        self.sync += rx_ctl_d.eq(rx_ctl[0] & rx_ctl[1])

        rx_data_h = Signal(4)
        rx_data_l = Signal(4)
        rx_data_delayf = Signal(4)

        for i in range(4):
            self.specials += [
                Instance("CC_IBUF",
                    p_DELAY_IBF = rx_delay_taps,
                    i_I         = pads.rx_data[i],
                    o_Y         = rx_data_delayf[i]),
                DDRInput(
                    clk = ClockSignal("eth_rx"),
                    i   = rx_data_delayf[i],
                    o1  = rx_data_h[i],
                    o2  = rx_data_l[i]
                )
            ]

        rx_data_lsb = Signal(4)
        rx_data_msb = Signal(4)

        for i in range(4):
            self.comb += rx_data_msb[i + 0].eq(rx_data_l[i])
            self.sync += rx_data_lsb[i + 0].eq(rx_data_h[i])

        last = Signal()
        self.sync += [
            last.eq(~rx_ctl & rx_ctl_d),
            source.valid.eq(rx_ctl_d),
            source.data.eq(Cat(rx_data_lsb, rx_data_msb)),
        ]
        self.comb += source.last.eq(last)

        #if with_inband_status:
        #    self.sync += [
        #        If(rx_ctl == 0b00,
        #            self.inband_status.fields.link_status.eq(  rx_data[0]),
        #            self.inband_status.fields.clock_speed.eq(  rx_data[1:3]),
        #            self.inband_status.fields.duplex_status.eq(rx_data[3]),
        #        )
        #    ]

class LiteEthPHYRGMIICRG(LiteXModule):
    def __init__(self, clock_pads, pads, with_hw_init_reset, hw_reset_cycles=256, tx_delay=0e-9, perf_mode="speed", corner="worst", tx_clk=None):
        self._reset = CSRStorage()

        # RX Clock
        self.cd_eth_rx = ClockDomain()
        self.comb += self.cd_eth_rx.clk.eq(clock_pads.rx)

        # TX Clock
        self.cd_eth_tx = ClockDomain()
        self.cd_eth_tx_delayed = ClockDomain(reset_less=True)

        if isinstance(tx_clk, Signal):
            self.comb += self.cd_eth_tx.clk.eq(tx_clk)
        else:
            self.comb += self.cd_eth_tx.clk.eq(self.cd_eth_rx.clk)

        self._iodly = iodly_timing[perf_mode.lower()][corner.lower()]
        tx_delay_taps = int(tx_delay/self._iodly)
        assert tx_delay_taps <= 16

        eth_tx_clk_o = Signal()
        self.specials += [
            DDROutput(
                clk = ClockSignal("eth_tx"),
                i1  = 0,
                i2  = 1,
                o   = eth_tx_clk_o,
            ),
            Instance("CC_OBUF",
                p_DELAY_OBF = tx_delay_taps,
                p_SLEW      = "fast",
                i_A         = eth_tx_clk_o,
                o_O         = clock_pads.tx,
            ),
        ]

        # Reset
        self.reset = reset = Signal()
        if with_hw_init_reset:
            self.hw_reset = LiteEthPHYHWReset(cycles=hw_reset_cycles)
            self.comb += reset.eq(self._reset.storage | self.hw_reset.reset)
        else:
            self.comb += reset.eq(self._reset.storage)
        if hasattr(pads, "rst_n"):
            self.comb += pads.rst_n.eq(~reset)
        self.specials += [
            AsyncResetSynchronizer(self.cd_eth_tx, reset),
            AsyncResetSynchronizer(self.cd_eth_rx, reset),
        ]

class LiteEthPHYRGMII(LiteXModule):
    dw          = 8
    tx_clk_freq = 25e6
    rx_clk_freq = 25e6
    def __init__(self, clock_pads, pads, with_hw_init_reset=True, hw_reset_cycles=256,
        tx_delay           = 0.0e-10, # 7.5e-10,
        rx_delay           = 0.0e-10, # 7.5e-10
        perf_mode          = "speed",
        corner             = "worst",
        with_inband_status = True,
        tx_clk             = None,
        ):
        self.crg = LiteEthPHYRGMIICRG(clock_pads, pads, with_hw_init_reset, hw_reset_cycles, tx_delay, perf_mode, corner, tx_clk)
        self.tx  = ClockDomainsRenamer("eth_tx")(LiteEthPHYRGMIITX(pads))
        self.rx  = ClockDomainsRenamer("eth_rx")(LiteEthPHYRGMIIRX(pads, rx_delay, perf_mode, corner, with_inband_status))
        self.sink, self.source = self.tx.sink, self.rx.source

        if hasattr(pads, "mdc"):
            self.mdio = LiteEthPHYMDIO(pads)
