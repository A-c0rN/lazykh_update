#!/bin/sh

simp=""

while getopts 'd:f:sr:x:' flag
do
    case "${flag}" in
        d) 
            directory=${OPTARG}
            ;;
        f) 
            file=${OPTARG}
            ;;
        s) 
            simp="-s"
            ;;
        r) 
            rate="-r ${OPTARG}"
            ;;
        x) 
            size="-x ${OPTARG}"
            ;;

    esac
done

if [ -n "${simp}" ]
then 
    echo "Using Simplified Graphics"
else
    echo "Using Fancy Graphics"
fi

echo "Converting Script..."
python3 code/gentleScriptWriter.py -i "${directory}/${file}"
echo "Gentle Align..."
python3 gentle/align.py "${directory}/${file}.wav" "${directory}/${file}_g.txt" -o "${directory}/${file}.json"
echo "Schedule Creation..."
python3 code/scheduler.py -i "${directory}/${file}" $simp
echo "Rendering..."
python3 code/videoDrawer.py -i "${directory}/${file}" $simp $rate $size
echo "Combining Rendered Frames..."
python3 code/videoFinisher.py -i "${directory}/${file}" $rate $size 
echo "Done! Cleaning up..."
cd "${directory}"
rm "${file}_g.txt" "${file}.json" "${file}_schedule.csv"
echo "Done."