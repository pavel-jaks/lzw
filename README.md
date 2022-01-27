# lzw.py
###### Implementation of Lempel-Ziv-Welch 84 compression and decompression algorithm
___
## Usage
The program is intended to be used in command prompt.
Pass the program and its arguments as arguments to python interpreter.

For help: 
```commandline
python lzw.py -h
```
For Compression:
```commandline
python lzw.py notcompressedfile.extension
```
For decompression:
```commandline
python lzw.py -d compressedfile.lzw
```
The program will automatically create new file in which the output shall go.
For compression - the output file will have extension lzw; for decompression it will be txt.
However, you can specify the output file manually by giving the program
extra parameter
```
--out_file OUT_FILE
```
E.g.:
```commandline
python lzw.py -d --out_file decompressedfile.csv compressedfile.lzw
```

Of course, change the path of lzw.py file accordingly.

There are no extra dependencies - the program uses only python libraries.
To be precise, the program was developed using python 3.8.
___
## Lempel-Ziv-Welch 84
###### The algorithm

The description of the underlying compression algorithm can be
easily found on the internet.
For my part, I used the explanation of the process published by
Ing. Pavel Strachota, Ph.D. on his web page.
To be specific:

https://saint-paul.fjfi.cvut.cz/base/sites/default/files/POGR/POGR1/07.ukladani_a_komprese_obrazu.pdf (in Czech)

I should also mention that this program was developed as a part of my completion
of the computer graphics 1 (POGR1) course held during my undergrad studies of mathematical computer science
on Faculty of Nuclear Sciences and Physical Engineering of Czech Technical University in Prague.
___
© Pavel Jakš, 2021/2022
