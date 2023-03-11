from __future__ import annotations
import argparse
import json
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

# Script variables used to
start_time = '2030-01-01'
stop_time = '2030-01-02'
ephem_type = 'APPROACH'
output_format = 'json'
target = 'sun'
step_size = '1m'
url = f'https://ssd.jpl.nasa.gov/api/horizons.api?format={output_format}&MAKE_EPHEM=YES&EPHEM_TYPE=VECTORS&COMMAND=' \
      f'{target}&OBJ_DATA=NO&STEP_SIZE={step_size}&START_TIME={start_time}&STOP_TIME={stop_time}&CSV_FORMAT=YES&' \
      f'CAL_FORMAT=JD&VEC_TABLE=1'
file_output = 'output.bin'
type_print = ON_WRITE_PRINT


def define_parser() -> argparse.ArgumentParser:
    """
    Defines the parser for the script
    :return: The parser
    """

    parser = argparse.ArgumentParser(description='Sun position calculator')
    parser.add_argument('start-time', type=str, help='Start time in the format YYYY-MM-DD')
    parser.add_argument('stop-time', type=str, help='Stop time in the format YYYY-MM-DD')
    parser.add_argument('-s', '--step-size', type=str, default=DEFAULT_STEP_SIZE)
    parser.add_argument('-t', '--target', type=str, default=DEFAULT_TARGET)
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_FILE_OUTPUT)
    parser.add_argument('-d', '--double', action='store_true', default=False)
    parser.add_argument('-p', '--print', type=int, choices=range(3), default=ALWAYS_PRINT)

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


def write_data(data: str, type_data: str):
    """
    Write the parameter data to the output.bin file and check if the written data is within the error bounds

    :param type_data: The type of data to be written ('d' or 'f')
    :param data: Data to be read and written check
    :return: None or ValueError is raised
    """
    assert type_data == DATA_DOUBLE or type_data == DATA_FLOAT, "Incorrect type"
    expected_data = float(data)

    # Appends the data to the file and prints the expected data written if applicable
    with open(file_output, "ab") as file:
        print_output_if_required(f'\tData written: {expected_data}', output_type=VERBOSE_PRINT)
        b = struct.pack(type_data, expected_data)
        byte = bytearray(b)
        file.write(byte)


def check_version(data: dict):
    """
    Prints out a warning if the version is difference from the supported one
    :param data: response.txt
    """
    if (data.get('signature')).get('version') != SUPPORTED_VERSION:
        print_output_if_required('WARNING: UNSUPPORTED HORIZON API VERSION USED')
        input('Press enter to continue: ')


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
        print_output_if_required('\t' * 4, 'JD:', '\t' * 4, 'X:', '\t' * 5, 'Y:', '\t' * 4, 'Z:',
                                 output_type=ON_WRITE_PRINT)
        print_output_if_required('-' * 130, output_type=ON_WRITE_PRINT)
    else:
        print_output_if_required('\t' * 4, 'JD:', '\t' * 4, 'X:', '\t' * 5, 'Y:', '\t' * 4, 'Z:',
                                 output_type=ON_WRITE_PRINT)
        print_output_if_required('-' * 130, output_type=ON_WRITE_PRINT)


def main():
    # TODO: Add argument parsing
    # Submit the API request and decode the JSON-response:
    type_data = 'f'
    response = requests.get(url)
    validate_response(response)

    try:
        data = json.loads(response.text)
    except ValueError:
        print("Unable to decode JSON results")
        raise ValueError

    lines = data.get('result').split('\n')
    check_version(data)
    start = False
    count = 0
    print_header()

    # Loop over response
    for i in lines:
        if i.startswith('$$SOE'):
            start = True
        if i.startswith('$$EOE'):
            start = False
        if start and not i.startswith('$$SOE'):
            print_output_if_required(f'Line being parsed: {i}', output_type=VERBOSE_PRINT)
            output = (i[:-1].split(', '))
            output.pop(1)

            print_output_if_required(f'Output written: ', *output, output_type=ON_WRITE_PRINT)
            for j in output:
                write_data(j, type_data)
            count += 1

    print_header(True)
    print_output_if_required(f'Lines written: {count}')


def test():
    args = define_parser().parse_args()
    print(args)


if __name__ == '__main__':
    main()
    # test()
