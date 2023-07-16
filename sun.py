from __future__ import annotations
import argparse
import json
import struct
import sys
from requests import Response
import requests
import logging
import re
from typing import Final
from typing import List
from dataclasses import dataclass
from math import isclose

# Script constants
SUPPORTED_VERSION: Final[str] = '1.2'
NUMBER_OF_HEADER_LINES: Final[int] = 3
ALWAYS_PRINT = 0  # Prints the required output
ON_WRITE_PRINT = 1  # Prints helpful output
VERBOSE_PRINT = 2  # Prints everything
DATA_FLOAT = 'f'
DATA_DOUBLE = 'd'
DEFAULT_STEP_SIZE: Final[str] = '1m'
DEFAULT_TARGET: Final[str] = 'sun'
DEFAULT_FILE_OUTPUT: Final[str] = 'output.bin'
DEFAULT_EXCLUDE: Final[str] = 'last'
SIZE_OF_DOUBLE: Final[int] = 8
SIZE_OF_HEADER: Final[int] = 1 + SIZE_OF_DOUBLE * NUMBER_OF_HEADER_LINES
RELATIVE_TOLERANCE: Final[float] = 1e-7

# Global variable for the type of print (ALWAYS_PRINT, ON_WRITE_PRINT, VERBOSE_PRINT) set by the -p argument similar
# debug levels
type_print = ON_WRITE_PRINT


@dataclass
class DataPoint:
    """
    Data class to store the data points
    """
    jd: float
    x: float
    y: float
    z: float

    def __eq__(self, other):
        """
        Checks if the two data points are equal
        :param other: The other data point
        :return: True if the two data points are equal otherwise False
        """
        return isclose(self.jd, other.jd, rel_tol=RELATIVE_TOLERANCE) and \
               isclose(self.x, other.x, rel_tol=RELATIVE_TOLERANCE) and \
               isclose(self.y, other.y, rel_tol=RELATIVE_TOLERANCE) and \
               isclose(self.z, other.z, rel_tol=RELATIVE_TOLERANCE)


@dataclass
class Header:
    """
    Data class to store the header information
    """
    is_double: bool
    start_time: float
    step_size: float
    number_of_points: int


def is_float(num: str):
    """
    Checks if the parameter is a float
    :param num:
    :return: True if the parameter is a float otherwise False
    """
    try:
        float(num)
        return True
    except ValueError:
        return False


def is_valid_time(time: str):
    """
    Checks if the parameter is a valid time
    :param time:
    :return: True if the parameter is a valid time otherwise False
    """
    # Regex for time format
    time_regex = re.compile(r'^[1-9]\d{3}-\d{2}-\d{2}$')

    return time_regex.match(time) or (time.startswith('JD') and is_float(time[2:]))


def validate_input(args: argparse.Namespace):
    """
    Validates the input arguments created by the define_parser() function. If all the inputs are valid then it will
    do nothing otherwise it will exit the script
    :param args: The arguments created by the define_parser() function
    """

    # use the regex to check if the start time is in the correct format
    if not is_valid_time(args.start_time):
        logging.critical('Start time must be in the format YYYY-MM-DD or JD#')
        sys.exit(10)

    # Checks if the stop time is in the correct format
    if not is_valid_time(args.stop_time):
        logging.critical('Stop time must be in the format YYYY-MM-DD or JD#')
        sys.exit(11)

    # Checks if the step size is in the correct format
    if not args.step_size[-1] in ['y', 'm', 'd', 'h', 's'] and not args.step_size[:-1].isnumeric() \
            and not args.step_size.isnumeric():
        logging.critical('Step size must be in the format #y, #m, #d, #h, #s, or #. Where # is a integer')
        sys.exit(12)

    # Checks if the output file is in the correct format
    if not args.output.endswith('.bin'):
        logging.critical('Output file must be in the format *.bin')
        sys.exit(13)


