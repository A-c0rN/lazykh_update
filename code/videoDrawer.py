import argparse
from fractions import Fraction
import os.path
import numpy as np
from PIL import Image, ImageDraw
import math
from utils import getFilenameOfLine
import shutil
from time import time

FRAME_START_RENDER_AT = 0
PRINT_EVERY = 10
FRAME_RATE = 24
PARTS_COUNT = 5
W_W = 1920
W_H = 1080
W_M = 20
EMOTION_POSITIVITY = [1, 1, 0, 0, 0, 1]
POSE_COUNT = 30
SCRIBBLE_W = 880
SCRIBBLE_H = 1000

MAX_JIGGLE_TIME = 7
BACKGROUND_COUNT = 5


def getJiggle(x, fader, multiplier):
    if x >= MAX_JIGGLE_TIME:
        return 1
    return math.exp(-fader * pow(x / multiplier, 2)) * math.sin(x / multiplier)


def drawFrame(
    INPUT_FILE,
    origScript,
    CACHES,
    USE_BILLBOARDS,
    ENABLE_JIGGLING,
    MOUTH_COOR,
    frameNum,
    paragraph,
    emotion,
    imageNum,
    pose,
    phoneNum,
    poseTimeSinceLast,
    poseTimeTillNext,
):
    FLIPPED = paragraph % 2 == 1

    if paragraph == CACHES[0][0]:
        frame = CACHES[0][1]
    else:
        frame = Image.open(f"assets/bg/bga{str(paragraph % BACKGROUND_COUNT)}.png")
        CACHES[0] = [paragraph, frame]
    frame = Image.eval(
        frame, lambda x: int(256 - (256 - x) / 2)
    )  # Makes the entire background image move 50% closer to white. In other words, it's paler.

    scribble = None
    if USE_BILLBOARDS:
        FILENAME = (
            f"{INPUT_FILE}_billboards/{getFilenameOfLine(origScript[imageNum])}.png"
        )
        if imageNum == CACHES[2][0]:
            scribble = CACHES[2][1]
        elif os.path.isfile(FILENAME):
            scribble = Image.open(FILENAME)
            CACHES[2] = [imageNum, scribble]

        if scribble is not None:
            s_W, s_H = scribble.size
            W_scale = SCRIBBLE_W / s_W
            H_scale = SCRIBBLE_H / s_H
            O_scale = min(W_scale, H_scale)
            scribble = scribble.resize(
                (int(round(O_scale * s_W)), int(round(O_scale * s_H))),
                Image.Resampling.LANCZOS,
            )

            s_W, s_H = scribble.size

    s_X = 0
    if FLIPPED:
        s_X += int(W_W / 2)

    if USE_BILLBOARDS and scribble is not None:
        img1 = ImageDraw.Draw(frame)
        img1.rectangle(
            [(s_X + W_M - 4, W_M - 4), (s_X + W_W / 2 - W_M + 8, W_H - W_M + 8)],
            fill="#603810",
        )
        img_centerX = s_X + W_M * 2 + SCRIBBLE_W * 0.5
        img_centerY = W_M * 2 + SCRIBBLE_H * 0.5
        img_pasteX = int(round(img_centerX - s_W / 2))
        img_pasteY = int(round(img_centerY - s_H / 2))
        frame.paste(scribble, (img_pasteX, img_pasteY))

    jiggleFactor = 1
    if ENABLE_JIGGLING:
        preJF = getJiggle(poseTimeSinceLast, 0.06, 0.6) - getJiggle(
            poseTimeTillNext, 0.06, 0.6
        )
        jiggleFactor = pow(1.07, preJF)

    blinker = 0
    blinkFactor = poseTimeSinceLast % 60
    if blinkFactor == 57 or blinkFactor == 58:
        blinker = 2
    elif blinkFactor >= 56:
        blinker = 1

    poseIndex = emotion * 5 + pose
    poseIndexBlinker = poseIndex * 3 + blinker
    body = Image.open(f"assets/p/pose{'{:04d}'.format(poseIndexBlinker + 1)}.png")

    mouthImageNum = phoneNum + 1
    if EMOTION_POSITIVITY[emotion] == 0:
        mouthImageNum += 11
    mouth = Image.open(f"assets/m/mouth{'{:04d}'.format(mouthImageNum)}.png")

    if MOUTH_COOR[poseIndex, 2] < 0:
        mouth = mouth.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if MOUTH_COOR[poseIndex, 3] != 1:
        m_W, m_H = mouth.size
        mouth = mouth.resize(
            (
                int(abs(m_W * MOUTH_COOR[poseIndex, 2])),
                int(m_H * MOUTH_COOR[poseIndex, 3]),
            ),
            Image.Resampling.LANCZOS,
        )
    if MOUTH_COOR[poseIndex, 4] != 0:
        mouth = mouth.rotate(
            -MOUTH_COOR[poseIndex, 4], resample=Image.Resampling.BICUBIC
        )

    m_W, m_H = mouth.size
    body.paste(
        mouth,
        (
            int(MOUTH_COOR[poseIndex, 0] - m_W / 2),
            int(MOUTH_COOR[poseIndex, 1] - m_H / 2),
        ),
        mouth,
    )

    ow, oh = body.size
    nh = oh * jiggleFactor
    nw = ow / jiggleFactor
    inh = int(round(nh))
    inw = int(round(nw))
    inx = int(round(W_W * 0.75 - nw / 2))
    if inx < 300:
        inx -= 50
    else:
        inx += 50
    iny = int(round(W_H - nh))
    body = body.resize((inw, inh), Image.Resampling.LANCZOS)

    if FLIPPED:
        body = body.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    frame.paste(body, (inx - s_X, iny), body)
    if not os.path.isdir(f"{INPUT_FILE}_frames"):
        os.makedirs(f"{INPUT_FILE}_frames")
    frame.save(f"{INPUT_FILE}_frames/f{'{:06d}'.format(frameNum)}.png")


