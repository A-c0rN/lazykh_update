import argparse
from utils import removeTags

parser = argparse.ArgumentParser(description="blah")
parser.add_argument(
    "--input_file", "-i", type=str, help="Script Filename (No Extensions)"
)
args = parser.parse_args()
INPUT_FILE = args.input_file

with open(f"{INPUT_FILE}.txt", "r+") as f:
    script = f.read()
with open(f"{INPUT_FILE}_g.txt", "w+") as f:
    f.write(removeTags(script))

print("Done creating the gentle-friendly script!")
