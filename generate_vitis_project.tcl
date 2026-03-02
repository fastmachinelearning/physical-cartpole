# ===== Vitis 2020.1 Automation for CartPoleFirmware =====

# --- Paths ---
set ws_path "$::env(HOME)/physical-cartpole/Firmware/VitisProjects"
set hw_xsa  "$::env(HOME)/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq/cartpole_driver_design_wrapper.xsa"
set proc_name "ps7_cortexa9_0"
set app_name  "CartPoleFirmware"
set hw_name   "cartpole_hw"
set bsp_name  "cartpole_bsp"
set symlink_script "$::env(HOME)/physical-cartpole/Firmware/create_symlinks_cartpole.sh"

# --- Workspace ---
if {[file exists $ws_path]} {
    # Make reruns idempotent: stale projects in this workspace cause createapp to fail.
    puts "Removing existing Vitis workspace: $ws_path"
    file delete -force $ws_path
}
file mkdir $ws_path
setws $ws_path

# --- Create HW platform & BSP ---
createhw  -name $hw_name  -hwspec $hw_xsa
createbsp -name $bsp_name -hwproject $hw_name -proc $proc_name -os standalone

# --- Create application ---
createapp -name $app_name -hwproject $hw_name -bsp $bsp_name -proc $proc_name -os standalone -lang C -app "Empty Application"

# --- Clean default sources from the template ---
set src_dir "$ws_path/$app_name/src"
if {[file exists $src_dir]} {
    foreach file [glob -nocomplain -directory $src_dir *.{c,h}] {
        file delete -force $file
    }
    puts "Deleted existing .c and .h files from $src_dir"
}

# --- Link to sources (symlinks) ---
if {[file exists $symlink_script]} {
    puts "Running create_symlinks_cartpole.sh ..."
    catch {exec bash -c "cd $::env(HOME)/physical-cartpole/Firmware && chmod +x ./create_symlinks_cartpole.sh && ./create_symlinks_cartpole.sh"} res
    puts $res
} else {
    puts "Symlink script not found at $symlink_script — skipping."
}

# ==================== MATH LIBRARY IMPORT ====================

# Remove any previous settings that might confuse ordering
catch { app config -name $app_name -remove linker-misc {-lm} }
catch { app config -name $app_name -remove libraries m }

# Correct placement: Libraries list
app config -name $app_name -add libraries m

# make sure C99/gnu99 is used for math builtins/macros
catch { app config -name $app_name -add compiler-misc {-std=gnu99} }

# Persist
catch { app write -name $app_name }

# ==================== BUILD ====================
# Clean & build (use both app/projects to be robust across 2020.1 variants)
catch { app clean -name $app_name }
if {[catch { app build -name $app_name } err]} {
    puts "app build failed ($err) — trying projects -clean/-build..."
    catch { projects -clean $app_name }
    projects -build $app_name
}

puts "\n=== Vitis automation completed (with libm correctly linked) ===\n"

# === FSBL + BOOT.BIN ===
# The path forthe .bit file might be misinterpreted, in hta case just run the command bootgen manually by copy pasting the directory
# into the .bif file. There might be hidden chars, so copy from the terminal output.
set fsbl_name "cartpole_fsbl"
# --- Workspace-derived paths (unchanged) ---
set app_elf   "$ws_path/$app_name/Debug/$app_name.elf"
set fsbl_elf  "$ws_path/$fsbl_name/Debug/$fsbl_name.elf"
set bif_file  "$ws_path/boot.bif"
set boot_bin  "$ws_path/BOOT.bin"

# --- Build the BIT path robustly ---
# Avoid string concatenation; join path segments so spaces/slashes are handled correctly.
set raw_bit_path [file join $::env(HOME) \
    physical-cartpole FPGA VivadoProjects CartpoleDriverZynq \
    CartpoleDriverZynq.runs impl_1 cartpole_driver_design_wrapper.bit]

# --- Path sanitizer ---
proc sanitize_path {p} {
    # Trim spaces and remove CR/LF/TAB that often sneak in from env/files
    set q [string trim $p]
    set q [string map {\r "" \n "" \t ""} $q]
    return $q
}

# Sanitize and normalize all paths
set fsbl_elf [file normalize [sanitize_path $fsbl_elf]]
set app_elf  [file normalize [sanitize_path $app_elf]]
set bit_file [file normalize [sanitize_path $raw_bit_path]]

# Fail early with a clear message if the app did not produce an ELF.
if {![file exists $app_elf]} {
    error "Missing application ELF: $app_elf. CartPoleFirmware build failed earlier; inspect vitis_output.log for compiler errors."
}

# --- Make BSP FSBL-ready (xilffs) ---
# Set the target BSP (most workspaces only have one; the -name is harmless if unsupported)
catch { bsp setlib -name xilffs }          ;# Enable FAT FS support needed by FSBL
catch { bsp write -name $bsp_name }        ;# Persist BSP settings
# Regenerate BSP so the new lib is compiled into it (try both spellings across 2020.1 variants)
if {[catch { bsp regenerate -name $bsp_name }]} {
    catch { bsp generate -name $bsp_name }
}


# Create & build FSBL
createapp -name $fsbl_name -hwproject $hw_name -bsp $bsp_name -proc $proc_name -os standalone -lang C -app "Zynq FSBL"
app build -name $fsbl_name

# --- Write BIF with safe quoting ---
set fp [open $bif_file "w"]
puts $fp "the_ROM_image:{"
puts $fp "  \[bootloader\] \"$fsbl_elf\""
puts $fp "  \"$bit_file\""
puts $fp "  \"$app_elf\""
puts $fp "}"
close $fp

# --- Generate BOOT.bin ---
exec bootgen -image $bif_file -arch zynq -o i $boot_bin -w
puts "BOOT image generated: $boot_bin"
