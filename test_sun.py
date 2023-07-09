import sun
from sun import DataPoint
from typing import List
import struct


def read_header(file_input: str) -> List:
    """
    Tests the header file to ensure that the data was read correctly

    :param file_input:
    """
    with open(file_input, "rb") as file:
        file.seek(0)
        output = [file.read(1)]
        for _ in sun.HEADER_LINES:
            byte_str = file.read(8)
            float_val = struct.unpack(sun.DATA_DOUBLE, byte_str)[0]
            output.append(float_val)
    return output


def read_file(file_output: str) -> List[DataPoint]:
    """
    Tests the output file to ensure that the data was written correctly

    :param lines_written:
    :param double:
    :param file_output:
    """
    output = []
    header = read_header(file_output)

    if header[0]:
        read_type = sun.DATA_DOUBLE
        read_size = 8
    else:
        read_type = sun.DATA_FLOAT
        read_size = 4

    with open(file_output, "rb") as file:
        file.seek(0)
        val = file.read(1)
        print(val)
        for i in range(sun.NUMBER_OF_HEADER_LINES):
            byte_str = file.read(8)
            float_val = struct.unpack(sun.DATA_DOUBLE, byte_str)[0]
            print(float_val)

        print()

        for i in range(header[3] * 4):
            byte_str = file.read(read_size)
            float_val = struct.unpack(read_type, byte_str)[0]
            print(float_val)
            if i % 4 == 3:
                print()
    return output


def test_is_float0():
    assert sun.is_float(1.0)


def test_is_float1():
    assert sun.is_float(1) 


def test_is_float2():
    assert sun.is_float("1.0")


def test_is_float3():
    assert sun.is_float("1")


def test_is_float4():
    assert not sun.is_float("a")


def test_is_float5():
    assert not sun.is_float("1a")


def test_is_float6():
    assert not sun.is_float("a1")


def test_is_float7():
    assert not sun.is_float("1.0a")


def test_is_float8():
    assert not sun.is_float("a1.0")


def test_is_float9():
    assert not sun.is_float("1.a0")


def test_is_valid_time0():
    assert sun.is_valid_time("JD2451545.0")


def test_is_valid_time1():
    assert sun.is_valid_time("JD2451545")


def test_is_valid_time2():
    assert sun.is_valid_time("2020-01-02")


def test_is_valid_time3():
    assert not sun.is_valid_time("2020-01-02 12:00:00")


def main():
    pass


if __name__ == "__main__":
    main()
