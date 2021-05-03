import math
# Angle unit conversion adc to radians: (ANGLE_TARGET + ANGLE DEVIATION - ANGLE_NORMALIZATION/2)/ANGLE_NORMALIZATION*math.pi
# ANGLE_KP = ANGLE_KP*ANGLE_NORMALIZATION/math.pi
ANGLE_AVG_LENGTH = 10  # adc routine in firmware reads ADC this many times quickly in succession to reduce noise
ANGLE_NORMALIZATION = 4095 # Range of angle values #
ANGLE_HANGING = 3456 # Value from sensor when pendulum is at stable equilibrium point
ANGLE_DEVIATION = ANGLE_NORMALIZATION - ANGLE_HANGING # Angle deviation from goal
ANGLE_HANGING_NORMALIZATION = (ANGLE_DEVIATION + ANGLE_HANGING - ANGLE_NORMALIZATION/2)/ANGLE_NORMALIZATION*2*math.pi # Should be equal to pi in radians

# Position unit conversion adc to meters: POSITION_TARGET = POSITION_TARGET/POSITION_NORMALIZATION*TRACK_LENGTH
# POSITION_KP = POSITION_KP*POSITION_NORMALIZATION/TRACK_LENGTH
POSITION_NORMALIZATION = 4660 # This is an empirical approximation
POSITION_FULL_SCALE_N = int(POSITION_NORMALIZATION)/2 # Corrected position full scale - cart position should range over +- this value if calibrated for zero at center
TRACK_LENGTH = 0.396 # Total usable track length in meters

# Direction for measurement.py - n = 2 for right, n = 1 for left.
n = 2

ratio = 1.05

def inc(param):
    if param < 2:
        param = round(param + 0.1, 1)
    else:
        old = param
        param = round(param * ratio)
        if param == old:
            param += 1
    return param


def dec(param):
    if param < 2:
        param = max(0, round(param - 0.1, 1))
    else:
        old = param
        param = round(param / ratio)
        if param == old:
            param -= 1
    return param