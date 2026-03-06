#!/usr/bin/env bash
# install_zybo_z7_20_xilinxboardstore.sh
#
# Installs Zybo Z7-20 board (version 1.0) for Vivado 2020.1
# from the official XilinxBoardStore repository (branch 2020.1).
# Local-user only, no root access required.

set -euo pipefail

# Configuration
REPO_URL="https://github.com/Xilinx/XilinxBoardStore.git"
BRANCH="2020.1"
CLONE_TEMP="$HOME/.Xilinx/tmp-xilinx-boardstore"
BOARD_SRC="boards/Digilent/zybo-z7-20/A.0"
FINAL_REPO="$HOME/.Xilinx/board_repos/xilinx-zybo"
DEST_PATH="$FINAL_REPO/boards/Digilent/zybo-z7-20/A.0"
INIT_DIR="$HOME/.Xilinx/Vivado"
INIT_FILE="$INIT_DIR/Vivado_init.tcl"

echo "Cloning XilinxBoardStore (branch: $BRANCH)..."
rm -rf "$CLONE_TEMP"
git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$CLONE_TEMP"

# Check that board.xml exists
if [ ! -f "$CLONE_TEMP/$BOARD_SRC/board.xml" ]; then
  echo "Error: board.xml not found at $BOARD_SRC"
  exit 1
fi

echo "Installing Zybo Z7-20 board files to $DEST_PATH..."
mkdir -p "$DEST_PATH"
cp "$CLONE_TEMP/$BOARD_SRC/"* "$DEST_PATH/"

# Clean up
rm -rf "$CLONE_TEMP"

# Ensure Vivado init file includes the board path
mkdir -p "$INIT_DIR"
if ! grep -Fq "$FINAL_REPO/boards" "$INIT_FILE" 2>/dev/null; then
  echo "set_param board.repoPaths [list \"$FINAL_REPO/boards\"]" >> "$INIT_FILE"
fi

# Done
echo "Zybo Z7-20 board (version 1.0) installed from XilinxBoardStore branch $BRANCH."
echo "Board path: $DEST_PATH"
echo
echo "To verify in Vivado 2020.1 Tcl console:"
echo "  get_board_parts -filter {NAME == \"digilentinc.com:zybo-z7-20:1.0\"}"