def duplicateFrame(INPUT_FILE, prevFrame, thisFrame):
    prevFrameFile = f"{INPUT_FILE}_frames/f{'{:06d}'.format(prevFrame)}.png"
    thisFrameFile = f"{INPUT_FILE}_frames/f{'{:06d}'.format(thisFrame)}.png"
    shutil.copyfile(prevFrameFile, thisFrameFile)


def infoToString(arr):
    return ",".join(map(str, arr))


def setPhoneme(phonemeTimeline, phonemesPerFrame, i):
    phoneme = phonemeTimeline[i][0]
    thisFrame = phonemeTimeline[i][1]
    nextFrame = phonemeTimeline[i + 1][1]
    frameLen = nextFrame - thisFrame
    simple = [["y", 0], ["t", 6], ["f", 7], ["m", 8]]
    prevPhoneme = "na"
    # print(phoneme)
    if i >= 1:
        prevPhoneme = phonemeTimeline[i - 1][0]
    nextPhoneme = phonemeTimeline[i + 1][0]
    for s in simple:
        if phoneme == s[0]:
            phonemesPerFrame[thisFrame:nextFrame] = s[1]
    if phoneme == "u":
        phonemesPerFrame[thisFrame:nextFrame] = 9
        if frameLen == 2:
            phonemesPerFrame[thisFrame + 1] = 10
        elif frameLen >= 3:
            phonemesPerFrame[thisFrame + 1 : nextFrame - 1] = 10
    elif phoneme == "a":
        START_FORCE_OPEN = prevPhoneme == "t" or prevPhoneme == "y"
        END_FORCE_OPEN = nextPhoneme == "t" or nextPhoneme == "y"
        OPEN_TRACKS = [
            [[1], [2], [2], [2]],
            [[2, 1], [1, 2], [2, 1], [3, 2]],
            [[1, 2, 1], [1, 3, 2], [2, 3, 1], [2, 3, 2]],
            [[1, 3, 2, 1], [1, 2, 3, 2], [2, 3, 2, 1], [2, 3, 3, 2]],
        ]
        if frameLen >= 5:
            startSize = 1
            endSize = 1
            if START_FORCE_OPEN:
                startSize = 2
            if END_FORCE_OPEN:
                endSize = 2
            for fra in range(thisFrame, nextFrame):
                starter = min(
                    fra - thisFrame + startSize, nextFrame - 1 - fra + endSize
                )
                if starter >= 3:
                    if starter % 2 == 1:
                        phonemesPerFrame[fra] = 4
                    else:
                        phonemesPerFrame[fra] = 5
                else:
                    phonemesPerFrame[fra] = (starter - 1) * 2
        else:
            index = 0
            if START_FORCE_OPEN:
                index += 2
            if END_FORCE_OPEN:
                index += 1
            choiceArray = OPEN_TRACKS[frameLen - 1][index]
            for fra in range(thisFrame, nextFrame):
                phonemesPerFrame[fra] = (choiceArray[fra - thisFrame] - 1) * 2
    if phoneme == "a" or phoneme == "y":
        if prevPhoneme == "u":
            phonemesPerFrame[thisFrame] += 1
        if nextPhoneme == "u":
            phonemesPerFrame[nextFrame - 1] += 1
    return phonemesPerFrame


