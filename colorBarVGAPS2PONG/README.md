# colorBarVGA

Simple VGA (640x480@60Hz) demonstration using a [Digilent PMOD
VGA](https://digilent.com/reference/pmod/pmodvga/start) to displays 8 colors
bars


To use the design with PMOD-VGA from [Muse
lab](https://www.tindie.com/products/johnnywu/pmod-vga-expansion-board/), add
`VGA=muselab` option to make (colors could be wrong, but syncro will be ok) :

```
$ make VGA=muselab
```

And with [Olimex GateMateA1 EVB](https://www.olimex.com/Products/FPGA/GateMate/GateMateA1-EVB/open-source-hardware),
add `VGA=olimex`

```
$ make VGA=olimex
```


Note: (*digilent* and *muselab*) due to PMOD level shifters **JP14** must be mounted between 2-3 (2v5)

- With Digilent adapt :

![ColorBarDemo](gatemateVGA.jpg)

- With Muse Lab adapt :

![ColorBarDemo](gatemateVGA_muselab.jpg)

- With Olimex GateMateA1 EVB:

![ColorBarDemo](gatemateVGA_olimex.jpg)
