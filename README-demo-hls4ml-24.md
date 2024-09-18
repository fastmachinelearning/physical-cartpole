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

 Execute the following commands to start the GUI application:
   ```bash
   chmod +x ./step3.sh
   ./step3.sh [MODEL_NAME]
   ```

   - The `MODEL_NAME` parameter is optional. If not provided, the script will use the default pre-trained model.
   - If you want to test different models trained at step 2, you can specify the `MODEL_NAME` as an argument. The available model names are located in the folder:
     ```
     Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models
     ```

   This will launch the Cartpole simulator GUI.

2. **Experiment with Different Settings**

   Use the GUI to experiment with various settings and observe how the controller performs.

3. **Save Recordings**

   You can save recordings of your experiments as CSV files. These recordings can be used for further analysis and training of the neural network controllers.

### Note

- If the `chmod` command does not work, open the `step3.sh` script in a text editor and run each command manually from the script.

By passing different model names, you can easily test and compare the performance of various trained models.

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



## Step 5. Testing model on PC - Running Model via PC/Software to control Cartpole:

Relevant script is physical_cartpole/Driver/control.py

Following edits need to be made:

### 5.1 

`physical_cartpole/Driver/globals.py`: edit controller name = neural-imitator; 


### 5.2 

`physical_cartpole/Driver/DriverFunctions/interface.py`

the serial port ID of the PC used to control the cartpole needs to be set correctly (we ran into issues when using a Macbook Pro and worked around as follows, might not be an issue for other PCs, needs to be checked)

we hardwired the Serial Port ID by commenting out the function which returns serial port ID:

```
    # from serial.tools import list_ports
    # ports = list(serial.tools.list_ports.comports())
    # serial_ports_names = []
    # print('\nAvailable serial ports:')
    # for index, port in enumerate(ports):
    #     serial_ports_names.append(port.device)
    #     print(f'{index}: port={port.device}; description={port.description}')
    # print()
    #
    # if chip_type == "STM":
    #     expected_description = 'USB Serial'
    # elif chip_type == "ZYNQ":
    #     expected_description = 'Digilent Adept USB Device - Digilent Adept USB Device'
    # else:
    #     raise ValueError(f'Unknown chip type: {chip_type}')
    #
    # SERIAL_PORT = None
    # for port in ports:
    #     if port.description == expected_description:
    #         SERIAL_PORT = port.device
    #         break
    # if SERIAL_PORT is None:
    #     message = f"Searching serial port by its expected description - {expected_description} - not successful."
    #     if serial_port_number is not None:
    #         print(message)
    #     else:
    #         raise Exception(message)
    #
    # if SERIAL_PORT is None and serial_port_number is not None:
    #     if len(serial_ports_names)==0:
    #         print(f'No serial ports')
    #     else:
    #         print(f"Setting serial port with requested number ({serial_port_number})\n")
    #         SERIAL_PORT = serial_ports_names[serial_port_number]
```

And setting variable directly instead:

`SERIAL_PORT = '/dev/tty.usbserial-210351B7BD461'` [this is a specific ID fpor the specific Macbook Pro and USB connector we have used]

We used the following command in Mac terminal to display the USB Serial Port ID:

ls /dev/tty.* (from any directory), making sure the FPGA is connected to the computer and ON. 

### 5.3 Navigate to script: 

`/physical-cartpole/Driver/CartPoleSimulation/Control_Toolkit_ASF/config_controllers.yml`

Match the model name and Model paths:

`PATH_TO_MODELS: './CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-14 /Models/'`

`net_name: 'Dense-7IN-32H1-32H2-1OUT-0'  # TF`

`Input_precision = float `

`hls4ml = False`

### 5.4 

go back to /physical-cartpole/

execute `/physical-cartpole$ python Driver/control.py`

use keyboard shortcuts to run different calibration modes, hitting ‘h’ on the keyboard will display all options

```
Key Bindings:
 h: Print this help message
 ?: Print this help message
 K: Calibration: find track middle
 k: PC Control On/Off
 u: Chip Control On/Off
 D: Dance Mode On/Off
 m: Change Experiment Protocol: running and recording predefined sequence of movements
 n: Start/Stop Experiment Protocol
 N: Start Experiment Protocol from Chip
 l: Start/Stop recording to a CSV file
 L: Start/Stop time limited recording to a CSV file
 6: Start/Stop sending data to Live Plotter Server - real time visualization
 7: Save data and figure at Live Plotter Server
 8: Reset Live Plotter Server
 ;: Switch target equilibrium
 ]: Increase target position
 [: Decrease target position
 b: Start precise angle measurement - multiple samples
 =: Finetune zero angle - increase angle deviation parameter
 -: Finetune zero angle - decrease angle deviation parameter
 9: Increase additional latency
 0: Decrease additional latency
 j: Joystick On/Off
 .: Key not assigned
 ,: Key not assigned
 /: Key not assigned
 5: Key not assigned
  ESC: Start experiment termination
```


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

22. Each time a new model with a different architecture is built, update the input and output vector normalization values in `src/Zynq/neural-imitator.c` with the new model data from:
    ```bash
    Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models/
    ```

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


## Step7

Load Image on SD card and onto FPGA

## Step8

Calibrate Cartpole (important parameters: hanging angle, motor power)

Execute `control.py` (see Step 5)

This Step is still under construction… Will be updated soon.

[Hold cartpole in down position and note the value of angle_raw

Values for ANGLE_HANGING_POLOLU and MOTOR_CORRECTION values are determined in this step and incorporated into the settings during implementation

This can be repeated after the first implementation run by opening parameters.c file with Vitis repeatedly and regenerating Boot Image.]


 


