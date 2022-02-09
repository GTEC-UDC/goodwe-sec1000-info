# goodwe-sec1000-info

This repository contains the executable python module `goodwe_sec1000_info` and the script `goodwe_sec1000_info_test.py`.

The module `goodwe_sec1000_info` allows to obtain the data of the inverters power and the mains power from the GoodWe SEC1000 Smart Energy Controller device. In particular, the data is obtained from the EzLogger device inside the SEC1000.

## Usage 

In the module `goodwe_sec1000_info`, inside the `__main` function, set the variables `host` and `port` to the address and port of your GoodWe SEC1000 device. Usually the port is 1234, unless you are accessing through some gateway with port forwarding.

Then, the module can be executed directly to obtain the SEC1000 data in JSON format. For example, the output may be:

```json
{
    "v1": 239.3,
    "v2": 238.10000000000002,
    "v3": 238.4,
    "i1": 21.62,
    "i2": 27.5,
    "i3": 24.240000000000002,
    "p1": -5.113,
    "p2": -6.412,
    "p3": -5.785,
    "meters_power": -17.311,
    "inverters_power": 0.0
}
```

## SEC1000 application protocol

The information about the application protocol used to query the SEC1000 data is not public. The only way of querying the data provided by the GoodWe company is to use its proprietary *ProMate* application.

Using Wireshark, we analyzed the packets exchanged between the *ProMate* application and the SEC1000 device and saw that a simple binary protocol is used. The script `sec1000_info_test.py` can be executed to print an analysis of the fields of the data received. An example of the output of this script is the following:

```
Total number of bytes received: 56

Bytes:
b'\x04REVO\x001\x01\x01\x0b\x00\x00\tV\x00\x00\tI\x00\x00\tM\x00\x00\x08p\x00\x00\n\xa6\x00\x00\t}\xff\xff\xec\x12\xff\xff\xe72\xff\xff\xe9d\xff\xff\xbc\xa7\x00\x00\x00\x00\x0f\x81'

Fields:
045245564F00     Header: \x04REV0\x00
31               Data lenght: 49
01010B           Unknown (request code?)
00000956         Voltage 1 (0.1V units): 2390
00000949         Voltage 2 (0.1V units): 2377
0000094D         Voltage 3 (0.1V units): 2381
00000870         Current 1 (0.01A units): 2160
00000AA6         Current 2 (0.01A units): 2726
0000097D         Current 3 (0.01A units): 2429
FFFFEC12         Power 1 (0.001W units): -5102
FFFFE732         Power 2 (0.001W units): -6350
FFFFE964         Power 3 (0.001W units): -5788
FFFFBCA7         Meter power (0.001W units): -17241
00000000         Inverters power (0.001W units): 0
0F81             Data checksum, calculated = F81
```

## SEC1000 problems

We found two problems when querying the data of the SEC1000. These also happen with the *ProMate* application, so it is something related to the SEC1000 and not to the way we are querying the data. These problems are:

- Sometimes the SEC1000 response is not correct. The expected response size (i.e., the size field in the response message from the SEC1000) should be 49, but sometimes is 6. To solve this we retry the query until we obtain a correct response.

- Sometimes the "inverters power" field has unexpectedly a value of 0. We have checked that the SEC1000 updates the "inverters power" value in intervals of approximately 30 seconds, but sometimes it sets this value to 0. This seems to be some problem within the SEC1000, since if the "inverters power" is 0, we would also expect the "meter power" (i.e., the power from the mains power grid) to increase accordingly, but this does not happen. To solve this we use a cache file to store a queue of some given size of the previous received values of "inverters power", then if we receive a "inverters power" of 0 we return the last non-zero value from the cache, or a 0 if there are no non-zero values in the cache.

## License

This code is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
