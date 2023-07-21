import os.path
from sun import ephemeris
from sun.ephemeris import DataPoint
from sun.ephemeris import Header
from typing import List, BinaryIO
import struct


def read_header(file_input: str) -> Header:
    """
    Tests the header file to ensure that the data was read correctly

    :param file_input:
    """
    with open(file_input, "rb") as file:
        file.seek(0)
        start_time = get_single_data_point(file, False)
        step_size = get_single_data_point(file, False)
        num_data_points = int(get_single_data_point(file, False))
        print(start_time)
        print(step_size)
        print(num_data_points)
        return Header(start_time, step_size, num_data_points)


def get_single_data_point(file: BinaryIO, is_float=True) -> float:
    """
    Tests the output file to ensure that the data was written correctly

    :param is_float: If true, then will parse as float, otherwise will parse as double
    :param file: The file to read from
    """
    if is_float:
        read_type = ephemeris.DATA_FLOAT
        read_size = 4
    else:
        read_type = ephemeris.DATA_DOUBLE
        read_size = 8

    byte_str = file.read(read_size)
    float_val = struct.unpack(read_type, byte_str)[0]
    return float(float_val)


def read_file(file_output: str) -> List[DataPoint]:
    """
    Tests the output file to ensure that the data was written correctly

    :param file_output:
    """
    output = []
    header = read_header(file_output)

    with open(file_output, "rb") as file:
        file.seek(ephemeris.SIZE_OF_HEADER)

        for i in range(header.num_data_points):
            jd = header.start_time + (i * header.step_size)
            data_point = DataPoint(jd, get_single_data_point(file),
                                   get_single_data_point(file), get_single_data_point(file))
            output.append(data_point)

    return output


def main():
    file = os.path.join('..', 'test_sun', 'test1.bin')
    expected = ephemeris.main(f'2020-01-01 2020-01-02 -s 5m -o {file}')
    actual = read_file('test1.bin')
    print(f'{len(expected) = }')
    print(f'{len(actual) = }')
    print(expected)
    assert len(expected) == len(actual)
    for i in range(len(expected)):
        print(f'{expected[i] = }')
        print(f'{actual[i] = }')
    assert expected == actual
    print()
    print(actual)


if __name__ == '__main__':
    main()
