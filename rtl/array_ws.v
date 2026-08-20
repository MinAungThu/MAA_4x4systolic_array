
module array_ws #(
    parameter integer R      = 4,
    parameter integer C      = 4,
    parameter integer DATA_W = 8,
    parameter integer ACC_W  = 32
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         load_w,
    input  wire [R*C*DATA_W-1:0]        w_bus,
    input  wire [R*DATA_W-1:0]          west_bus,
    output wire [C*ACC_W-1:0]           south_bus
);
   
    wire signed [DATA_W-1:0] a_w  [0:R-1][0:C];
    wire signed [ACC_W-1:0]  ps_w [0:R][0:C-1];

    genvar r, c;
    generate
        
        for (r = 0; r < R; r = r + 1) begin : WEST
            assign a_w[r][0] = $signed(west_bus[r*DATA_W +: DATA_W]);
        end
        
        for (c = 0; c < C; c = c + 1) begin : NORTH
            assign ps_w[0][c] = {ACC_W{1'b0}};
        end
        // PE grid
        for (r = 0; r < R; r = r + 1) begin : ROW
            for (c = 0; c < C; c = c + 1) begin : COL
                wire signed [DATA_W-1:0] w_pe =
                    $signed(w_bus[(r*C + c)*DATA_W +: DATA_W]);
                pe_ws #(.DATA_W(DATA_W), .ACC_W(ACC_W)) u_pe (
                    .clk(clk), .rst_n(rst_n), .load_w(load_w),
                    .w_in(w_pe),
                    .a_in(a_w[r][c]),     .psum_in(ps_w[r][c]),
                    .a_out(a_w[r][c+1]),  .psum_out(ps_w[r+1][c])
                );
            end
        end
    
        for (c = 0; c < C; c = c + 1) begin : SOUTH
            assign south_bus[c*ACC_W +: ACC_W] = ps_w[R][c];
        end
    endgenerate
endmodule
