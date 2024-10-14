# Instructions


## Step 1: Environment Setup

### Clone the Github repository
To clone the repository along with its submodules, use the SSH URL:

```bash
git clone --recurse-submodules git@github.com:fastmachinelearning/physical-cartpole.git && cd physical-cartpole
```

**Note**: Using SSH is required because the submodules are cloned using SSH. If you don't have SSH configured, the submodule cloning will fail. 

If you need to run this code on a remote server where SSH is not available, you should first clone the repository locally using the SSH command. Once the repository is cloned locally, you can transfer it to the remote server using `scp`:


```bash
scp -r /path/to/local/physical-cartpole username@remote-server:/path/to/destination/
```

Replace `/path/to/local/physical-cartpole` with the path to your local repository, `username@remote-server` with your remote server's username and address, and `/path/to/destination/` with the path where you want to place the repository on the server.


### Conda Environment

To set up the project environment using Conda, follow these steps:

1. **Install Conda**: If you don't have Conda installed, you can find instructions on how to set it up at the [Conda Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).


2. **Create Conda Environment**

   ```bash
   conda create -n physical_cartpole python=3.9
   ```

3. **Activate Conda Environment**

   ```bash
   conda activate physical_cartpole
   ```

   **Remember to activate the environment each time you start a new terminal tab or window.**



4. **Install Packages from `requirements.txt`**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install Additional Packages**

   ```bash
   pip install watchdog pydot graphviz PyQt6
   ```


   **Bravo! Environment is ready to use!**


## Step 2: Training Neural Network Controller

To train the neural network controller, follow these steps:

1. **Locate Pre-Computed Training Set**

   The precomputed dataset is initially located in the root directory of the repository:
   ```
   ./Experiment-1
   ```

   After executing step 2, the dataset will be moved to the appropriate location within the directory:
   ```
   Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1
   ```

2. **Run Pre-Computed Model**

   If you do not wish to retrain the model and want to use the precomputed model, execute the following commands:
   ```bash
   chmod +x ./step2-no-train.sh
   ./step2-no-train.sh
   ```

   If the `chmod` command does not work, you can run the commands manually from the `step2-no-train.sh` script. Open the script in a text editor and execute each command one by one in your terminal.

3. **Modify Neural Network Parameters**

   To modify the neural network parameters, edit the configuration file located at:
   ```
   Driver/CartPoleSimulation/SI_Toolkit_ASF/config_training.yml
   ```
   You can use a text editor such as `vim` or any other editor of your choice.

4. **Train the Neural Network**

   To train the neural network with the updated parameters, execute:
   ```bash
   chmod +x ./step2.sh
   ./step2.sh
   ```

   If the `chmod` command does not work, you can run the commands manually from the `step2.sh` script. Open the script in a text editor and execute each command one by one in your terminal.

    A newly created model will be added into the following directory:
    ```
    Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models
    ```


## Step 3: Cartpole Simulator

In this section, we will primarily focus on using the Cartpole Simulator to test the performance of trained neural network controllers. This simulator not only allows for performance evaluation but can also be used to generate new datasets for further training. Here, we will describe how to effectively use the simulator to assess your model's capabilities.

### Using the Simulator to Test Neural Network Performance

Follow these steps to evaluate your trained neural network using the Cartpole Simulator:

1. **Choose the Model**:
   - Run the script with the desired model name as an argument to select a specific trained model. If no model name is provided, the default pre-trained model will be used.
   - Available model names can be found in the following folder:
     ```
     Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models
     ```

2. **Launch the GUI**:
   - Execute the commands below to start the Cartpole Simulator GUI:
     ```bash
     chmod +x ./step3.sh
     ./step3.sh [MODEL_NAME]
     ```

3. **Configure the Simulation Settings**:
   - In the GUI, select **"Neural-Imitator"** under the controller options on the right side.
   - Adjust the following settings to test the network effectively:
     - **Initial Position**: Set the starting position of the cart.
     - **Initial Angle**: Set the starting angle of the pole.
     - **Latency**: Define the response time of the controller to changes in the system.

4. **Perform Kicking Simulations**:
   - Use the provided buttons to simulate a kick to the left or right, allowing you to observe how the model reacts to disturbances.

5. **Observe Performance**:
   - Watch the simulation in real-time and note how well the controller maintains the balance of the pole and cart.

6. **Save Your Experiment**:
   - You can save recordings of your experiments as CSV files for further analysis and refinement of the neural network controllers.

