#!/usr/bin/env python3

import sys
import time
import argparse

from litex import RemoteClient

#--------------------------------------------------------------------------------
# MDIO Constants
#--------------------------------------------------------------------------------

MDIO_CLK  = 0x01
MDIO_OE   = 0x02
MDIO_DO   = 0x04

MDIO_DI   = 0x01

MDIO_PREAMBLE    = 0xffffffff
MDIO_START       = 0x1
MDIO_READ        = 0x2
MDIO_WRITE       = 0x1
MDIO_TURN_AROUND = 0x2

#--------------------------------------------------------------------------------
# MDIO Class
#--------------------------------------------------------------------------------

class MDIO:
    """MDIO bit-banged driver, using bus.regs accessor style."""

    def __init__(self, bus, reg_name="eth_mdio"):
        """
        :param bus: RemoteClient bus.
        :param reg_name: Register prefix to use (e.g. "eth_mdio" or "ethphy_mdio").
        """
        self.bus = bus
        self.reg_name = reg_name
        # The actual register names become, for example:
        #   "<reg_name>_w" and "<reg_name>_r"
        self._mdio_w = self._reg(f"{self.reg_name}_w")
        self._mdio_r = self._reg(f"{self.reg_name}_r")

    def _reg(self, name):
        """Return a register object from bus.regs by name."""
        return getattr(self.bus.regs, name)

    def _mdio_w_write(self, val):
        """Write a value to the MDIO output register."""
        self._mdio_w.write(val)

    def _mdio_r_read(self):
        """Read (and return) a value from the MDIO input register."""
        return self._mdio_r.read()

    def _delay(self):
        # Optionally add a real delay here if needed for timing.
        pass

    def _raw_write(self, word, bitcount):
        """Bit-bang writing of 'bitcount' bits of 'word' on MDIO."""
        word <<= (32 - bitcount)
        while bitcount > 0:
            if (word & 0x80000000):
                # Drive MDIO_DO
                print("here+")
                self._mdio_w_write(MDIO_DO | MDIO_OE)
                self._delay()
                self._mdio_w_write(MDIO_CLK | MDIO_DO | MDIO_OE)
                self._delay()
                self._mdio_w_write(MDIO_DO | MDIO_OE)
            else:
                print("here-")
                # Drive MDIO_OE (no DO)
                self._mdio_w_write(MDIO_OE)
                self._delay()
                self._mdio_w_write(MDIO_CLK | MDIO_OE)
                self._delay()
                self._mdio_w_write(MDIO_OE)
            word <<= 1
            bitcount -= 1

    def _raw_read(self):
        """Bit-bang reading of 16 bits from MDIO."""
        word = 0
        for _ in range(16):
            word <<= 1
            if self._mdio_r_read() & MDIO_DI:
                word |= 1
            # Clock high
            self._mdio_w_write(MDIO_CLK)
            self._delay()
            # Clock low
            self._mdio_w_write(0)
            self._delay()
        return word

    def _raw_turnaround(self):
        """Toggle clock and data lines per MDIO protocol turnaround."""
        self._delay()
        self._mdio_w_write(MDIO_CLK)
        self._delay()
        self._mdio_w_write(0)
        self._delay()
        self._mdio_w_write(MDIO_CLK)
        self._delay()
        self._mdio_w_write(0)

    def write(self, phyadr, reg, val):
        """Perform an MDIO write (PHY address, register, 16-bit value)."""
        # Put MDIO line in output mode
        self._mdio_w_write(MDIO_OE)
        # Write Preamble, Start, Opcode, PhyAdr, Reg, Turn-around, Val
        self._raw_write(MDIO_PREAMBLE, 32)
        self._raw_write(MDIO_START, 2)
        self._raw_write(MDIO_WRITE, 2)
        self._raw_write(phyadr, 5)
        self._raw_write(reg, 5)
        self._raw_write(MDIO_TURN_AROUND, 2)
        self._raw_write(val, 16)
        self._raw_turnaround()

    def read(self, phyadr, reg):
        """Perform an MDIO read (PHY address, register) -> 16-bit value."""
        self._mdio_w_write(MDIO_OE)
        self._raw_write(MDIO_PREAMBLE, 32)
        self._raw_write(MDIO_START, 2)
        self._raw_write(MDIO_READ, 2)
        self._raw_write(phyadr, 5)
        self._raw_write(reg, 5)
        self._raw_turnaround()
        val = self._raw_read()
        self._raw_turnaround()
        return val

    def dump(self, phyadr, count):
        """Read a sequence of 'count' registers from a given PHY address."""
        result = []
        for r in range(count):
            val = self.read(phyadr, r)
            result.append((r, val))
        return result

#--------------------------------------------------------------------------------
# Main
#--------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MDIO control via Etherbone.")
    parser.add_argument("--name", default="eth_mdio", choices=["eth_mdio", "ethphy_mdio"], help="Name of the MDIO registers to use (default: eth_mdio)")
    subparsers = parser.add_subparsers(dest="command")

    # write
    write_parser = subparsers.add_parser("write", help="Write MDIO register")
    write_parser.add_argument("phyadr", type=int, help="PHY address")
    write_parser.add_argument("reg",    type=int, help="Register offset")
    write_parser.add_argument("val",    type=int, help="Value to write")

    # read
    read_parser = subparsers.add_parser("read", help="Read MDIO register")
    read_parser.add_argument("phyadr", type=int, help="PHY address")
    read_parser.add_argument("reg",    type=int, help="Register offset")

    # dump
    dump_parser = subparsers.add_parser("dump", help="Dump MDIO registers")
    dump_parser.add_argument("phyadr", type=int, help="PHY address")
    dump_parser.add_argument("count",  type=int, help="Number of registers to dump")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Connect to Etherbone
    bus = RemoteClient()
    bus.open()

    # Create MDIO instance, using the --name argument
    mdio = MDIO(bus, reg_name=args.name)

    if args.command == "write":
        print(f"MDIO write @0x{args.phyadr:x}, reg=0x{args.reg:02x}, val=0x{args.val:04x}")
        mdio.write(args.phyadr, args.reg, args.val)

    elif args.command == "read":
        val = mdio.read(args.phyadr, args.reg)
        print(f"MDIO read @0x{args.phyadr:x}, reg=0x{args.reg:02x} -> 0x{val:04x}")

    elif args.command == "dump":
        print(f"MDIO dump @0x{args.phyadr:x}, count={args.count}")
        regs = mdio.dump(args.phyadr, args.count)
        for reg_num, val in regs:
            print(f"  reg 0x{reg_num:02x} -> 0x{val:04x}")

    bus.close()

if __name__ == "__main__":
    main()
