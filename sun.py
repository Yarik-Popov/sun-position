from __future__ import annotations
import argparse
import json
import os
import struct
import sys
from requests import Response
import requests


# Script constants
SUPPORTED_VERSION = '1.2'
ALWAYS_PRINT = 0  # Prints the required output
ON_WRITE_PRINT = 1  # Prints helpful output
VERBOSE_PRINT = 2  # Prints everything
DATA_FLOAT = 'f'
DATA_DOUBLE = 'd'
DEFAULT_STEP_SIZE = '1m'
DEFAULT_TARGET = 'sun'
DEFAULT_FILE_OUTPUT = 'output.bin'
DEFAULT_EXCLUDE = 'last'

type_print = ON_WRITE_PRINT


def define_parser() -> argparse.ArgumentParser:
    """
    Defines the parser for the script
    :return: The parser
    """
    parser = argparse.ArgumentParser(description='Position Ephemeris Retriever')
    parser.add_argument('start_time', type=str, help='Start time in the format YYYY-MM-DD or JD')
    parser.add_argument('stop_time', type=str, help='Stop time in the format YYYY-MM-DD or JD')
    parser.add_argument('-s', '--step-size', type=str, default=DEFAULT_STEP_SIZE,
                        help=f'Step size in the same format as the horizontal API (e.g. 1m, 1h, 1d, 1y, JD100). '
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
    # Change to store_false if you want to override the output file by default
    parser.add_argument('-w', '--write', action='store_true', help='Overrides the output file')
    parser.add_argument('-e', '--exclude', choices=['first', 'last', 'both', 'none'], default=DEFAULT_EXCLUDE,
                        help=f'Exclude the first, last, both or none of the values from the output file. '
                             f'Default: {DEFAULT_EXCLUDE}')

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


def write_data(data: str, is_double: bool, file_output: str):
    """
    Write the parameter data to the output.bin file and check if the written data is within the error bounds

    :param file_output: The output file
    :param data: Data to be read and written check
    :param is_double: If True then the data is written as a double precision (8 bytes)
    otherwise it is written as a float
    """
    expected_data = float(data)

    # Appends the data to the file and prints the expected data written if applicable
    with open(file_output, 'ab') as file:
        print_output_if_required(f'\tData written: {expected_data}', output_type=VERBOSE_PRINT)
        if is_double:
            b = struct.pack(DATA_DOUBLE, expected_data)
        else:
            b = struct.pack(DATA_FLOAT, expected_data)
        byte: bytearray = bytearray(b)
        file.write(byte)


def check_version(data: dict):
    """
    Prints out a warning if the version is difference from the supported one
    :param data: response.txt
    """
    if (data.get('signature')).get('version') != SUPPORTED_VERSION:
        print_output_if_required('WARNING: UNSUPPORTED HORIZON API VERSION USED')


def validate_response(response: Response):
    """
    Validates the responses. It handles the 400 status error code specifically. It also makes sure that the status code
    is always 200 for the rest of the script

    :param response: The response object
    """
    if response.status_code == 400:
        data = json.loads(response.text)
        if "message" in data:
            print_output_if_required(f"Message: {data['message']}")
        else:
            print_output_if_required(json.dumps(data, indent=2))
        sys.exit(1)
    if response.status_code != 200:
        print_output_if_required(f'{response.status_code = }')
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


def main():
    # TODO: Add argument parsing
    # Submit the API request and decode the JSON-response:
    args = define_parser().parse_args()
    url = f'https://ssd.jpl.nasa.gov/api/horizons.api?format=json&MAKE_EPHEM=YES&EPHEM_TYPE=VECTORS&COMMAND=' \
          f'{args.target}&OBJ_DATA=NO&STEP_SIZE={args.step_size}&START_TIME={args.start_time}&STOP_TIME=' \
          f'{args.stop_time}&CSV_FORMAT=YES&CAL_FORMAT=JD&VEC_TABLE=1'

    response = requests.get(url)
    validate_response(response)

    try:
        data = json.loads(response.text)
        print(data)
    except ValueError:
        print("Unable to decode JSON results")
        raise ValueError

    lines = data.get('result').split('\n')
    check_version(data)
    start = False
    count = 0
    total_count = 0
    lines_written = 0
    print_header()

    # Find total number of lines to be written
    for i in lines:
        if i.startswith('$$SOE'):
            start = True
        if i.startswith('$$EOE'):
            start = False
        if start and not i.startswith('$$SOE'):
            total_count += 1

    # Overwrite the output file if it exists
    if args.write and os.path.exists(args.output):
        os.remove(args.output)

    # Loop over response
    for i in lines:
        if i.startswith('$$SOE'):
            start = True
        if i.startswith('$$EOE'):
            start = False
        if start and not i.startswith('$$SOE'):
            if not ((count == 0 and (args.exclude == 'both' or args.exclude == 'first'))
                    or (count == total_count - 1) and (args.exclude == 'both' or args.exclude == 'last')):
                print_output_if_required(f'Line being parsed: {i}', output_type=VERBOSE_PRINT)
                output = (i[:-1].split(', '))
                output.pop(1)

                print_output_if_required(f'Output written: ', *output, output_type=ON_WRITE_PRINT)
                for j in output:
                    write_data(j, args.double, args.output)
                lines_written += 1
            count += 1

    print_header(True)
    print_output_if_required(f'Lines written: {lines_written}')


if __name__ == '__main__':
    main()
