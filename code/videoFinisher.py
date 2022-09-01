import argparse
import os.path
import os
import shutil

FRAME_RATE = 24
W_W = 1920
W_H = 1080


def emptyFolder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
    try:
        os.rmdir(folder)
    except Exception as e:
        print("Failed to delete %s. Reason: %s" % (folder, e))


parser = argparse.ArgumentParser(description="blah")
parser.add_argument("--input_file", "-i", type=str, help="the script")
parser.add_argument(
    "--keep_frames",
    "-k",
    action="store_true",
    help="Keep Frame images",
)
args = parser.parse_args()
INPUT_FILE = args.input_file

command = f"ffmpeg -hide_banner -v quiet -stats -y -r {FRAME_RATE} -f image2 -s {W_W}x{W_H} -i {INPUT_FILE}_frames/f%06d.png -i {INPUT_FILE}.wav -vcodec libx264 -shortest -pix_fmt yuv420p -b 2M -acodec aac {INPUT_FILE}_final.mp4"
os.system(command)

if not args.keep_frames:
    emptyFolder(INPUT_FILE + "_frames")
