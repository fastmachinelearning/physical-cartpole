# Load user-defined board repo path from vivado_init.tcl if configured
if {[file exists "$::env(HOME)/.Xilinx/Vivado/Vivado_init.tcl"]} {
  source "$::env(HOME)/.Xilinx/Vivado/Vivado_init.tcl"
}


# Source the project setup script (creates block design, constraints, etc.)
source ~/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq_new.tcl

# Launch synthesis, implementation, and generate bitstream
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

# Export hardware platform including bitstream (.xsa file)
write_hw_platform -fixed -include_bit \
  -file ~/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq/cartpole_driver_design_wrapper.xsa
