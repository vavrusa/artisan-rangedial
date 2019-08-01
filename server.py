#!/usr/bin/env python
# Adapter for Supermechanical Range Dial temperature probe.
# See https://supermechanical.com/rangedial/
import struct, sys, time
import logging
import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART

# Debug logging
logging.basicConfig(level=logging.INFO)

# Optional device name and log file
deviceName = sys.argv[1] if len(sys.argv) > 1 else 'RangeWhite24'
logFile = sys.argv[2] if len(sys.argv) > 2 else None

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()

# Scan for UART devices with matching name.
def find_device(adapter, name):
    logging.info('searching for UART device {0}'.format(name))
    try:
        adapter.start_scan()
        while True:
            devices = set(UART.find_devices())
            for device in devices:
                logging.debug('found UART device {0}'.format(device.name))
                if device.name == name:
                    return device

            # Wait for the device to come up
            time.sleep(1)

    finally:
        adapter.stop_scan()

def to_fahrenheit(celsius):
    return 9.0/5.0 * celsius + 32

# Parse datapoint from the Range dial.
# The Range sends three types of messages.
# First byte defines the message types:
#  * 'D' is initialization message
#  * 'V' is some kind of control device followed by 2 bytes
#  * 'T' is temperature data followed by 4 bytes
# The Range dial has two ports for temperature sensors, upper and lower.
#  * When the upper port is used, the first two bytes will be set to '\x81\x0c'.
#  * When the lower port is used, the last two bytes will be set to '\x81\x0c'.
# The temperature is a fixed-point number in celsius, e.g. 2868 equals to 28.68 degrees C
def parse_datapoint(data, celsius = False):
    if len(data) == 0:
        return

    # Some kind of control command (e.g. 'V\x08\0x05')
    if data[0] == 'V':
        return

    # Temperature data point
    if data[0] == 'T':
        data = data[1:]
        value = data[2:] if data[:2] == '\x81\x0c' else data[:2]
        value = struct.unpack('>H', value)
        if len(value) > 0:
            value = value[0] / 100.0
            return value if celsius else to_fahrenheit(value)

# Main function implements the program logic so it can run in a background
# thread.  Most platforms require the main thread to handle GUI events and other
# asyncronous events like BLE actions.  All of the threading logic is taken care
# of automatically though and you just need to provide a main function that uses
# the BLE provider.
def main():
    ble.clear_cached_data()
    UART.disconnect_devices()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()

    # Find UART device
    device = find_device(adapter, deviceName)
    if device is None:
        raise RuntimeError('Failed to find UART device!')

    logging.info('connecting to {0} [{1}]'.format(device.name, device.id))
    
    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    device.connect()
    try:
        # Wait for service discovery to complete for the UART service.  Will
        # time out after 60 seconds (specify timeout_sec parameter to override).
        UART.discover(device, timeout_sec=5)
        uart = UART(device)

        # Read temperature data from the sensor
        while True:
            received = uart.read(timeout_sec=5)
            if received is not None:
                logging.debug('received {0} bytes: {1}'.format(len(received), received))
                temp = parse_datapoint(received)
                if not temp:
                    continue
                # Log temperature data to file or stdout
                if logFile:
                    with open(logFile, 'w') as fp:
                        fp.write('{0}'.format(temp))
                else:
                    print(temp)

            else:
                # Timeout waiting for data, None is returned.
                break

    finally:
        # Make sure device is disconnected on exit.
        logging.info('disconnected from {0} [{1}]'.format(device.name, device.id))
        try:
            device.disconnect()
        except:
            pass


# Initialize the BLE system.  MUST be called before other BLE calls!
ble.initialize()

# Start the mainloop to process BLE events, and run the provided function in
# a background thread.  When the provided main function stops running, returns
# an integer status code, or throws an error the program will exit.
ble.run_mainloop_with(main)
