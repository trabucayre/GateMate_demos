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
2. Source the environment to add tools to your `$PATH`:

```bash
source /path/to/oss-cad-suite/environment
```

#### Alternate Method: toolchain-sources-build.sh

You can also build [**yosys**](https://github.com/YosysHQ/yosys),
[**prjpeppercorn**](https://github.com/YosysHQ/prjpeppercorn) and [**nextpnr**](https://github.com/YosysHQ/nextpnr) from source.

This bash script provides an alternative to using *oss-cad-suite* for setting
up the toolchain. It automates the process of downloading, building, and
installing FPGA toolchain components manually.

**Objectives**

The script handles the following tasks:

- checking and installing build dependencies
- cloning, updating and checking out latest [gatemate-timings-latest](https://colognechip.com/downloads/gatemate-timings-latest.tar.gz)
- building each specified tools
- installing the resulting binaries into the */opt/gatemate* directory (default target path).

**Usage**

The script can be exceuted with or without arguments:

- with no arguments or `all`: downloads, builds and installs all supported tools
- with specific tool names (`yosys` and/or `nextpnr` and/or `prjpeppercorn`) only the specified tools will be downloaded, built, and installed.
- with `INSTALL_PREFIX=CUSTOM_DIRECTORY` before the script (or exported): all tools will be installed in the specified directory instead
  of */opt/gatemate*

```bash
[INSTALL_PREFIX=/somewhere] ./toolchain-sources-builder.sh [opts]
```

with:
- `INSTALL_PREFIX` (optional): the install directory (*/opt/gatemate* when not specified)
- `opts` (optional): may be `all` or any combinaisons of `nextpnr`, `yosys` and `prjpeppercorn` (`all` when not specified)

**Environment setup**

After installation, the script generate a file at *opt/gatemate/export.sh*,
which can be sourced in your terminal to update the environment variables
accordingly:

```bash
source /opt/gatemate/export.sh
```

This allows you to use the installed tools in your current shell session without manually modifying/adding:
- `PATH`
