#!/bin/bash

EXPERIMENT_NAME="Experiment-1"

mkdir Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments
cp -r "$EXPERIMENT_NAME" Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/
FILE="Driver/CartPoleSimulation/SI_Toolkit_ASF/config_training.yml"

# Determine the operating system
OS=$(uname)

# Define sed command based on OS
if [ "$OS" = "Darwin" ]; then

    # macOS (BSD sed)
    # If you are running commands manually, run these ones if using MacOS

    # Use sed to update path_to_experiment
    sed -i "" "s|path_to_experiment:.*|path_to_experiment: '$EXPERIMENT_NAME'|" "$FILE"
    # Use sed to update PATH_TO_EXPERIMENT_FOLDERS
    sed -i "" "s|PATH_TO_EXPERIMENT_FOLDERS:.*|PATH_TO_EXPERIMENT_FOLDERS: './SI_Toolkit_ASF/Experiments/'|" "$FILE"

else
    # Linux (GNU sed)
    # If you are running commands manually, run these ones if using Linux

    # Use sed to update path_to_experiment
    sed -i "s|path_to_experiment:.*|path_to_experiment: '$EXPERIMENT_NAME'|" "$FILE"
    # Use sed to update PATH_TO_EXPERIMENT_FOLDERS
    sed -i "s|PATH_TO_EXPERIMENT_FOLDERS:.*|PATH_TO_EXPERIMENT_FOLDERS: './SI_Toolkit_ASF/Experiments/'|" "$FILE"
fi

cd Driver/CartPoleSimulation

python SI_Toolkit_ASF/Run/A1_Create_Normalization_File.py

python SI_Toolkit_ASF/Run/A2_Train_Network.py
