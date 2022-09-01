#!/bin/sh

while getopts d:f: flag
do
    case "${flag}" in
        d) directory=${OPTARG};;
        f) file=${OPTARG};;
    esac
done

# echo "Converting Script..."
# python3 code/gentleScriptWriter.py -i "${directory}/${file}"
# echo "Gentle Align..."
# python3 gentle/align.py "${directory}/${file}.wav" "${directory}/${file}_g.txt" -o "${directory}/${file}.json"
echo "Schedule Creation..."
python3 code/scheduler.py -i "${directory}/${file}" -s
echo "Rendering..."
python3 code/videoDrawer.py -i "${directory}/${file}" -s
echo "Combining Rendered Frames..."
python3 code/videoFinisher.py -i "${directory}/${file}" -k
# echo "Done! Cleaning up..."
# cd "${directory}"
# rm "${file}_g.txt" "${file}.json" "${file}_schedule.csv"
echo "Done."