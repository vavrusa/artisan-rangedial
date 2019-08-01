# Range Dial adapter for Artisan

This is an adapter for reading the [Range Dial](https://store.supermechanical.com/products/range-dial) probe directly.
Range Dial probes do not have the circuitry to work with the microphone port anymore, hence this workaround.
The adapter consists of two parts:
* `server.py` - a server that connects to the Dial over BLE and writes out temperature reading to a local file.
* `reader.py` - a reader that read the local file with temp reading and prints them in a format suitable for artisan (you can also do just `cat <tempfile>`)

## Installation

This only works on Mac as the BLE library only works on Mac.

```bash
$ pip install pyobjc Adafruit_BluefruitLE
```

## How do you use it with Artisan?

First start the server and wait for the device to connect:

```bash
$ ./server.py RangeWhite24 /tmp/artisan.log
INFO:root:searching for UART device RangeWhite24
INFO:root:connecting to RangeWhite24 [2d188e3c-a4cb-4a8b-9f86-bc4f813dc7fb]
```

The `RangeWhite24` is the name of the BLE device (it can change) and `/tmp/artisan.log` is the file for temp readings. You can now print the current temperature in F:

```bash
$ cat /tmp/artisan.log
69.782
```

In Artisan go to `Config > Device`, select `Prog`, and put in `cat /tmp/artisan.log`. Artisan should now take temperature readings from the file.
Don't forget to start the `server.py` before roasting. The server stops automatically when you disconnect the probe from Dial.

## Range Dial UART Protocol
The Dial protocol isn't documented, but it's fairly easy to understand:

```
# The Range sends three types of messages.
# First byte defines the message types:
#  * 'D' is initialization message
#  * 'V' is some kind of control device followed by 2 bytes
#  * 'T' is temperature data followed by 4 bytes
# The Range dial has two ports for temperature sensors, upper and lower.
#  * When the upper port is used, the first two bytes will be set to '\x81\x0c'.
#  * When the lower port is used, the last two bytes will be set to '\x81\x0c'.
# The temperature is a fixed-point number in celsius, e.g. 2868 equals to 28.68 degrees C
```