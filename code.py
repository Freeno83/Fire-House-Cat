"""
Fire House Cat - Pickles Fire Pole
Last Modified by Nick Robinson 12th May 2021
This circuit python code has the following function/flow:
1) At boot up, move Pickels to the top of the pole if not already there
2) Once at the top of the pole, wait for a timer or user input (botton push, etc.)
3) Upon receiving user input, pickles drops down the pole, slowing near the bottom
4) At the bottom, pickles pauses and then "climbs" back up the pole
5) Once at the top of the pole again, return to step 2)
"""

# Library imports
import board
import time
from digitalio import DigitalInOut, Pull, Direction

#This variable controls the time in between drops
CYCLE_TIME = 5 # minutes

# These variables affect how pickles acts when climbing up
CLIMB_RUN = 2 # seconds to climb when going up
CLIMB_PAUSE = 0.5 # seconds to pause when going up
CLIMB_FALL = 0.5 # seconds to fall when climbing up

# This variable controls how long pickles pauses at the bottom
BOTTOM_PAUSE = 3 # seconds

# These variables affect the braking action at the bottom of a fall
BOTTOM_SLOW = 1 # the total duration in seconds that braking will occur in
BRAKE_TIME = 0.2 # The duration in seconds between braking events (ex: 0.2 = 5 times/sec)
BRAKE_RATE = 0.25 # % of BRAKE_TIME in which the brake will be set (duty cycle)

# Initialize I/O
if "IO7" in dir(board):
    print("Setting pins for ESP32s2")
    sound = DigitalInOut(board.IO7)
    light = DigitalInOut(board.IO8)
    brake = DigitalInOut(board.IO9)
    clutch = DigitalInOut(board.IO10)
    motor = DigitalInOut(board.IO11)

    drop = DigitalInOut(board.IO12)
    upper_stop = DigitalInOut(board.IO13)
    lower_slow = DigitalInOut(board.IO14)

else:
    print("Setting pins for Metro Express M0")
    sound = DigitalInOut(board.D2)
    light = DigitalInOut(board.D3)
    brake = DigitalInOut(board.D4)
    clutch = DigitalInOut(board.D5)
    motor = DigitalInOut(board.D6)

    drop = DigitalInOut(board.D7)
    upper_stop = DigitalInOut(board.D8)
    lower_slow = DigitalInOut(board.D9)

for output in [sound, light, brake, clutch, motor]:
    output.direction = Direction.OUTPUT

for input in [drop, upper_stop, lower_slow]:
    input.direction = Direction.INPUT
    input.pull = Pull.UP


# User defined functions
def print_status(phrase):
    """Prints the time in seconds since start and a phrase"""
    print("{} - {} ".format(int(time.monotonic()), phrase))


def set_drive(brake_val, clutch_val, motor_val):
    """Sets the state of each drive line component"""
    brake.value, clutch.value, motor.value = brake_val, clutch_val, motor_val


def rising_edge(curr_val, prev_val):
    """Determines if a rising edge event has occured"""
    if curr_val is not prev_val:
        if curr_val is True:
            return True
	else:
	    return False

def falling_edge(curr_val, prev_val):
    """Determines if a falling edge event has occured"""
    if curr_val is not prev_val:
        if curr_val is False:
            return True
	else:
	    return False


def home_pickles():
    """Return pickles to the top of the pole smoothly"""
    at_top = False

    if upper_stop.value is False: # Check if pickles is already at the top
	at_top = True
        set_drive(True, False, False)

    prev_upper_stop = True
    while not at_top: # If pickles is not at top, move him there
        set_drive(False, True, True)

        if falling_edge(upper_stop.value, prev_upper_stop):
            at_top = True
            set_drive(True, False, False)

        prev_upper_stop = upper_stop.value
        time.sleep(0.005)


home_pickles()
print_status("Homed")

# Main Program
state = 0
prev_drop = True
cycle_start = time.monotonic()

while True:
    if state is 0:
        if falling_edge(drop.value, prev_drop) or time.monotonic()-cycle_start > CYCLE_TIME*60:
            print_status("Dropping")
            state = 1


    if state is 1: # drop down, slow at the end
        set_drive(False, False, False)
        sound.value, light.value = True, True

        if falling_edge(lower_slow.value, prev_lower_slow):
            slow_start = time.monotonic()
            print_status("Stopping")

            while time.monotonic()-slow_start<BOTTOM_SLOW: # feather brake
                set_drive(True, False, False)
                time.sleep(BRAKE_TIME*BRAKE_RATE)
                set_drive(False, False, False)
                time.sleep(BRAKE_TIME-BRAKE_TIME*BRAKE_RATE)

            sound.value, light.value = False, False
            pause_start = time.monotonic()
            print_status("Stopped")
            state = 2


    if state is 2: # wait at the bottom of the pole
        if time.monotonic()-pause_start > BOTTOM_PAUSE:
            drive_start = time.monotonic()
            print_status("Climbing")
            state = 3


    if state is 3: # climb back up in a pause and go fashion
        drive_time = time.monotonic()-drive_start

        if drive_time < CLIMB_RUN:
            set_drive(False, True, True) # climb up

        if drive_time > CLIMB_RUN and drive_time < CLIMB_RUN+CLIMB_FALL:
            set_drive(False, False, True) # fall down slightly

        if drive_time > CLIMB_RUN+CLIMB_FALL:
            set_drive(True, False, True) # pause climb

        if drive_time > CLIMB_RUN+CLIMB_FALL+CLIMB_PAUSE:
            drive_start = time.monotonic() # reset climb cycle timer

        if falling_edge(upper_stop.value, prev_upper_stop):
            set_drive(True, False, False) # stop when the upper sensor is reached
            cycle_start = time.monotonic()
            print_status("Top reached")
            state = 0	


    prev_drop = drop.value
    prev_lower_slow = lower_slow.value
    prev_upper_stop = upper_stop.value
    time.sleep(0.005)