def timestepToFrames(timestep):
    return max(0, int(timestep * FRAME_RATE - 2))


def stateOf(schedules, indicesOn, p):
    if indicesOn[p] == -1:
        return 0
    parts = schedules[p][indicesOn[p]].split(",")
    return int(parts[2])


def frameOf(schedules, indicesOn, p, offset):
    if indicesOn[p] + offset <= -1 or indicesOn[p] + offset >= len(schedules[p]):
        return -999999
    parts = schedules[p][indicesOn[p] + offset].split(",")
    timestep = float(parts[0])
    frames = timestepToFrames(timestep)
    return frames


def genSchedules(lines):
    schedules = [None] * PARTS_COUNT
    for i in range(PARTS_COUNT):
        schedules[i] = lines[i].split("\n")
        if i == 4:
            schedules[i] = schedules[i][0:-1]
    return schedules


def getFrameCount(schedules):
    lastParts = schedules[-1][-2].split(",")
    lastTimestamp = float(lastParts[0])
    FRAME_COUNT = timestepToFrames(lastTimestamp + 1)
    return FRAME_COUNT


def getPhonemes(SIMP, schedules, FRAME_COUNT):
    phonemeTimeline = []
    for i in range(len(schedules[4])):
        parts = schedules[4][i].split(",")
        timestamp = float(parts[0])
        framestamp = timestepToFrames(timestamp)
        if (
            i >= 1 and framestamp <= phonemeTimeline[-1][1]
        ):  # we have a 0-frame phoneme! Try to fix it.
            if i >= 2 and phonemeTimeline[-2][1] <= framestamp - 2:
                phonemeTimeline[-1][1] = framestamp - 1  # shift previous one back
            else:
                framestamp += 1  # shift current one forward
        phoneme = parts[2]
        phonemeTimeline.append([phoneme, framestamp])
    phonemeTimeline.append(["end", FRAME_COUNT])
    phonemesPerFrame = np.zeros(FRAME_COUNT, dtype="int32")
    for i in range(len(phonemeTimeline) - 1):
        phonemesPerFrame = setPhoneme(phonemeTimeline, phonemesPerFrame, i)
    if SIMP:
        print(
            "Mapping Phonemes to Simple (Note, will look off if the scheduler wasn't compiled with simple!)"
        )
        newList = []
        for i in phonemesPerFrame.tolist():
            if i in [0, 8]:
                pass
            else:
                i = 0
            newList.append(i)
        phonemesPerFrame = np.array(newList, dtype="int32")
    return phonemesPerFrame