def define_parser() -> argparse.ArgumentParser:
    """
    Defines the parser for the script
    :return: The parser
    """
    parser = argparse.ArgumentParser(description='Position Ephemeris Retriever')
    parser.add_argument('start_time', type=str, help='Start time in the format YYYY-MM-DD or JD#')
    parser.add_argument('stop_time', type=str, help='Stop time in the format YYYY-MM-DD or JD#')
    parser.add_argument('-s', '--step-size', type=str, default=DEFAULT_STEP_SIZE,
                        help=f'Step size in the same format as the horizontal API (e.g. 1m, 1h, 1d, 1y, 100). '
                             f'Default: {DEFAULT_STEP_SIZE}')
    parser.add_argument('-t', '--target', type=str, default=DEFAULT_TARGET,
                        help=f'Target object (e.g. sun, moon, mars). Default: {DEFAULT_TARGET}')
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_FILE_OUTPUT,
                        help=f'Output file name. Default: {DEFAULT_FILE_OUTPUT}')
    parser.add_argument('-d', '--double', action='store_true', default=False,
                        help='Use double precision (8 bytes). Default: False (4 bytes) or float')
    parser.add_argument('-p', '--print', type=int, choices=range(3), default=ALWAYS_PRINT,
                        help=f'Prints the output to the console. 0 = Always, 1 = On write, 2 = Verbose. '
                             f'Default: {ALWAYS_PRINT}')
    parser.add_argument('-e', '--exclude', choices=['first', 'last', 'both', 'none'], default=DEFAULT_EXCLUDE,
                        help=f'Exclude the first, last, both or none of the values from the output file. '
                             f'Default: {DEFAULT_EXCLUDE}')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Verbose output used for debugging purposes. Default: False')
    parser.add_argument('-l', '--log', type=str, default=None,
                        help='Log file for debugging purposes. Default: None')

    return parser


def print_output_if_required(*values, output_type=ALWAYS_PRINT, sep: str | None = None, end: str | None = None,
                             file=sys.stdout, flush=False):
    """
    Function to determine whether to print to the values based on the output_type and prints them if required

    :param values: The values to be printed
    :param output_type: The type of output used to determine when to print it
    :param sep: Seperator
    :param end: The end of a line
    :param file: File SupportsWrite[str] | None
    :param flush: Passed to print
    """
    if output_type == ALWAYS_PRINT or output_type <= type_print:
        print(*values, sep=sep, end=end, file=file, flush=flush)


def check_version(data: dict):
    """
    Prints out a warning if the version is difference from the supported one
    :param data: response.txt
    """
    if (data.get('signature')).get('version') != SUPPORTED_VERSION:
        logging.warning('WARNING: UNSUPPORTED HORIZON API VERSION USED')


def validate_response(response: Response):
    """
    Validates the responses. It handles the 400 status error code specifically. It also makes sure that the status code
    is always 200 for the rest of the script

    :param response: The response object
    """
    if response.status_code == 400:
        data = json.loads(response.text)
        if "message" in data:
            logging.critical(f"Message: {data['message']}")
        else:
            logging.critical(json.dumps(data, indent=2))
        sys.exit(1)

    if response.status_code != 200:
        logging.critical(f'{response.status_code = }')
        sys.exit(2)


def print_header(reverse=False):
    """
    Prints the header of the data printed

    :param reverse: If True then reverses the order of the header and prints and extra seperator line
    :return:
    """
    if reverse:
        print_output_if_required('-' * 130, output_type=ON_WRITE_PRINT)
        print_output_if_required('\t' * 3, 'JD:', '\t' * 4, 'X:', '\t' * 5, 'Y:', '\t' * 4, 'Z:',
                                 output_type=ON_WRITE_PRINT)
        print_output_if_required('-' * 130, output_type=ON_WRITE_PRINT)
    else:
        print_output_if_required('\t' * 3, 'JD:', '\t' * 4, 'X:', '\t' * 5, 'Y:', '\t' * 4, 'Z:',
                                 output_type=ON_WRITE_PRINT)
        print_output_if_required('-' * 130, output_type=ON_WRITE_PRINT)


def write_data(data: DataPoint, is_double: bool, file_output: str):
    """
    Write the parameter data to the output.bin file and check if the written data is within the error bounds

    :param file_output: The output file
    :param data: Data to be read and written check
    :param is_double: If True then the data is written as a double precision (8 bytes)
    otherwise it is written as a float
    """
    data_format = DATA_DOUBLE if is_double else DATA_FLOAT

    # Appends the data to the file and prints the expected data written if applicable
    with open(file_output, 'ab') as file:
        print_output_if_required(f'\tData written: {data}', output_type=VERBOSE_PRINT)

        # Write the JD value
        bjd = struct.pack(data_format, float(data.jd))
        file.write(bytearray(bjd))

        # Write the x value
        bx = struct.pack(data_format, data.x)
        file.write(bytearray(bx))

        # Write the y value
        by = struct.pack(data_format, data.y)
        file.write(bytearray(by))

        # Write the z value
        bz = struct.pack(data_format, data.z)
        file.write(bytearray(bz))


def write_header(file_output: str, min_jd: float, max_jd: float, count: float, is_double: bool, write_to_file=True):
    """
    Writes the header of the data to the output file

    :param is_double: If True then the data is written as a double precision (8 bytes) otherwise it is written as a
    float. Also writes the first byte of the file to indicate the precision. 0 = float, 1 = double
    :param count: The number of the data points
    :param max_jd: The maximum JD
    :param min_jd: The minimum JD
    :param file_output: The output file
    :param write_to_file: If True then the header is written to the file
    """
    if not write_to_file:
        return

    data = [min_jd, max_jd, count]

    with open(file_output, 'rb+') as file:
        print_output_if_required(f'Writing header to {file_output}', output_type=VERBOSE_PRINT)
        file.seek(0)
        if is_double:
            file.write(b'1')
        else:
            file.write(b'0')

        for i in data:
            print_output_if_required(f'\tData written: {i}', output_type=VERBOSE_PRINT)
            b = struct.pack(DATA_DOUBLE, i)
            byte: bytearray = bytearray(b)
            file.write(byte)


