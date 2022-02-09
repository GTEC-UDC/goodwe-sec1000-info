import dataclasses
import json
import logging
import pathlib
import shelve
import socket
import struct
import sys
import time


# global logger object
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class EzloggerData:
    v1: float
    v2: float
    v3: float
    i1: float
    i2: float
    i3: float
    p1: float
    p2: float
    p3: float
    meters_power: float
    inverters_power: float


def ezlogger_raw_request(host: str, port: int = 1234, timeout: float = 10) -> bytes:
    request_msg = b'\x00\x05\x01\x01\x0b\x00\x0d'

    # make request
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(request_msg)

        # receive first 7 bytes (header and response size)
        data = b''
        while len(data) < 7:
            recv_data = s.recv(7 - len(data))
            data += recv_data
            if len(recv_data) == 0:
                raise Exception("Bad response: no data received.")

        # get response size
        response_size = data[6]

        # the expected response size is 49, if not something went wrong
        if response_size != 49:
            raise Exception("Bad response: expected size was 49, but is {}.".
                            format(response_size))

        # receive the rest of the response data
        data += s.recv(response_size)
        return data


def ezlogger_request(host: str, port: int = 1234, timeout: float = 10) -> EzloggerData:
    data = ezlogger_raw_request(host, port, timeout)

    # decode the received data
    v1 = 0.1 * struct.unpack(">i", data[0xA:0xE])[0]
    v2 = 0.1 * struct.unpack(">i", data[0xE:0x12])[0]
    v3 = 0.1 * struct.unpack(">i", data[0x12:0x16])[0]

    i1 = 1e-2 * struct.unpack(">i", data[0x16:0x1A])[0]
    i2 = 1e-2 * struct.unpack(">i", data[0x1A:0x1E])[0]
    i3 = 1e-2 * struct.unpack(">i", data[0x1E:0x22])[0]

    p1 = 1e-3 * struct.unpack(">i", data[0x22:0x26])[0]
    p2 = 1e-3 * struct.unpack(">i", data[0x26:0x2A])[0]
    p3 = 1e-3 * struct.unpack(">i", data[0x2A:0x2E])[0]

    meter_power = 1e-3 * struct.unpack(">i", data[0x2E:0x32])[0]
    inverters_power = 1e-3 * struct.unpack(">i", data[0x32:0x36])[0]

    return EzloggerData(v1, v2, v3, i1, i2, i3, p1, p2, p3,
                        meter_power, inverters_power)


def fix_data(data, cache_path="ezlogger_cache",
             cache_max_items=10, cache_max_age=None):
    # If the received inverters_power field is 0 then we replace it
    # with the last non 0 value in the cache and update the cache.

    with shelve.open(str(cache_path)) as db:
        # get data from the cache
        inverters_power_list = db.get('inverters_power_list', [])
        cache_time = db.get('cache_time', None)

        # if the cache has exceeded the maximum age then reinitialize
        # inverters_power_list to an empty list
        if cache_max_age is not None and cache_time is not None and \
                (cache_age := time.time() - cache_time) > cache_max_age:
            logger.info("Reinitializing cache: cache age is {:.02f}, but the "
                        "maximum set age is {:.02f}.".
                        format(cache_age, cache_max_age))
            inverters_power_list = []

        # Update data.inverters_power to last non 0 value from the cache
        inverters_power = data.inverters_power
        if len(inverters_power_list) != 0 and inverters_power == 0.0:
            try:
                data.inverters_power = next(filter(lambda x: x != 0,
                                            reversed(inverters_power_list)))
                logger.info("Possible bad inverted_powers value: a 0 was "
                            "received, replaced by {:0.3f} from the cache.".
                            format(data.inverters_power))
            except StopIteration:
                pass

        # update cache
        inverters_power_list.append(inverters_power)
        inverters_power_list = inverters_power_list[-cache_max_items:]
        db['inverters_power_list'] = inverters_power_list
        db['cache_time'] = time.time()


def __main():
    # sometimes the returned inverters_power field is 0 unexpectedly. We use a
    # cache file to store past results and if a 0 is returned then we replace
    # inverters_power with the last non 0 value stored in the cache.
    script_path = pathlib.Path(__file__).parent.absolute()
    ezlogger_cache_path = script_path / "ezlogger_cache"
    ezlogger_cache_max_items = 10  # 0 or None to disable the cache
    ezlogger_cache_max_age = 1200  # max age of the cache in seconds

    # host = '10.18.24.62'
    # port = 1234
    host = '127.0.0.1'
    port = 8888

    # we consider several retries since the request sometimes may fail
    num_retries = 10
    wait_retry = 5

    for i in range(1, num_retries + 1):
        try:
            # request data to the ezlogger device
            data = ezlogger_request(host, port)

            if ezlogger_cache_max_items is not None and ezlogger_cache_max_items > 0:
                fix_data(data, ezlogger_cache_path, ezlogger_cache_max_items,
                         ezlogger_cache_max_age)

            # print data
            print(json.dumps(dataclasses.asdict(data), indent=4))

            # test
            # print(datetime.datetime.now().isoformat() + "," +
            #       "{:.03f}".format(data.meters_power) + "," +
            #       "{:.03f}".format(data.inverters_power))
            sys.exit(0)
        except Exception as e:
            logger.info(e)
            time.sleep(wait_retry)

    logger.error("No correct response was received")
    sys.exit(1)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.WARNING)
        __main()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