def main():
    startDraw = time()
    parser = argparse.ArgumentParser(description="blah")
    parser.add_argument(
        "--input_file", "-i", type=str, help="Script Asset (No File Extesion)"
    )
    parser.add_argument(
        "--use_billboards", "-b", action="store_true", help="Use Billboards"
    )
    parser.add_argument(
        "--jiggly_transitions", "-j", action="store_true", help="Pose Transition Jiggle"
    )
    parser.add_argument(
        "--no_frame_caching",
        "-n",
        action="store_false",
        help="Duplicate Frames that are similar.",
    )
    parser.add_argument(
        "--simple", "-s", action="store_true", help="Simple Style, no phoneme text."
    )
    args = parser.parse_args()
    INPUT_FILE = args.input_file
    USE_BILLBOARDS = args.use_billboards
    ENABLE_JIGGLING = args.jiggly_transitions
    ENABLE_FRAME_CACHING = args.no_frame_caching
    SIMP = args.simple

    with open(f"{INPUT_FILE}_schedule.csv", "r+") as f:
        scheduleLines = f.read().split("\nSECTION\n")
    with open(f"{INPUT_FILE}.txt", "r+") as f:
        origScript = f.read().split("\n")
    with open("code/mouthCoordinates.csv", "r+") as f:
        mouthCoordinatesStr = f.read().split("\n")

    schedules = genSchedules(scheduleLines)
    FRAME_COUNT = getFrameCount(schedules)
    phonemesPerFrame = getPhonemes(SIMP, schedules, FRAME_COUNT)

    # while "" in origStr:
    #    origStr.remove("")

    MOUTH_COOR = np.zeros((POSE_COUNT, 5))
    for i in range(len(mouthCoordinatesStr)):
        parts = mouthCoordinatesStr[i].split(",")
        for j in range(5):
            MOUTH_COOR[i, j] = float(parts[j])
    MOUTH_COOR[:, 0:2] *= 3  # upscale for 1080p, not 360p

    lastFrameInfo = None
    CACHES = [[None, None]] * PARTS_COUNT
    FRAME_CACHES = {}
    indicesOn = [-1] * (PARTS_COUNT - 1)
    print("Drawing Frames...")
    for frame in range(0, FRAME_COUNT):
        for p in range(PARTS_COUNT - 1):
            frameOfNext = frameOf(schedules, indicesOn, p, 1)
            if frameOfNext >= 0 and frame >= frameOfNext:
                indicesOn[p] += 1
        paragraph = stateOf(schedules, indicesOn, 0)
        emotion = stateOf(schedules, indicesOn, 1)
        imageNum = stateOf(schedules, indicesOn, 2)
        pose = stateOf(schedules, indicesOn, 3)
        timeSincePrevPoseChange = frame - frameOf(schedules, indicesOn, 3, 0)
        timeUntilNextPoseChange = frameOf(schedules, indicesOn, 3, 1) - frame

        TSPPC_cache = (
            min(timeSincePrevPoseChange, MAX_JIGGLE_TIME) if ENABLE_JIGGLING else 0
        )
        TUNPC_cache = (
            min(timeUntilNextPoseChange, MAX_JIGGLE_TIME) if ENABLE_JIGGLING else 0
        )
        IMAGE_cache = imageNum if USE_BILLBOARDS else 0

        thisFrameInfo = infoToString(
            [
                paragraph,
                emotion,
                IMAGE_cache,
                pose,
                phonemesPerFrame[frame],
                TSPPC_cache,
                TUNPC_cache,
            ]
        )
        if ENABLE_FRAME_CACHING and thisFrameInfo not in FRAME_CACHES:
            FRAME_CACHES[thisFrameInfo] = frame

        if frame >= FRAME_START_RENDER_AT:
            if ENABLE_FRAME_CACHING and FRAME_CACHES[thisFrameInfo] < frame:
                duplicateFrame(INPUT_FILE, FRAME_CACHES[thisFrameInfo], frame)
            else:
                drawFrame(
                    INPUT_FILE,
                    origScript,
                    CACHES,
                    USE_BILLBOARDS,
                    ENABLE_JIGGLING,
                    MOUTH_COOR,
                    frame,
                    paragraph,
                    emotion,
                    imageNum,
                    pose,
                    phonemesPerFrame[frame],
                    timeSincePrevPoseChange,
                    timeUntilNextPoseChange,
                )
            print(f"Frame {frame+1} of {FRAME_COUNT}          ", end="\r")
    endDraw = time()
    renderTime = int(endDraw) - int(startDraw)
    avgFPS = round(FRAME_COUNT / renderTime, 0)
    print(f"\nDone! Took {renderTime} seconds to render. (~{avgFPS} FPS)")


if __name__ == "__main__":
    main()
