import json
# Requests needs to be installed
import requests

# Define API URL and SPK filename:

# Define the time span:
start_time = '2030-01-01'
stop_time = '2030-01-02'
ephem_type = 'APPROACH'
output_format = 'json'

url = f'https://ssd.jpl.nasa.gov/api/horizons.api?format={output_format}&MAKE_EPHEM=YES&EPHEM_TYPE=VECTORS&COMMAND=' \
      f'sun&OBJ_DATA=NO&STEP_SIZE=1m&START_TIME=JD2451545&STOP_TIME=JD2451545.1&CSV_FORMAT=YES&CAL_FORMAT=JD&VEC_TABLE=1'

# Submit the API request and decode the JSON-response:
response = requests.get(url)
lines = ''
data = {}

try:
    data = json.loads(response.text)
except ValueError:
    print("Unable to decode JSON results")

results = data['result']
lines = results.split('\n')

print(data)
# Shows only values that may be needed (JD, AD, X, Y, Z)
# Need to drop AD and convert all others to floats
start = False
for i in lines:
    if i.startswith('$$SOE'):
        start = True
    if i.startswith('$$EOE'):
        start = False
    if start and not i.startswith('$$SOE'):
        # print(i)
        print(i[:-1].split(', '))

print(response.status_code)
# If the request was valid...
# if response.status_code == 200:
#     # If the SPK file was generated, decode it and write it to the output file:
#     if "spk" in data:
#         #
#         # If a suggested SPK file basename was provided, use it:
#         if "spk_file_id" in data:
#             spk_filename = data["spk_file_id"] + ".bsp"
#         try:
#             f = open(spk_filename, "wb")
#         except OSError as err:
#             print(f"Unable to open SPK file '{spk_filename}': {err}")
#         # Decode and write the binary SPK file content:
#         f.write(base64.b64decode(data["spk"]))
#         f.close()
#         print(f"wrote SPK content to {spk_filename}")
#         sys.exit()
#     # Otherwise, the SPK file was not generated so output an error:
#     print("ERROR: SPK file not generated")
#     if "result" in data:
#         print(data["result"])
#     else:
#         ...
#         # print(response.text)
#     sys.exit(1)
#
# # If the request was invalid, extract error content and display it:
# if response.status_code == 400:
#     data = json.loads(response.text)
#     if "message" in data:
#         print(f"MESSAGE: {data['message']}")
#     else:
#         ...
#         # print(json.dumps(data, indent=2))
#
# # Otherwise, some other error occurred:
# print(f"response code: {response.status_code}")
# sys.exit(2)
