module red_pitaya_infrastructure #(
        parameter MULTIPLY = 1,
        parameter DIVIDE   = 1,
        parameter DIVCLK   = 1
    ) (
        //input  sys_clk_buf_n,
        //input  sys_clk_buf_p,

        input adc_clk_in,

        output user_clk,
        output user_rst,

        output adc_clk_125,
        output adc_rst,
        output dac_clk_250,
        output dac_rst,
        output dac_clk_250_315
    );

    wire clk_fb;
    wire adc_clk_ibuf;
    wire user_clk_mmcm;
    wire adc_clk_mmcm;
    wire dac_clk_mmcm;
    wire dac_clk_250_315_mmcm;
    wire user_mmcm_lock;
    wire adc_mmcm_lock;
    
    // single clock input
    IBUF adc_clk_ibuf_inst (.I (adc_clk_in), .O (adc_clk_ibuf));  // differential clock input
    
    // diferential clock input
    // IBUFDS i_clk (.I (adc_clk_i[1]), .IB (adc_clk_i[0]), .O (adc_clk_ibufds));  // differential clock input
    
    MMCM_BASE #(
        .BANDWIDTH          ("OPTIMIZED"), // Jitter programming ("HIGH","LOW","OPTIMIZED")
        .CLKFBOUT_MULT_F    (MULTIPLY), // Multiply value for all CLKOUT (5.0-64.0).
        .CLKFBOUT_PHASE     (0.0),
        .CLKIN1_PERIOD      (8.0), // Red Pitaya clock is 125 MHz
        .CLKOUT0_DIVIDE_F   (DIVIDE),   // Divide amount for CLKOUT0 (1.000-128.000).
        .CLKOUT0_DUTY_CYCLE (0.5),
        .CLKOUT1_DUTY_CYCLE (0.5),
        .CLKOUT2_DUTY_CYCLE (0.5),
        .CLKOUT3_DUTY_CYCLE (0.5),
        .CLKOUT4_DUTY_CYCLE (0.5),
        .CLKOUT5_DUTY_CYCLE (0.5),
        .CLKOUT6_DUTY_CYCLE (0.5),
        .CLKOUT0_PHASE      (0.0),
        .CLKOUT1_PHASE      (0.0),
        .CLKOUT2_PHASE      (0.0),
        .CLKOUT3_PHASE      (0.0),
        .CLKOUT4_PHASE      (0.0),
        .CLKOUT5_PHASE      (0.0),
        .CLKOUT6_PHASE      (0.0),
        .CLKOUT1_DIVIDE     (12),
        .CLKOUT2_DIVIDE     (6),
        .CLKOUT3_DIVIDE     (6),
        .CLKOUT4_DIVIDE     (1),
        .CLKOUT5_DIVIDE     (1),
        .CLKOUT6_DIVIDE     (1),
        .CLKOUT4_CASCADE    ("FALSE"),
        .CLOCK_HOLD         ("FALSE"),
        .DIVCLK_DIVIDE      (DIVCLK), // Master division value (1-80)
        .REF_JITTER1        (0.0),
        .STARTUP_WAIT       ("FALSE")
    ) user_clk_mmcm_inst (
        .CLKIN1   (adc_clk_ibuf),
        .CLKFBIN  (user_clk_mmcm_fb),
        .CLKFBOUT  (user_clk_mmcm_fb),
        .CLKFBOUTB (),
        .CLKOUT0  (user_clk_mmcm),
        .CLKOUT0B (),
        .CLKOUT1  (),
        .CLKOUT1B (),
        .CLKOUT2  (),
        .CLKOUT2B (),
        .CLKOUT3  (),
        .CLKOUT3B (),
        .CLKOUT4  (),
        .CLKOUT5  (),
        .CLKOUT6  (),
        .LOCKED   (user_mmcm_lock),
        .PWRDWN   (1'b0),
        .RST      (1'b0)
    );
    
    MMCM_BASE #(
        .BANDWIDTH          ("OPTIMIZED"), // Jitter programming ("HIGH","LOW","OPTIMIZED")
        .CLKFBOUT_MULT_F    (8), // Multiply value for all CLKOUT (5.0-64.0).
        .CLKFBOUT_PHASE     (0.0),
        .CLKIN1_PERIOD      (8.0), // Red Pitaya clock is 125 MHz
        .CLKOUT0_DIVIDE_F   (1),   // Divide amount for CLKOUT0 (1.000-128.000).
        .CLKOUT0_DUTY_CYCLE (0.5),
        .CLKOUT1_DUTY_CYCLE (0.5),
        .CLKOUT2_DUTY_CYCLE (0.5),
        .CLKOUT3_DUTY_CYCLE (0.5),
        .CLKOUT4_DUTY_CYCLE (0.5),
        .CLKOUT5_DUTY_CYCLE (0.5),
        .CLKOUT6_DUTY_CYCLE (0.5),
        .CLKOUT0_PHASE      (0.0),
        .CLKOUT1_PHASE      (0.0),
        .CLKOUT2_PHASE      (0.0),
        .CLKOUT3_PHASE      (-45.0),
        .CLKOUT4_PHASE      (0.0),
        .CLKOUT5_PHASE      (0.0),
        .CLKOUT6_PHASE      (0.0),
        .CLKOUT1_DIVIDE     (8),
        .CLKOUT2_DIVIDE     (4),
        .CLKOUT3_DIVIDE     (4),
        .CLKOUT4_DIVIDE     (1),
        .CLKOUT5_DIVIDE     (1),
        .CLKOUT6_DIVIDE     (1),
        .CLKOUT4_CASCADE    ("FALSE"),
        .CLOCK_HOLD         ("FALSE"),
        .DIVCLK_DIVIDE      (1), // Master division value (1-80)
        .REF_JITTER1        (0.0),
        .STARTUP_WAIT       ("FALSE")
    ) adc_clk_mmcm_inst (
        .CLKIN1   (adc_clk_ibuf),
        .CLKFBIN  (adc_clk_mmcm_fb),
        .CLKFBOUT  (adc_clk_mmcm_fb),
        .CLKFBOUTB (),
        .CLKOUT0  (),
        .CLKOUT0B (),
        .CLKOUT1  (adc_clk_125_mmcm),
        .CLKOUT1B (),
        .CLKOUT2  (dac_clk_250_mmcm),
        .CLKOUT2B (),
        .CLKOUT3  (dac_clk_250_315_mmcm),
        .CLKOUT3B (),
        .CLKOUT4  (),
        .CLKOUT5  (),
        .CLKOUT6  (),
        .LOCKED   (adc_mmcm_lock),
        .PWRDWN   (1'b0),
        .RST      (1'b0)
    );
    
    BUFG bufg_sysclk[3:0](
      .I({user_clk_mmcm, adc_clk_125_mmcm, dac_clk_250_mmcm, dac_clk_250_315_mmcm}),
      .O({user_clk,      adc_clk_125,      dac_clk_250     , dac_clk_250_315})
    );
    
    // TODO: Check this logic and look a the resets
    assign user_rst = !(adc_mmcm_lock & user_mmcm_lock);
    assign adc_rst  = !(adc_mmcm_lock & user_mmcm_lock);
    assign dac_rst  = !(adc_mmcm_lock & user_mmcm_lock);

endmodule