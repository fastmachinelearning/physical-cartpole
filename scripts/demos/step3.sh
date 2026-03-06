#!/bin/bash

# Default values
EXPERIMENT_NAME="Experiment-1"
DEFAULT_MODEL_NAME="Dense-7IN-32H1-32H2-1OUT-0"
CONFIG_FILE="Driver/CartPoleSimulation/Control_Toolkit_ASF/config_controllers.yml"

# Check if a model name is provided as an argument
if [ -z "$1" ]; then
    MODEL_NAME="$DEFAULT_MODEL_NAME"
else
    MODEL_NAME="$1"
fi

# Determine the operating system
OS=$(uname)

# Define sed command based on OS
if [ "$OS" = "Darwin" ]; then
    # macOS (BSD sed)
    # If you are running commands manually, run these ones if using MacOS

    # Update PATH_TO_MODELS
    sed -i '' -e "s|PATH_TO_MODELS: .*$|PATH_TO_MODELS: ./SI_Toolkit_ASF/Experiments/$EXPERIMENT_NAME/Models/|" "$CONFIG_FILE"

    # Update net_name
    sed -i '' -e "s|net_name: .*$|net_name: '$MODEL_NAME'|" "$CONFIG_FILE"

    # Update input_precision
    sed -i '' -e "s|input_precision: .*$|input_precision: 'float'|" "$CONFIG_FILE"

    # Update hls4ml
    sed -i '' -e "s|hls4ml: .*$|hls4ml: False|" "$CONFIG_FILE"

else
    # Linux (GNU sed)
    # If you are running commands manually, run these ones if using Linux

    # Update PATH_TO_MODELS
    sed -i -e "s|PATH_TO_MODELS: .*$|PATH_TO_MODELS: ./SI_Toolkit_ASF/Experiments/$EXPERIMENT_NAME/Models/|" "$CONFIG_FILE"

    # Update net_name
    sed -i -e "s|net_name: .*$|net_name: '$MODEL_NAME'|" "$CONFIG_FILE"

    # Update input_precision
    sed -i -e "s|input_precision: .*$|input_precision: 'float'|" "$CONFIG_FILE"

    # Update hls4ml
    sed -i -e "s|hls4ml: .*$|hls4ml: False|" "$CONFIG_FILE"
fi

cd Driver/CartPoleSimulation

python run_cartpole_gui.py
