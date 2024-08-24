# Cartpole Demo

An env for users needs to be created using the proper conda env file: 

```
conda create -n physical_cartpole python=3.9
```

User environments should also have:

```
pip install watchdog pydot graphviz
```

## Step 1: Model Generation

```
physical_cartpole/Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Trial_14__17_08_2024/Models
```

- [already done on our server] Create Directory named `Experiments` under `../CartPoleSimulation/SI_Toolkit_ASF`
- [already done on our server] Place Training Data folder `Experiment_14` under `Experiments`
- [already done on our server] Edit in `.yml` file `/CartPoleSimulation/SI_Toolkit_ASF/config_training.yml`: 

    Important paths to set correctly:
    - `path_to_experiment: 'Experiment_14'`
    - `PATH_TO_EXPERIMENT_FOLDERS: './SI_Toolkit_ASF/Experiment/'`

- [already done on our server] Navigate to:
  
  ```
  ../CartPoleSimulation/SI_Toolkit_ASF/Run/A1_Create_Normalization_File.py
  ```
  
  Edit configuration of this `.py` to make the working directory `CartPoleSimulation`.

- Execute:

  ```
  python A1_Create_Normalization_File.py
  ```

- [already done on our server] Navigate to:

  ```
  ../CartPoleSimulation/SI_Toolkit_ASF/Run/A2_Train_Network.py
  ```

  Edit configuration of `A2_Train_Network.py` to make the working directory `CartPoleSimulation`.

- Execute:

  ```
  python A2_Train_Network.py
  ```

A newly created model is added into the `../CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment_14/Models` directory.

## Step 2: Cartpole Simulator

- [in the physical_cartpole directory] 

  ```
  conda activate physical_cartpole
  ```

- [need to be in physical_cartpole folder same level as requirements.txt] 

  ```
  pip install -r requirements.txt
  ```

- [in folder `./Driver/CartpoleSimulation`] execute:

  ```
  python run_cartpole_gui.py
  ```

  Use GUI to experiment with different settings and save recordings as svc as data.

## Step 4: Conversion of Model through hls4ml

Edit `config_hls4ml.yml` to do the following:
- Point to correct Vivado path
- Point to correct Model folder
- Correct Model name

Adjust other hls setting if desired.

Execute:

```
~/cartpole/common/physical-cartpole/Driver/CartPoleSimulation$ python SI_Toolkit_ASF/Run/Convert_Network_With_hls4ml.py 
```

HLS4ML folder will be created upon completion.

All vhdl files generated under:

```
./HLS4ML/d3232_12_2_v0/myproject_prj/solution1/impl/vhdl
```

Need to be transferred into the Vivado Project in Step 6.

## Step 5: Testing Model on PC - Running Model via PC/Software to control Cartpole

Relevant script is `physical_cartpole/Driver/control.py`.

Following edits need to be made:

1. **Edit `globals.py`**: 

   ```
   controller name = neural-imitator
   ```

2. **Edit `interface.py`**:

   The serial port ID of the PC used to control the cartpole needs to be set correctly (we ran into issues when using a Macbook Pro and worked around as follows; this might not be an issue for other PCs, needs to be checked).

   We hardwired the Serial Port ID by commenting out the function which returns the serial port ID:

   ```python
   # from serial.tools import list_ports
   # ports = list(serial.tools.list_ports.comports())
   # serial_ports_names = []
   # print('\nAvailable serial ports:')
   # for index port in enumerate(ports):
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

   And setting the variable directly instead:

   ```python
   SERIAL_PORT = '/dev/tty.usbserial-210351B7BD461' 
   ```

   [this is a specific ID for the specific Macbook Pro and USB connector we have used].

   We used the following command in Mac terminal to display the USB Serial Port ID:

   ```
   ls /dev/tty.* 
   ```

   (from any directory) making sure the FPGA is connected to the computer and ON.

3. **Navigate to script**:

   ```
   /physical-cartpole/Driver/CartPoleSimulation/Control_Toolkit_ASF/config_controllers.yml
   ```

   Match the model name and Model paths:
   
   ```
   PATH_TO_MODELS: './CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment_14/Models/'
   ```
   
   ```
   net_name: 'Dense-7IN-32H1-32H2-1OUT-0'  # TF
   ```

   ```
   Input_precision = float 
   ```

   ```
   hls4ml = False
   ```

4. Go back to `/physical-cartpole/`

   Execute:

   ```
   physical-cartpole$ python Driver/control.py
   ```

   Use keyboard shortcuts to run different calibration modes; hitting `h` on the keyboard will display all options.
   
   **Key Bindings:**
   ```
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
   : Key not assigned
   /: Key not assigned
   5: Key not assigned
   ESC: Start experiment termination
   ```

## Step 6: Implementation

Start Vivado2020.1 within folder by executing:

```
~/vivado.2020.1
/physical-cartpole/FPGA/VivadoProjects$ ~/vivado.2020.1
```

Inside Vivado GUI: 
- Go to Tools in top toolbar and choose "Run tcl script"
  - Choose `CartpoleDriverZynq_21_08_2024.tcl` and execute.

  This script loads all files needed for implementation. When the script finishes:
- Execute `Generate Bitstream`
- After the conclusion of this step click `OK` on the next dialog box.
  - Bitstream will be written and the message "Bitstream Generation Successfully Completed" will be displayed.
- If you wish to observe the implementation layout on the FPGA you can choose `Open Implemented Design`, otherwise choose `Cancel`.
- Go to File -> Export -> Export Hardware [choose Platform Type as Fixed] click `Next`.
  - Choose Output as [Include Bitstream] click `Next`.
  - Leave default choices and click `Next`.
  - Finish.
  - Close Vivado.
- Navigate to `/physical-cartpole/Firmware$`.
- Execute:

  ```
  physical-cartpole/Firmware$ source /tools/Xilinx/Vitis/2020.1/settings64.sh
  ```

- Start Vitis 2020.1:

  ```
  physical-cartpole/Firmware$ ./common/xilinx/Vitis2020.1/bin/vitis
  ```

- Choose Vivado Project, then Xilinx Platform
- Wait until both projects have been loaded.
- You can now continue work with your final project.