By following these steps, you can effectively assess and compare the performance of different trained models in the Cartpole Simulator.

### Note

- If the `chmod` command does not work, open the `step3.sh` script in a text editor and run each command manually from the script.



## Step 4: Conversion of Neural Network Controller using hls4ml

### 1. Edit the Configuration File

You need to modify the file located at `Driver/CartPoleSimulation/SI_Toolkit_ASF/config_hls.yml`. 

This file contains parameters used for converting the neural network controller into HLS (High-Level Synthesis) code via `hls4ml`. However, **this is not the standard `hls4ml` YAML configuration format**. Instead, it is a custom file where these parameters are parsed and then used to generate the actual HLS configuration. For reference, you can find the standard `hls4ml` YAML format here:
[https://fastmachinelearning.org/hls4ml/api/configuration.html](https://fastmachinelearning.org/hls4ml/api/configuration.html).

You can modify several important parameters in the file:
- **PRECISION**: Adjust precision for the network layers.
- **Strategy**: Choose the optimization strategy.
- **ReuseFactor**: Set the reuse factor for the network's HLS implementation.

Additionally, you need to modify the following paths:
- **`path_to_hls_installation`**: 
<br>**Attention, VIVADO 2020.1 is required**. 
<br>Set this to the Vivado installation path. If you're unsure, run:
  ```bash
  echo $XILINX_VIVADO
  ```
  Copy and paste the displayed path here.
- **`path_to_models`**: Set this to:
  ```bash
  './SI_Toolkit_ASF/Experiments/Experiment-1/Models'
  ```
- **`net_name`**: Specify the model name you want to use from the available models in `Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models`.
- **`output_dir`**: Set the directory where output files will be saved. Please put:
  ```bash
  ../../HLS4ML/x3232_12_2_v3
  ```
  This places the `HLS4ML` folder directly inside the root of the repository folder (where files like `.gitignore` are located).

  #### Possible Compatibility Issue with Vivado 2020.1 on Newer Linux Versions
     When using Vivado 2020.1 on newer Linux versions, you may encounter a compatibility issue due to `binutils-2.26` not working well with newer versions of `glibc`. An error like the following may occur:
  
  `/opt/xilinx/Vivado/2021.1/tps/lnx64/binutils-2.26/bin/ld: /lib64/libm.so.6: don't know how to handle section '.relr.dyn' [0x 13]`
  
   A possible workaround is to temporarily remove `ld` within Vivado's `binutils`, as suggested in [this article](https://adaptivesupport.amd.com/s/question/0D54U00005VQKeNSAX/vitis-hls-20211-ld-linker-and-libm-relr-section-error?language=en_US).


### 2. Understanding the Conversion Process

The script you'll execute leverages key methods from the [hls4ml](https://github.com/fastmachinelearning/hls4ml) library to convert the neural network. Specifically, it uses:
- `hls4ml.utils.config_from_keras_model`
- `hls_model = hls4ml.converters.convert_from_keras_model`
- `hls_model.compile`
- `hls_model.build`
- `hls4ml.utils.plot_model`
- `hls4ml.report.read_vivado_report`

If you're interested in understanding how these methods are applied, refer to the script:
```bash
Driver/CartPoleSimulation/SI_Toolkit_ASF/Run/Convert_Network_With_hls4ml.py
```
You can explore the method `train_network` imported from `SI_Toolkit.Training.Train` to see what is being executed in detail.

### 3. Execute the Conversion

To run the conversion process, execute the following commands:
```bash
cd Driver/CartPoleSimulation
python SI_Toolkit_ASF/Run/Convert_Network_With_hls4ml.py
```

Note: it is important to run the python command from the `Driver/CartPoleSimulation` directory.


### 4. Generated Files

Upon completion, an `HLS4ML` folder will be created based on the configurations in the YAML file. The VHDL files generated can be found under:
```bash
./HLS4ML/x3232_12_2_v3/myproject_prj/solution1/impl/vhdl
```

These files are necessary for the Vivado project described in Step 6.


## Step 5: Testing Model on PC - Running Model via PC/Software to Control Cartpole

This step focuses on testing the trained model by controlling the physical Cartpole using a PC. In this demo, we will configure settings that depend on the physical system (such as motor power, track middle, and vertical angle). These calibrated values will be saved and used later in Step 6 when creating the SoC project.

Please also have a look at the [Calibration section](./README.md#calibration) of the README.


### 5.1 Set the Controller

In the following file, set the `controller` to use the neural network imitator:

- **File**: `physical_cartpole/Driver/globals.py`
- **Edit**: Change the controller name to `neural-imitator`:
  ```python
  controller = 'neural-imitator'
  ```

### 5.2 Serial Port Configuration

If you're using a MacBook Pro or a similar system, you might encounter issues identifying the serial port used to control the Cartpole. To work around this issue:

1. **File**: `physical_cartpole/Driver/DriverFunctions/interface.py`
2. **Step**: Comment out the function that automatically detects the serial port ID.
3. **Action**: Manually set the serial port ID. For example, on a Mac:
   ```python
   SERIAL_PORT = '/dev/tty.usbserial-210351B7BD461'  # Replace with your serial port ID
   ```
   > Use the command `ls /dev/tty.*` in your terminal to find your specific serial port ID, ensuring the FPGA is connected and powered on.

### 5.3 Model Configuration

Ensure that the model configuration matches your trained neural network by modifying the following file:

- **File**: `/physical-cartpole/Driver/CartPoleSimulation/Control_Toolkit_ASF/config_controllers.yml`
- **Steps**:
  - Set the correct model path:
    ```yaml
    PATH_TO_MODELS: './CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models/'
    ```
  - Set the model name:
    ```yaml
    net_name: 'Dense-7IN-32H1-32H2-1OUT-0'  # Example TF model name
    ```
  - Ensure input precision and other related parameters are correct:
    ```yaml
    Input_precision: float
    hls4ml: False
    ```

### 5.4 Running the Software to Control Cartpole

1. **Set the Python Path**: Navigate to the `physical-cartpole/` directory and set the `PYTHONPATH` environment variable to the project root. Run the following command:
   ```bash
   export PYTHONPATH=$(pwd):$PYTHONPATH
   ```

2. **Start the Control Script**: Execute the following command from the `physical-cartpole` root directory:
   ```bash
   python Driver/control.py
   ```

3. **Key Bindings for Additional Control**: The following keyboard shortcuts are available for testing various functionalities:
   ```plaintext
   h: Print help message
   K: Calibration: find track middle
   k: PC Control On/Off
   u: Chip Control On/Off
   D: Dance Mode On/Off
   ...
   ```

Values for `ANGLE_HANGING_POLOLU` and `MOTOR_CORRECTION` are determined in this step and incorporated into the settings during implementation. 

***ATTENTION:*** These calibration values (motor power, middle of the track, and vertical angle) will be critical for ensuring the system functions correctly when transitioning to SoC-based control in Step 6. You can repeat this process after the first implementation by opening the `parameters.c` file in Vitis and regenerating the Boot Image.


---

### Note on Calibration

The calibration process during this step ensures that the physical Cartpole is correctly aligned and functional. You will be configuring:

1. **Middle of the Cartpole Track**: Recalibrate each time the Cartpole is powered on.
2. **Motor Power**: Ensure the Cartpole can move freely without friction issues.
3. **Vertical Angle**: Correctly calibrate the potentiometer's dead zone to avoid control interference.

This calibration saves system-specific parameters, which will be reused in the SoC setup in Step 6.

---


## Step 6: Implementation

There are two parts to the system implementation: 
1. generating the NN model bitstream.
2. generating the full Zynq SoC project including board interfaces.

### Generating the FPGA Bitstream (Executable)

1. Vivado 2020.1 is required for this step (GUI version).<br>
Start Vivado (you may need to use VNC or XQuartz if running on a remote server to be able to use the GUI. In this case you may need to use the `-Y` flag in the ssh command).

2. Inside the Vivado GUI:

    - Go to the **Tools** menu in the top toolbar and select **Run Tcl Script**.

    - Ensure that you have the board definition for `digilentinc.com:zybo-z7-20:part0:1.0` installed. This board definition is required for the implementation.

    - Choose the script file `CartpoleDriverZynq_new.tcl` located in the `FPGA/VivadoProjects/` directory, located in the base directory of the cloned GitHub repository, and execute it. This script loads all files needed for implementation.

3. After the script finishes executing, click on **Generate Bitstream**.

4. Once the bitstream generation is complete, click **OK** on the dialog box that appears.

5. The message **"Bitstream Generation Successfully Completed"** will be displayed.

6. If you wish to observe the implementation layout on the FPGA, you can choose **Open Implemented Design**; otherwise, choose **Cancel**.

7. Go to **File** → **Export** → **Export Hardware**. Choose **Platform Type** as **Fixed** and click **Next**.

8. Choose **Output** as **Include Bitstream** and click **Next**.

9. Leave the default choices and click **Next**.

10. Click **Finish**.

11. Close Vivado.


### Generating the SoC Project

1. Navigate to the `Firmware` directory , located in the base directory of the cloned GitHub repository, using the terminal.

2. Ensure that Vitis 2020.1 is installed and available. You can check the version by running:
    ```bash
    vitis -version
    ```
   Once confirmed, start Vitis by running:
    ```bash
    vitis
    ```

4. In the **Select Workspace Directory** dialog box, choose the `Firmware/VitisProjects`.

5. Click **Launch** to open the Vitis workspace.

6. In the Vitis GUI, create a new **Application Project**.

7. Under the **Create New Platform from Hardware (XSA)** tab, select the XSA file by navigating to:
    ```bash
    FPGA/VivadoProjects/CartPoleDriverZynq/cartpole_driver_design_wrapper.xsa
    ```

8. Make sure the **Generate Boot Components** box is selected, then click **Next**.

9. In the **Application Project Details** dialog box:
    - Enter `CartPoleFirmware` as the **Application Project Name**.
    - Choose `ps7_cortexa9_0` as the processor.

10. Click **Next**.

11. Click **Next** again and then **Finish** to create the project.

12. A new project window will open. In this window, expand the `src` folder.

13. Delete all existing `.c` and `.h` files inside the `src` folder.

14. Return to the terminal and execute the following script to populate the `src` folder with necessary files:
    ```bash
    ./Firmware/create_symlinks_cartpole.sh
    ```

15. Return to the Vitis project window and observe the `src` folder being populated with new files.


16. Open `parameters.c` inside the `src` folder and edit the following values, which are specific to the cartpole hardware and were generated in Step 5:<br><br>
   **Important**: The values below are just examples. Be sure to replace them with the actual values generated for your physical setup.
      ```c
      Line 52: float MOTOR_CORRECTION[3] = {0.6310468, 0.0472680, 0.0408973};
      Line 54: float ANGLE_HANGING_POLOLU = 783.0;
      ```

17. Save the `parameters.c` file.

18. Right-click on `CartPoleFirmware [domain_ps7_cortexa9_0]` and select **C/C++ Build Settings**.

19. In the center box, choose **Libraries**.

20. In the **Libraries** pane, click the `+` sign, and in the **Enter Value** box, type:
    ```bash
    m
    ```

21. Click **Apply and Close**.

22. Update the input and output vector normalization values in `src/Zynq/neural-imitator.c` with the new model data from:
    ```bash
    Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models/[ModelName]
    ```
      The following files should be used:  
          - `normalization_vec_a.csv`  
          - `normalization_vec_b.csv`  
          - `denormalization_vec_A.csv`  
          - `denormalization_vec_B.csv`


    Example normalization values:
    ```c
    float hls_normalize_a[] = {0.05600862, 1.00000000, 1.00000000, 5.20657063, 0.88941061, 1.00000000, 5.05586720};
    float hls_normalize_b[] = {0.02947879, 0.00000000, 0.00000000, 0.01642668, 0.00083601, 0.00000000, 0.00045502};
    float hls_denormalize_A[] = {1.0};
    float hls_denormalize_B[] = {0.0};
    ```

      Additionally, update the model input/output size and precision if necessary in `src/Zynq/neural-imitator.c` and `neural-imitator.h`.

24. Right-click on `CartPoleFirmware [domain_ps7_cortexa9_0]` and choose **Build Project**.

25. Right-click on `CartPoleFirmware [cartpole_driver_design_wrapper]` and choose **Create Boot Image**.

26. Leave the default settings and click **Create Image**.

27. Retrieve the `.bin` file from the path displayed on the console to load onto an SD card and program the FPGA.


## Step 7

Load Image on SD card and onto FPGA

This is the final step.

Once the image is successfully loaded onto the SD card and FPGA, the system will be fully configured and ready for operation.
There are four switches on the board: the two in the middle serve important functions. One of the switches calibrates the center of the track, while the other allows the cartpole to stabilize either in the upward or downward position. Play with them to see what happens!

Congratulations on completing the setup!
