
module mac_top #(
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
    output reg  [C*ACC_W-1:0]           south_bus
);
    // Input registers
    reg                          load_w_q;
    reg [R*C*DATA_W-1:0]         w_bus_q;
    reg [R*DATA_W-1:0]          west_bus_q;
    wire [C*ACC_W-1:0]          south_w;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            load_w_q   <= 1'b0;
            w_bus_q    <= {R*C*DATA_W{1'b0}};
            west_bus_q <= {R*DATA_W{1'b0}};
            south_bus  <= {C*ACC_W{1'b0}};
        end else begin
            load_w_q   <= load_w;
            w_bus_q    <= w_bus;
            west_bus_q <= west_bus;
            south_bus  <= south_w;     // output register
        end
    end

    array_ws #(.R(R), .C(C), .DATA_W(DATA_W), .ACC_W(ACC_W)) u_array (
        .clk(clk), .rst_n(rst_n), .load_w(load_w_q),
        .w_bus(w_bus_q), .west_bus(west_bus_q), .south_bus(south_w)
    );
endmodule
