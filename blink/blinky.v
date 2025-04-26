/*
 * blinky.v
 *
 * Copyright (C) 2025  Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
 * SPDX-License-Identifier: MIT
 */

module blinky #(
	parameter CLK_FREQ_HZ = 10000000
) (
	input                clk,
	output [`N_LEDS-1: 0] leds
);

reg [`N_LEDS-1:0] q;
assign leds = ~q;

reg [$clog2(CLK_FREQ_HZ)-1:0] count = 0;

always @(posedge clk) begin
	count <= count + 1;
	if (count == CLK_FREQ_HZ/4-1) begin
		q <= q + 1'b1;
		count <= 0;
	end
end
endmodule
