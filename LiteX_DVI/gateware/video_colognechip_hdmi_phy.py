from migen import *
from migen.genlib.cdc import MultiReg
 
from litex.gen import *

from litex.build.io import DDROutput
 
from litex.soc.interconnect.csr import *
from litex.soc.interconnect import stream
from litex.soc.cores.code_tmds import TMDSEncoder

from litex.soc.cores.video import video_data_layout, _dvi_c2d, VideoHDMI10to1Serializer
 
# HDMI (CologneChip).

class VideoCologneChipHDMI10to1Serializer2(LiteXModule):
    def __init__(self, data_i, data_o, clock_domain):
        # Clock Domain Crossing.
        self.cdc = stream.ClockDomainCrossing([("data", 10)], cd_from=clock_domain, cd_to=clock_domain + "5x", depth=8, buffered=True)
        self.comb += self.cdc.sink.valid.eq(1)
        self.comb += self.cdc.sink.data.eq(data_i)
                             
        # 10:2 Converter.   
        self.converter = ClockDomainsRenamer(clock_domain + "5x")(stream.Converter(nbits_from=10, nbits_to=2, reverse=False))

        self.comb += self.cdc.source.connect(self.converter.sink)
                       
        # 2:1 Output DDR.         
        self.comb += self.converter.source.ready.eq(1)
        self.specials += DDROutput(
            clk = ClockSignal(clock_domain + "5x"),
            i1  = self.converter.source.data[0],
            i2  = self.converter.source.data[1],
            o   = data_o,    
        )                    

class VideoCologneChipHDMI10to1Serializer(LiteXModule):
    def __init__(self, data_i, data_o, clock_domain):

        # # #

        dat_pos        = Signal(10);
 
        # detect ref_clk_i edge
        ref_clk_i_d    = Signal()
        ref_clk_i_s    = Signal()
        ref_clk_i_edge = Signal()

        self.sync.pix += ref_clk_i_s.eq(~ref_clk_i_s)
 
        self.sync += [
            ref_clk_i_d.eq(ref_clk_i_s),
            ref_clk_i_edge.eq(ref_clk_i_d ^ ref_clk_i_s),

            If(ref_clk_i_edge,
                dat_pos.eq(data_i)
            ).Else(
                dat_pos.eq(Cat(dat_pos[2:10], Constant(0,2)))
            )
        ]

        self.specials += DDROutput(
            clk = ClockSignal(clock_domain + "5x"),
            i1  = dat_pos[0],
            i2  = dat_pos[1],
            o   = data_o,
        )

class VideoCologneChipHDMIPHY(LiteXModule):
    def __init__(self, pads, clock_domain="sys", pn_swap=[], serializer_mode="custom"):
        self.sink = sink = stream.Endpoint(video_data_layout)

        assert serializer_mode in ["custom", "v2", "litex"]

        # # #

        serializer_cls = {
            "custom": VideoCologneChipHDMI10to1Serializer,
            "v2"    : VideoCologneChipHDMI10to1Serializer2,
            "litex" : VideoHDMI10to1Serializer,
        }[serializer_mode]

        # Always ack Sink, no backpressure.
        self.comb += sink.ready.eq(1)

        # Clocking + Differential Signaling.
        clk_o = Signal()
        if serializer_mode == "custom":
            pix_clk = ClockSignal(clock_domain)
            self.comb += clk_o.eq(pix_clk if "clk" not in pn_swap else ~pix_clk)
        else:
            clk_pattern = {True: 0b1111100000, False: 0b0000011111}[True]
            serializer = serializer_cls(
                data_i       = clk_pattern,
                data_o       = clk_o,
                clock_domain = clock_domain,
            )
            if serializer_mode == "custom":
                serializer = ClockDomainsRenamer({"pix": clock_domain, "sys": f"{clock_domain}5x"})(serializer)
            self.add_module(name=f"clk_serializer", module=serializer)

        self.specials += Instance("CC_LVDS_OBUF",
            i_A   = clk_o,
            o_O_P = pads.clk_p,
            o_O_N = pads.clk_n,
        )

        # Encode/Serialize Datas.
        for color, channel in _dvi_c2d.items():
            # TMDS Encoding.
            encoder = ClockDomainsRenamer(clock_domain)(TMDSEncoder())
            self.add_module(name=f"{color}_encoder", module=encoder)
            self.comb += encoder.d.eq(getattr(sink, color))
            self.comb += encoder.c.eq(Cat(sink.hsync, sink.vsync) if channel == 0 else 0)
            self.comb += encoder.de.eq(sink.de)

            # 10:1 Serialization + Pseudo Differential Signaling.
            data_i = encoder.out if color not in pn_swap else ~encoder.out
            data_o = Signal()
            serializer = serializer_cls(
                data_i       = data_i,
                data_o       = data_o,
                clock_domain = clock_domain,
            )
            if serializer_mode == "custom":
                serializer = ClockDomainsRenamer({"pix": clock_domain, "sys": f"{clock_domain}5x"})(serializer)
            self.add_module(name=f"{color}_serializer", module=serializer)

            pad_p = getattr(pads, f"data{channel}_p")
            pad_n = getattr(pads, f"data{channel}_n")
            self.specials += Instance("CC_LVDS_OBUF",
                i_A   = data_o,
                o_O_P = pad_p,
                o_O_N = pad_n
            )
