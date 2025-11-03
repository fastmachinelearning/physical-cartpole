#!/usr/bin/env bash
# run_vitis_cartpole.sh
# Launches Vitis 2020.1 headlessly on Ubuntu 20.04 to run your existing TCL.
# - Forces a clean Xvfb display
# - Pins Java 8 (preferred for Vitis 2020.1 Eclipse/SWT)
# - Uses GTK2 for SWT (avoids headless GTK3 crashes)
# - Shows helpful logs on failure (including Eclipse .metadata/.log)

set -euo pipefail

### --- USER SETTINGS (edit if your install paths differ) ---
VITIS_ROOT="${VITIS_ROOT:-/mnt/xilinx/Xilinx/Vitis/2020.1}"    # Path to your Vitis 2020.1
TCL="${TCL:-generate_vitis_project.tcl}"                        # Your TCL file (unchanged)
LOG="${LOG:-vitis_output.log}"                                  # Where to write xsct output
DISPLAY_NUM="${DISPLAY_NUM:-99}"                                # Xvfb display number

# Workspace path used inside your TCL (for surfacing Eclipse logs on failure)
WS_DIR="${WS_DIR:-$HOME/physical-cartpole/Firmware/VitisProjects}"

# Set to 1 if you want this script to try installing dependencies via apt
RUN_DEPS="${RUN_DEPS:-0}"

### --- FUNCTIONS ---
install_deps() {
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "[WARN] apt-get not available; skipping dependency install." >&2
    return 0
  fi

  # universe is where some GTK2/compat libs live on Ubuntu 20.04
  sudo add-apt-repository -y universe || true
  sudo apt-get update

  # Core X/GTK/SWT bits for headless Eclipse on 20.04
  DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
    xvfb xauth x11-xkb-utils x11-utils \
    libgtk2.0-0 libcanberra-gtk-module \
    libxrender1 libxtst6 libxi6 libxt6 libxext6 libxrandr2 libxdamage1 libxft2 \
    libxinerama1 libxkbfile1 \
    libnss3 libasound2 fontconfig \
    libncurses5 libtinfo5 libjpeg-turbo8 ca-certificates procps || {
      echo "[WARN] Some packages failed to install; continuing." >&2
    }

  # Prefer Java 8 for Vitis 2020.1
  sudo apt-get install -y openjdk-8-jre || {
    echo "[WARN] Could not install openjdk-8-jre; continuing." >&2
  }
}

start_xvfb() {
  local disp=":$DISPLAY_NUM"
  export DISPLAY="$disp"

  # Kill any stale Xvfb on that display
  if pgrep -f "Xvfb $disp" >/dev/null 2>&1; then
    pkill -f "Xvfb $disp" || true
    sleep 1
  fi

  # Start a clean Xvfb
  Xvfb "$disp" -screen 0 1920x1080x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 &
  XVFB_PID=$!
  sleep 2

  # Basic sanity check if xdpyinfo exists
  if command -v xdpyinfo >/dev/null 2>&1; then
    xdpyinfo >/dev/null 2>&1 || {
      echo "[ERROR] Xvfb did not start correctly on $DISPLAY" >&2
      kill "$XVFB_PID" >/dev/null 2>&1 || true
      exit 2
    }
  fi
}

cleanup_xvfb() {
  if [[ -n "${XVFB_PID:-}" ]]; then
    kill "$XVFB_PID" >/dev/null 2>&1 || true
    wait "$XVFB_PID" 2>/dev/null || true
  fi
}

### --- OPTIONAL: install dependencies ---
if [[ "$RUN_DEPS" == "1" ]]; then
  install_deps
fi

### --- SANITY CHECKS ---
# TCL presence
if [[ ! -f "$TCL" ]]; then
  echo "[ERROR] Can't find $TCL in $(pwd)" >&2
  exit 2
fi

# Vitis environment
if [[ ! -f "$VITIS_ROOT/settings64.sh" ]]; then
  echo "[ERROR] $VITIS_ROOT/settings64.sh not found. Set VITIS_ROOT or fix path." >&2
  exit 2
fi

# HOME must be writable (Eclipse writes .metadata here and under the workspace)
if [[ ! -w "$HOME" ]]; then
  echo "[ERROR] HOME ($HOME) is not writable; Vitis workspace will fail." >&2
  exit 2
fi

### --- JAVA SETUP (prefer Java 8) ---
# If Java 8 exists, force it; else, fall back to whatever 'java' is available.
if [[ -d "/usr/lib/jvm/java-8-openjdk-amd64" ]]; then
  export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"
  export PATH="$JAVA_HOME/bin:$PATH"
fi
# Avoid stray Java flags that can break SWT
unset JAVA_TOOL_OPTIONS JDK_HOME

### --- LOCALE & SWT/GTK HINTS ---
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export SWT_GTK3=0               # force GTK2 for old SWT on Ubuntu 20.04
export GDK_BACKEND=x11
export LIBGL_ALWAYS_INDIRECT=1  # safer on headless GL stacks

### --- SOURCE VITIS ENV (xsct, bootgen, etc.) ---
# shellcheck source=/dev/null
source "$VITIS_ROOT/settings64.sh"

### --- DEBUG PRINTS ---
echo "== Java in PATH =="
( which java && java -version ) || true
echo "== XSCT version =="
xsct -eval 'puts [version]' || true
echo "== DISPLAY =="
echo "$DISPLAY"

### --- START XVFB ---
trap cleanup_xvfb EXIT
start_xvfb

### --- RUN THE TCL (unchanged) ---
set +e
xsct -quiet -eval "source $TCL" > "$LOG" 2>&1
RET=$?
set -e

### --- ON FAILURE: surface useful logs ---
if [[ $RET -ne 0 ]]; then
  echo
  echo "==== xsct exited with code $RET ===="
  echo "Last 80 lines of $LOG:"
  tail -n 80 "$LOG" || true

  META_LOG="$WS_DIR/.metadata/.log"
  if [[ -f "$META_LOG" ]]; then
    echo
    echo "==== Eclipse workspace log (.metadata/.log) tail ===="
    tail -n 120 "$META_LOG" || true
  else
    echo
    echo "[INFO] No Eclipse workspace log found at: $META_LOG"
  fi

  echo
  echo "Common fixes:"
  echo " - Ensure your XSA exists inside the container:"
  echo "   $HOME/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq/cartpole_driver_design_wrapper.xsa"
  echo " - Ensure the workspace path is writable:"
  echo "   $WS_DIR"
  echo " - Keep SWT_GTK3=0 and prefer Java 8 for Vitis 2020.1."
  echo " - Set XILINXD_LICENSE_FILE if licensing dialogs might appear (headless = crash)."
  exit $RET
fi

echo "Success. Full log: $LOG"
