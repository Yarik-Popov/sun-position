# Sun Position 

Script for parsing data from the NASA Horizon API used by ADCS for onboard algorithms

## Requirements:
Check the requirements.txt file for the latest version of the requirements (pip install -r requirements.txt)
- Python
- Requests (pip install requests)
- PyTest (pip install pytest)

## Usage:
usage: sun.py [-h] [-s STEP_SIZE] [-t TARGET] [-o OUTPUT] [-d] [-p {0,1,2}] [-e {first,last,both,none}] [-v] [-l LOG] start_time stop_time

Position Ephemeris Retriever

positional arguments:
-  start_time            Start time in the format YYYY-MM-DD or JD#
-  stop_time             Stop time in the format YYYY-MM-DD or JD#

options:
-  -h, --help           <br>
show this help message and exit
-  -s STEP_SIZE, --step-size STEP_SIZE <br>
                        Step size in the same format as the horizontal API (e.g. 1m, 1h, 1d, 1y, 100). Default: 1m
-  -t TARGET, --target TARGET <br>
                        Target object (e.g. sun, moon, mars). Default: sun
-  -o OUTPUT, --output OUTPUT <br>
                        Output file name. Default: output.bin
-  -d, --double       <br>
Use double precision (8 bytes). Default: False (4 bytes) or float
-  -p {0,1,2}, --print {0,1,2} <br>
                        Prints the output to the console. 0 = Always, 1 = On write, 2 = Verbose. Default: 0
-  -e {first,last,both,none}, --exclude {first,last,both,none} <br>
                        Exclude the first, last, both or none of the values from the output file. Default: last
-  -v, --verbose        <br> Verbose output used for debugging purposes. Default: False (UNUSED)
-  -l LOG, --log LOG      <br>Log file for debugging purposes. Default: None (UNUSED)

## Contents of the output file:
### Header:
- 1 byte: 0x00 or 0x01 (0x00 = single precision or 4 bytes, 0x01 = double precision or 8 bytes) (DEPRECATED)
- 8 bytes: Start time in JD (min_jd)
- 8 bytes: Step size of data points (step_size) (NEED TO ADD)
- 8 bytes: Number of data points (n)

### Data: n data points of a total of 16 or 32 (depending on the precision) bytes per data point
- precision bytes: JD - min_jd (DEPRECATED - WILL BE CALCULATED VALUE BASED ON STEP SIZE AND START TIME)
- precision bytes: x
- precision bytes: y
- precision bytes: z
