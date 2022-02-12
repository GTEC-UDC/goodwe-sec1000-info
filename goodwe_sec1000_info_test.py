import goodwe_sec1000_info
import logging
import struct
import sys
import time


def hex2str(data):
    try:
        return ''.join('{:02X}'.format(a) for a in data)
    except TypeError:
        return '{:02X}'.format(data)


def print_response(data):
    print("Total number of bytes received:", len(data))
    print()
    print("Bytes:")
    print(repr(data))
    print()
    # print("Bytes (hex):")
    # print(textwrap.fill(hexstr(data), width=8))
    # print()

    print("Fields:")
    print(hex2str(data[0x00:0x06]), "\t Header: \\x04REV0\\x00")
    print(hex2str(data[0x06]), "\t\t Data lenght:", data[0x06])
    print(hex2str(data[0x07:0x0A]), "\t\t Unknown (request code?)")

    print(hex2str(data[0x0A:0x0E]), "\t Voltage 1 (0.1V units):",
          struct.unpack(">i", data[0x0A:0x0E])[0])
    print(hex2str(data[0x0E:0x12]), "\t Voltage 2 (0.1V units):",
          struct.unpack(">i", data[0x0E:0x12])[0])
    print(hex2str(data[0x12:0x16]), "\t Voltage 3 (0.1V units):",
          struct.unpack(">i", data[0x12:0x16])[0])

    print(hex2str(data[0x16:0x1A]), "\t Current 1 (0.01A units):",
          struct.unpack(">i", data[0x16:0x1A])[0])
    print(hex2str(data[0x1A:0x1E]), "\t Current 2 (0.01A units):",
          struct.unpack(">i", data[0x1A:0x1E])[0])
    print(hex2str(data[0x1E:0x22]), "\t Current 3 (0.01A units):",
          struct.unpack(">i", data[0x1E:0x22])[0])

    print(hex2str(data[0x22:0x26]), "\t Power 1 (1W units):",
          struct.unpack(">i", data[0x22:0x26])[0])
    print(hex2str(data[0x26:0x2A]), "\t Power 2 (1W units):",
          struct.unpack(">i", data[0x26:0x2A])[0])
    print(hex2str(data[0x2A:0x2E]), "\t Power 3 (1W units):",
          struct.unpack(">i", data[0x2A:0x2E])[0])

    print(hex2str(data[0x2E:0x32]), "\t Meter power (1W units):",
          struct.unpack(">i", data[0x2E:0x32])[0])
    print(hex2str(data[0x32:0x36]), "\t Inverters power (1W units):",
          struct.unpack(">i", data[0x32:0x36])[0])

    print(hex2str(data[0x36:0x38]), "\t\t Data checksum, calculated =",
          hex2str(sum(data[0x07:0x36])))


# host = '10.18.24.62'
# port = 1234
host = '127.0.0.1'
port = 8888

num_retries = 10
wait_retry = 5

for i in range(1, num_retries + 1):
    try:
        data = goodwe_sec1000_info.ezlogger_raw_request(host, port)
        print_response(data)
        sys.exit(0)
    except Exception as e:
        logging.error(e)
        time.sleep(wait_retry)

sys.exit(1)
