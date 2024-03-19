`default_nettype none

module colorBarVGAPS2 (
	input  wire       clk_i, 
	input  wire       rstn_i,
	output wire [3:0] o_r,
	output wire [3:0] o_g,
	output wire [3:0] o_b,
	output wire       o_vsync,
	output wire       o_hsync,
	output wire       o_clk,
	output wire       o_rst,
	input wire ps2clk,
	input wire ps2data,
	output wire o_led
);

wire clk_pix, lock;


/* PLL for 125MHz (1/2 hdmi clk rate) */
pll pll_inst (
    .clock_in(clk_i), // 10 MHz
	.rst_in(~rstn_i),
    .clock_out(clk_pix), // 40 MHz, 0 deg
    .locked(lock)
);

assign o_clk = 1'b0;//clk_pix;
assign o_rst = 1'b0;//lock;

wire [7:0] ps2_code;

ps2kbd kbd(clk_pix, ps2clk, ps2data, ps2_code, , );

    parameter C_bits = 8;
    reg [C_bits-1:0] R_display; // something to display
    always @(posedge clk_pix)
    begin
      R_display[7:0] <= ps2_code; //btn[0];
    end

    parameter C_color_bits = 16; 
    wire [9:0] x;
    wire [9:0] y;
    // for reverse screen:
    wire [9:0] rx = 636-x;
    wire [C_color_bits-1:0] color;
    hex_decoder_v
    #(
        .c_data_len(C_bits),
        .c_row_bits(3), // 2**n digits per row (4*2**n bits/row) 3->32, 4->64, 5->128, 6->256 
        .c_grid_6x8(0), // NOTE: TRELLIS needs -abc9 option to compile
        .c_font_file("hex/hex_font.mem"),
        .c_x_bits(8),
        .c_y_bits(4),
	.c_color_bits(C_color_bits)
    )
    hex_decoder_v_inst
    (
        .clk(clk_pix),
        .data(R_display),
        .x(rx[9:2]),
        .y(y[5:2]),
        .color(color)
    );

	assign o_led = lock; 

	assign o_r = color[15:12];
	assign o_g = color[10:6];
	assign o_b = color[4:1];

	wire vga_hsync, vga_vsync, vga_blank;

	vga
	vga_instance
	(
	  .clk_pixel(clk_pix),
	  .clk_pixel_ena(1'b1),
	  .test_picture(1'b0), // enable test picture generation
	  .beam_x(x),
	  .beam_y(y),
	  //.vga_r(vga_r),
	  //.vga_g(vga_g),
	  //.vga_b(vga_b),
	  .vga_hsync(o_hsync),
	  .vga_vsync(o_vsync),
	  .vga_blank(vga_blank)
	);

endmodule
