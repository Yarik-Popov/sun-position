import sun
from sun import DataPoint
from typing import List, BinaryIO
import struct


def read_header(file_input: str) -> List:
    """
    Tests the header file to ensure that the data was read correctly

    :param file_input:
    """
    with open(file_input, "rb") as file:
        file.seek(0)
        output = [file.read(1)]
        for _ in range(sun.NUMBER_OF_HEADER_LINES):
            byte_str = file.read(8)
            float_val = struct.unpack(sun.DATA_DOUBLE, byte_str)[0]
            output.append(float_val)
    return output


def get_single_data_point(file: BinaryIO, read_type: str) -> float:
    """
    Tests the output file to ensure that the data was written correctly

    :param file:
    :param read_type:
    """
    if read_type == b'1':
        read_type = sun.DATA_DOUBLE
        read_size = 8
        print("double")
    else:
        read_type = sun.DATA_FLOAT
        read_size = 4
        print("float")

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
    rt = header[0]

    with open(file_output, "rb") as file:
        file.seek(sun.SIZE_OF_HEADER)

        for i in range(int(header[3])):
            data_point = DataPoint(get_single_data_point(file, rt), get_single_data_point(file, rt),
                                   get_single_data_point(file, rt), get_single_data_point(file, rt))
            output.append(data_point)

    return output


def main():
    expected = sun.main('2020-01-01 2020-01-02 -s 5m')
    actual = read_file('output.bin')
    assert len(expected) == len(actual)
    assert expected == actual
    print(expected)
    print()
    print(actual)


if __name__ == '__main__':
    main()
