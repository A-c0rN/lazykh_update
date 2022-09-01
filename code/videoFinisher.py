import argparse
import os.path
import os
import shutil


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
parser.add_argument("--framerate", "-r", type=int, default=24, help="Store Framerate.")
parser.add_argument(
    "--framesize", "-x", type=str, default="1920x1080", help="Store Frame size."
)
args = parser.parse_args()
INPUT_FILE = args.input_file
FRAME_RATE = args.framerate
W_W, W_H = (int(i) for i in args.framesize.split("x"))
print(W_W, W_H)

command = f"ffmpeg -hide_banner -v quiet -stats -y -r {FRAME_RATE} -f image2 -s {W_W}x{W_H} -i {INPUT_FILE}_frames/f%06d.png -i {INPUT_FILE}.wav -vcodec libx264 -shortest -pix_fmt yuv420p -b 2M -acodec aac {INPUT_FILE}_final.mp4"
os.system(command)

if not args.keep_frames:
    emptyFolder(INPUT_FILE + "_frames")