def find_number_of_data_points(lines: List[str]) -> int:
    """
    Finds the number of data points in the data

    :param lines: The lines of the data
    :return: The number of data points
    """
    total_count = 0
    start = False
    for i in lines:
        if i.startswith('$$SOE'):
            start = True
        if i.startswith('$$EOE'):
            start = False
        if start and not i.startswith('$$SOE'):
            total_count += 1

    return total_count


def allocate_header(write_to_file: bool, file_output: str):
    """
    Overwrites the output file and allocates the space for the header

    :param write_to_file: If True then the header is written to the file
    :param file_output: The output file
    """
    if not write_to_file:
        return

    with open(file_output, 'wb') as file:
        file.write(bytes(SIZE_OF_HEADER))


def calculate_step_size(min_jd: float, max_jd: float, number_of_data_points: int) -> float:
    """
    Calculates the step size of the data

    :param min_jd: The minimum JD
    :param max_jd: The maximum JD
    :param number_of_data_points: The number of data points
    :return: The step size
    """
    if max_jd < min_jd:
        raise ValueError('The maximum JD is less than the minimum JD')

    if min_jd == max_jd and number_of_data_points > 1:
        raise ValueError('The minimum JD is equal to the maximum JD but there is more than one data point')

    if number_of_data_points < 1:
        raise ValueError('The number of data points is less than 1')

    if number_of_data_points == 1:
        return 0

    return (max_jd - min_jd) / (number_of_data_points - 1)


def main(argsv: str | None = None, *, write_to_file=True) -> List[DataPoint]:
    # Parse the arguments and set logging
    if isinstance(argsv, str):
        args = define_parser().parse_args(argsv.split())
    else:
        args = define_parser().parse_args()
    validate_input(args)
    global type_print  # This is not good practice, but it is the easiest way to do it
    type_print = args.print
    logging.basicConfig(filename=args.log, level=logging.DEBUG if args.verbose else logging.INFO, encoding='utf-8')

    # Get the data from the API
    url = f'https://ssd.jpl.nasa.gov/api/horizons.api?format=json&MAKE_EPHEM=YES&EPHEM_TYPE=VECTORS&COMMAND=' \
          f'{args.target}&OBJ_DATA=NO&STEP_SIZE={args.step_size}&START_TIME={args.start_time}&STOP_TIME=' \
          f'{args.stop_time}&CSV_FORMAT=YES&CAL_FORMAT=JD&VEC_TABLE=1'
    response = requests.get(url)
    validate_response(response)

    try:
        data = json.loads(response.text)
    except ValueError:
        logging.critical('Invalid JSON response')
        raise ValueError

    check_version(data)
    lines = data.get('result').split('\n')

    # Find total number of lines to be written
    total_count = find_number_of_data_points(lines)

    # Overwrite the output file and allocates the space for the header
    allocate_header(write_to_file, args.output)

    start = False
    count = 0
    lines_written = 0
    min_jd = 0
    max_jd = 0
    data_points = []
    print_header()

    # Loop over response
    for i in lines:
        if i.startswith('$$SOE'):
            start = True
        if i.startswith('$$EOE'):
            start = False
        # If the line is not the start or end of the data then it is a line of data
        if start and not i.startswith('$$SOE'):
            if not ((count == 0 and (args.exclude == 'both' or args.exclude == 'first'))
                    or (count == total_count - 1) and (args.exclude == 'both' or args.exclude == 'last')):
                print_output_if_required(f'Line being parsed: {i}', output_type=VERBOSE_PRINT)
                output = (i[:-1].split(', '))
                output.pop(1)

                jd = float(output[0])
                if min_jd == 0:
                    min_jd = jd
                output[0] = (jd - min_jd)
                max_jd = jd

                print_output_if_required(f'Output written: ', *output, output_type=ON_WRITE_PRINT)
                data_point = DataPoint(output[0], float(output[1]), float(output[2]), float(output[3]))
                data_points.append(data_point)
                write_data(data_point, args.double, args.output)
                lines_written += 1
            count += 1

    write_header(args.output, min_jd, max_jd, lines_written, args.double)
    print_header(True)
    print_output_if_required(f'Lines written: {lines_written}')

    return data_points


if __name__ == '__main__':
    main('2020-01-01 2020-01-03 -p 2')
