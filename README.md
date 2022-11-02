# GateMate_demos
gateware for [CologneChip](https://www.colognechip.com/) [GateMate Evaluation Board](https://www.colognechip.com/programmable-logic/gatemate-evaluation-board/)

## Get

This repository uses [fgpalibs](https://github.com/trabucayre/fpgalibs) as
submodule.

To clone this repository:

```
git clone --recursive https://github.com/trabucayre/GateMate_demos
```

Or

```
git clone https://github.com/trabucayre/GateMate_demos
git submodule init
git submodule update
```

## Toolchain

These demos requires to use CologneChip toolchain:

download
[toolchain](https://www.colognechip.com/programmable-logic/gatemate/gatemate-download/)

And extract archive content somewhere

now `CC_TOOL` env variable must be set:

```
export CC_TOOL=/somewhere/cc-toolchain-linux
```

