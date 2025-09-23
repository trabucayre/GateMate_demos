# GateMate_demos

Gateware examples for the [CologneChip GateMate Evaluation Board](https://www.colognechip.com/programmable-logic/gatemate-evaluation-board/).

## Get the Source

This repository uses [fpgalibs](https://github.com/trabucayre/fpgalibs) as a submodule.

Clone with submodules in one step:

```bash
git clone --recursive https://github.com/trabucayre/GateMate_demos
```

Or clone and initialize submodules separately:

```bash
git clone https://github.com/trabucayre/GateMate_demos
cd GateMate_demos
git submodule init
git submodule update
```

## Toolchains

These demos can be built using either:

- The **CologneChip Legacy toolchain**
- The **nextpnr + prjpeppercorn open-source flow**

### CologneChip Toolchain

1. [Download the toolchain](https://colognechip.com/programmable-logic/gatemate/toolchain/).
2. Extract the archive to a chosen location.
3. Set the `CC_TOOL` environment variable:

```bash
export CC_TOOL=/path/to/cc-toolchain-linux
```

### NextPNR + Prjpeppercorn Toolchain

The easiest method is to use the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build/releases).

1. Download and extract the latest release.
2. Source the environment to add tools to your `\$PATH`:

```bash
source /path/to/oss-cad-suite/environment
```

#### Alternate Method (TBD)

You can also build **yosys**, **prjpeppercorn**, and **nextpnr** from source (instructions coming soon).
