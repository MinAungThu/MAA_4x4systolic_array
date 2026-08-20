
module pe_ws #(
    parameter integer DATA_W = 8,
    parameter integer ACC_W  = 32
)(
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire                       load_w,
    input  wire signed [DATA_W-1:0]   w_in,
    input  wire signed [DATA_W-1:0]   a_in,
    input  wire signed [ACC_W-1:0]    psum_in,
    output reg  signed [DATA_W-1:0]   a_out,
    output reg  signed [ACC_W-1:0]    psum_out
);
    reg  signed [DATA_W-1:0]   w_reg;
    wire signed [2*DATA_W-1:0] prod = w_reg * a_in;   

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            w_reg    <= {DATA_W{1'b0}};
            a_out    <= {DATA_W{1'b0}};
            psum_out <= {ACC_W{1'b0}};
        end else begin
            if (load_w) w_reg <= w_in;
            a_out    <= a_in;
            psum_out <= psum_in + {{(ACC_W-2*DATA_W){prod[2*DATA_W-1]}}, prod};
        end
    end
endmodule
