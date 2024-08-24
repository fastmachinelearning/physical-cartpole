# Instructions

An env for users needs to created using the proper conda env file: 
`[conda create -n physical_cartpole python=3.9]`

User environments should also have
`pip install watchdog pydot graphviz`

Since the environment is set up, just do:
`conda activate physical_cartpole`

## Step1: Model Generation:

`physical_cartpole/Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Trial_14__17_08_2024/Models`

1.	[already done on our server] Create Directory named Experiments under` ../ CartPoleSimulation/SI_Toolkit_ASF`

2.	[already done on our server] Place Training Data folder `Experiment_14` under `Experiments` 

3.	Edit in .yml file `/CartPoleSimulation/SI_Toolkit_ASF/config_training.yml`: 

Important paths to set correctly:

    - path_to_experiment: ‘Experiment_14’
    - PATH_TO_EXPERIMENT_FOLDERS: `./SI_Toolkit_ASF/Experiment/`

4.	[already done on our server]  Navigate to:
`../CartPoleSimulation/SI_Toolkit_ASF/Run/A1_Create_Normalization_File.py`<br>
edit configuration of this .py to make working directory CartPoleSimulation

5.	Execute python `A1_Create_Normalization_File.py`

6.	[already done on our server] Navigate to `../CartPoleSimulation/SI_Toolkit_ASF/Run/A2_Train_Network.py` <br>
Edit Configuration of `A2_Train_Network.py` to make working directory CartPoleSimulation

7.	Execute python `A2_Train_Network.py` <br>
  A newly created model is added into the: `../CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment_14/Models directory`



## Step2: Cartpole simulator: 


1.	[in the physical_cartpole directory] conda activate physical_cartpole

2.	 [need to be in physical_cartpole folder same level as requirements.txt]    <br>`pip install -r requirements.txt`

3.	`[in folder ./Driver/CartpoleSimulation]` execute `python run_ cartpole_gui.py`

4.	Use GUI to experiment with different settings and save recordings as svc as data

## Step4: Conversion of Model through hls4ml

1.	Edit `config_hls4ml.yml` to do the following:
    - Point to correct Vivado path
    - Point to correct Model folder
    - Correct Model name

    Adjust other hls setting if desired

2.	Execute <br>
`~/cartpole/common/physical-cartpole/Driver/CartPoleSimulation$ python SI_Toolkit_ASF/Run/Convert_Network_With_hls4ml.py` 


HLS4ML folder will be created upon completion

All vhdl files generated under
 
`./HLS4ML/d3232_12_2_v0/myproject_prj/solution1/impl/vhdl` need to be transferred into the **Vivado Project in Step 6**.




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

`PATH_TO_MODELS: './CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment_14 /Models/'`

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

1. Start Vivado2020.1 within folder  by `executing ~/vivado.2020.1
  /physical-cartpole/FPGA/VivadoProjects$ ~/vivado.2020.1`

2.	Inside Vivado GUI: 

    Go to Tools in top toolbar and choose “Run tcl script”

                `Choose CartpoleDriverZynq_21_08_2024.tcl` and execute

                This script loads all files needed for implementation. When the script finishes

3. Execute Generate Bitstream

4. After the conclusion of this step, click OK on the next dialog box

5. Bitstream will be written and message “Bitstream Generation Successfully Completed” will be displayed

6. If you wish to observe the implementation layout on the FPGA, you can choose Open Implemented Design, otherwise choose Cancel

7. Go to File –> Export -> Export Hardware [choose Platform Type as Fixed] click Next

8. Choose Output as [Include Bitstream] click Next

9. leave default choices and click Next

10. Finish

11. Close Vivado

12.  Navigate to `/physical-cartpole/Firmware$`

13. Execute `physical-cartpole/Firmware$ source /tools/Xilinx/Vitis/2020.1/settings64.sh`

14. Start Vitis 2020.1: `physical-cartpole/Firmware$` vitis

15. In Select Workspace Directory dialog box create a new folder named VitisProjects under `physical-cartpole/Firmware/`

16. Click Launch

17. In Vitis GUI: Create new Application Project

18. Choose Create New Platform from hardware (XSA) Tab

19. Navigate to:  
`physical-cartpole/FPGA/VivadoProjects/CartPoleDriverZynq/
cartpole_driver_design_wrapper.xsa`

20. Click OK

21. Make sure the Generate Boot Components box is selected in this dialog box

22. Click Next

23. In the Application Project Details Box: 
  - enter CartPoleFirmware as Application Project Name
  - Choose ps7_cortexa9_0

24. Click Next

25. Click Next again

26. Click Finish

27. A new project window opens

28. Expand src folder

29. Delete all .c and .h files

30. Return to terminal

31. Uncomment reference to zynq implementation for cartpole firmware in the `create_symlinks.sh` file

32. Execute `physical-cartpole/Firmware/./create_symlinks.sh`

33. You can go back to Vitis project window and observe the src folder being populated with several new files

34. Under src open `parameters.c` and edit as follows

35. [these values are specific to the cartpole hardware] 
  `Line 52: float MOTOR_CORRECTION[3] = {0.6310468, 0.0472680, 0.0408973};`

36. `Line 54: float ANGLE_HANGING_POLOLU = 783.0; `

37. Save `parameters.c`

38.	Right click on CartPoleFirmware[domain_ps7_cotexa9_0] and C/C++ Build Settings

39. In the box at the center choose Libraries

40. In the Libraries pane click on the + sign

41. Enter m in the Enter Value Box

42. Choose Apply and Close

43. Each time a new model is built do the following:

      Replace the in and out vector normalizations in neural-imitator.c values with the data from
      `test1/physicalcartpole/Driver/CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment_14/Models/`
      [Use the name of model folder used]

      These are the values we used in our case:

      ```float hls_normalize_a[] = {0.05600862,1.00000000,1.00000000,5.20657063,0.88941061,1.00000000,5.05586720};
      float hls_normalize_b[] = {0.02947879,0.00000000,0.00000000,0.01642668,0.00083601,0.00000000,0.00045502};
      float hls_denormalize_A[] = {1.0};
      float hls_denormalize_B[] = {0.0};
      ```

      Similarly, in neural-imitator.h update model input output size if new model is sized differently or has different precision.

44. Right click on CartPoleFirmware[domain_ps7_cotexa9_0] and choose Build Project

45. Right Click on CartPoleFirmware[cartpole_driver_design_wrapper] and choose Create Boot Image

46. Leave default settings and Create Image

47. Retrieve the .bin file from the path displayed to load on an SD card and program FPGA with it

## Step7

Load Image on SD card and onto FPGA

## Step8

Calibrate Cartpole (important parameters: hanging angle, motor power)

Execute `control.py` (see Step 5)

This Step is still under construction… Will be updated soon.

[Hold cartpole in down position and note the value of angle_raw

Values for ANGLE_HANGING_POLOLU and MOTOR_CORRECTION values are determined in this step and incorporated into the settings during implementation

This can be repeated after the first implementation run by opening parameters.c file with Vitis repeatedly and regenerating Boot Image.]


 


