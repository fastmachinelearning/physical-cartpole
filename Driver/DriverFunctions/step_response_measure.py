# measurements from cartpole, controlled by state machine.
# control.py calls update_state() if state is not 'idle'
import time
from globals import *
from CartPoleSimulation.CartPole.state_utilities import (
    ANGLE_IDX,
    ANGLED_IDX,
    POSITION_IDX,
    POSITIOND_IDX,
)

ACCOUNT_FOR_MOTOR_CORRECTION = True
ACCELERATE_FIRST_TO_LEFT = True
BIDIRECTIONAL = True
FRICTION_SLOWDOWN = False

# Direction for measurement.py with the cart accelerating to right:
STARTING_POSITION = -0.15  # cart starting position (in m)
ENDING_POSITION = 0.1  # position to turn off motor
RESET_Q = 0.5
SPEED_STEP = 0.1
STARTING_SPEED = 0.25  # doesn't work for low values for some reason
ENDING_SPEED = 1.0
PAUSE_BEFORE_STEP_S = .5  # pause after reset to start position before starting step
FRICTION_SLOWDOWN_TIME_S = 1  # time at end to just turn off motor and glide to stop
STEP_TIMEOUT_S = 10


# Call this function if you wish cart to accelerate to left instead
def get_parameters_opposite_direction():
    global STARTING_POSITION, ENDING_POSITION, RESET_Q, SPEED_STEP, STARTING_SPEED, ENDING_SPEED

    STARTING_POSITION = -STARTING_POSITION
    ENDING_POSITION = -ENDING_POSITION
    RESET_Q = -RESET_Q
    SPEED_STEP = -SPEED_STEP
    STARTING_SPEED = -STARTING_SPEED
    ENDING_SPEED = -ENDING_SPEED


class StepResponseMeasurement:
    def __init__(self):

        self.motor = MOTOR

        if self.motor == 'POLOLU':
            self.motor_correction = MOTOR_CORRECTION_POLOLU
        elif self.motor == 'ORIGINAL':
            self.motor_correction = MOTOR_CORRECTION_ORIGINAL
        else:
            raise Exception('Unknown motor')

        if ACCELERATE_FIRST_TO_LEFT:
            get_parameters_opposite_direction()

        self.assign_parameters()

        self.second_round = False  # In case of bidirectional measurement, detect second "round", the opposite direction

        self.state = 'idle'
        self.speed = self.reset_Q
        self.Q = 0.0
        self.time_state_changed = time.time()

        self.state_logging = 'idle'

        if abs(STARTING_SPEED * MOTOR_FULL_SCALE_SAFE) - self.motor_correction[1] < 0:
            minimal_starting_speed = self.motor_correction[1]/MOTOR_FULL_SCALE_SAFE
            raise Exception('To small starting speed ({}). When ACCOUNT_FOR_MOTOR_CORRECTION is True minimal starting speed is {}'.format(STARTING_SPEED, minimal_starting_speed))

    def rescale_motor_command(self, Q):
        if Q > 0:
            return (Q * MOTOR_FULL_SCALE_SAFE - self.motor_correction[1]) / self.motor_correction[0]
        else:
            return (Q * MOTOR_FULL_SCALE_SAFE + self.motor_correction[1]) / self.motor_correction[0]


    def assign_parameters(self):

        if ACCOUNT_FOR_MOTOR_CORRECTION:
            self.reset_Q = self.rescale_motor_command(RESET_Q)
            self.speed_step = SPEED_STEP * MOTOR_FULL_SCALE_SAFE / self.motor_correction[0]
            self.starting_speed = self.rescale_motor_command(STARTING_SPEED)
            self.ending_speed = self.rescale_motor_command(ENDING_SPEED)
        else:
            self.reset_Q = RESET_Q
            self.speed_step = SPEED_STEP
            self.starting_speed = STARTING_SPEED
            self.ending_speed = ENDING_SPEED

    def start(self):
        print('Start measurement!')
        self.state = 'start'
        self.Q = 0.0

    def stop(self):
        print('Stop measurement!')
        self.Q = 0.0
        self.state = 'idle'

    def get_state(self):
        return self.state

    def is_idle(self):
        return self.state == 'idle'

    def is_running(self):
        return not self.is_idle()

    def update_state(self, angle: int, position: int, time: float):
        if self.state == 'idle':
            self.state_logging = 'idle'
            self.Q = 0.0
            return
        elif self.state == 'start':  # init measurement
            self.state_logging = 'start'
            self.speed = self.starting_speed
            self.state = 'resetting'
            self.time_state_changed = time
        elif self.state == 'resetting':  # moving back to start
            self.state_logging = 'resetting'
            if (STARTING_POSITION < 0 and position > STARTING_POSITION) or (
                    STARTING_POSITION > 0 and position < STARTING_POSITION):
                self.Q = -self.reset_Q
            else:
                self.Q = 0.0
                self.state = 'pausing_before_step'
                self.time_state_changed = time
            self._check_timeout(time, raise_error=True)
        elif self.state == 'pausing_before_step':
            self.state_logging = 'pausing_before_step'
            if time - self.time_state_changed > PAUSE_BEFORE_STEP_S:
                self.state = 'starting_step'
                self.time_state_changed = time
        elif self.state == 'starting_step':
            self.state_logging = 'starting_step'
            if abs(self.speed) < abs(self.ending_speed):
                self.speed += self.speed_step
                print(self.speed)
                self.Q = self.speed
                self.state = 'moving'
                self.time_state_changed = time
            else:
                if BIDIRECTIONAL and (self.second_round is False):
                    get_parameters_opposite_direction()
                    self.assign_parameters()
                    self.second_round = True
                    self.state = 'start'
                else:
                    if BIDIRECTIONAL:
                        get_parameters_opposite_direction()
                        self.assign_parameters()
                        self.second_round = False
                    self.state = 'idle'

                self.speed = 0
                self.Q = 0.0
                self.time_state_changed = time
        elif self.state == 'moving':
            self.state_logging = 'moving'
            if (0 < ENDING_POSITION < position) or (0 > ENDING_POSITION > position):
                self.Q = 0.0
                if FRICTION_SLOWDOWN:
                    self.state = 'friction_slowdown'
                else:
                    self.state = 'resetting'
                self.time_state_changed = time
            if self._check_timeout(time, raise_error=False):
                self.Q = 0.0
                if FRICTION_SLOWDOWN:
                    self.state = 'friction_slowdown'
                else:
                    self.state = 'resetting'
        elif self.state == 'friction_slowdown':
            self.state_logging = 'friction_slowdown'
            self.Q = 0.0
            if time - self.time_state_changed > FRICTION_SLOWDOWN_TIME_S:
                self.state = 'resetting'
                self.time_state_changed = time
        else:
            raise Exception(f'unknown state {self.state}')

    def _check_timeout(self, time, raise_error=False):
        if time - self.time_state_changed > STEP_TIMEOUT_S:
            if raise_error:
                self.stop()
                raise TimeoutError(f'step took more than {STEP_TIMEOUT_S} to complete')
            else:
                return True
        else:
            return False

    def __str__(self):
        return f' Step Response (State:{self.state_logging}, Speed:{self.speed}, Q:{self.Q})'
