# colorBarDVI

A simple DVI demo (640x480@60Hz) that displays 8 shaded color bars using either:
- [Machdyne DDMI Pmod](https://machdyne.com/product/ddmi-pmod/)
- [Sipeed PMOD_DVI](https://wiki.sipeed.com/hardware/en/tang/tang-PMOD/FPGA_PMOD.html#PMOD_DVI)

## Build

```bash
make [DVI=xxx] [TOOLCHAIN=yyy]
```

### Parameters

- **TOOLCHAIN**
  - `colognechip`: CologneChip legacy toolchain
  - `nextpnr`: nextpnr + prjpeppercorn toolchain (default)

- **DVI (Pmod model)**
  - `machdyne`: [Machdyne DDMI Pmod](https://machdyne.com/product/ddmi-pmod/) (default)
  - `sipeed_pmod`: [Sipeed PMOD_DVI](https://wiki.sipeed.com/hardware/en/tang/tang-PMOD/FPGA_PMOD.html#PMOD_DVI)

## Notes

- Due to PMOD level shifters, jumper **JP14** must be mounted between **pins 2-3 (2V5)**.

## Preview

![ColorBarDemo](gatemateDVI.jpg)