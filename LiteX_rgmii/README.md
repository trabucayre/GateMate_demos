# LiteX RGMII tests

## Build

```bash
./intergalaktik_ulx5m_gs.py --build --load [--with-etherbone] [--with-ethernet] [--with-eth-debug] [--cable]
```

Where:

- `--with-ethernet` to enable ethernet support
- `--with-etherbone` to enable etherbone support
- `--with-eth-debug` to enable PHY debug (MDIO)
- `--cable` must be adapted to the JTAG probe in uses (default tigard. see `openFPGALoader --list-cables`)

Additionals options:

- `--eth-ip` target IP
- `--remote-ip` host (computer IP)

## Debug MDIO communication

```bash
./intergalaktik_ulx5m_gs.py --with-eth-debug --cpu-type None --uart-name uartbone --disable-sdram --disable-leds --csr-csv csr.csv --build --load
```

In a first terminal:

```bash
litex_server --uart --uart-name /dev/ttyUSB1
```

Please adapts `dev/ttyUSB1` to the UART connected to the target

In a second terminal to dump registers:

```bash
./test_mdio.py dump phyadr count

```

Where:
- `phyadr` is a PHY address
- `count` is the number of registers to dump

`MDC`/`MDIO` signals are copied in RPI header IOs:
- `mdc`: `GPIO26`
- `mdio_i`: `GPIO19` (from PHY to FPGA
- `mdio_o`: `GPIO13` (from FPGA to PHY
- `mdio_io`: `GPIO06` according to `CC_IOBUF` is `mdio_o` or `mdio_i`

