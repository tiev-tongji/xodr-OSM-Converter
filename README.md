# xodr-OSM-Converter

A simple python script to convert OpenDrive file to OpenStreetMap file.

#### how it works

The parser samples the roads in the OpenDrive road network that are expressed analytically, storing key nodes required by the OSM format at appropriate intervals, and connecting the nodes in straight lines in a logical form.



### Usage

To use the converter, you should put your OpenDRIVE file in the resource folder, and run Converter.py

```shell
usage: Converter.py [-h] [--debug DEBUG] [--input_file INPUT_FILE]
                    [--scale SCALE] [--precise PRECISE]
                    [--output_file OUTPUT_FILE]

A random road generator

optional arguments:
  -h, --help            show this help message and exit
  --debug DEBUG         Is using debug mode
  --input_file INPUT_FILE
                        Input OpenDRIVE file name
  --scale SCALE         Scale of xodr file (in meter)
  --precise PRECISE     Precision of OSM file (in meter)
  --output_file OUTPUT_FILE
                        Output OSM file name
```

For example, you may use the example OpenDRIVE file (named `example.xodr`) in `./resources/`. 

```
pip install -r requirements.txt # install the dependencies
cd src
python Converter.py             # run using default parameters

# which is equal to python Converter.py --input_file=example.xodr --output_file=example.osm
```

and you will see:

```
Namespace(debug=False, input_file='example.xodr', output_file='example.osm', precise=0.1, scale=10000)
Start converting file...
Reading OpenDrive file: ../resource/example.xodr
Converting...
Processing road_id=109: 100%|################################| 98/98 [00:00<00:00, 1863.52it/s]
All done
```



### Dependency

python=3.7.3

geompreds==1.0.2

lxml==4.5.2

matplotlib==3.3.0

numpy==1.19.0

Pillow==7.2.0

Pyqtree==1.0.0

scipy==1.5.1

tqdm==4.48.0


