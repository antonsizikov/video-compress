# Video Compressor
This script calculates video bitrate based on file duration and target size and than compresses the video with this value in 2 passes to save maximum quality.

Targeted size is usfull if you want to compress video for some of the social networks.

Also you can eneble hardware acceleration to speed up the process but it is not recommended if you want the best quality.
## Using
To start the script type in terminal following command:
```
python3 compress.py
```
Or doble click on `compress-mac.command` ro `compress-win.bat`.

Than you need to type the path to folder with videos and target size and wait until compression is done.
## FFmpeg
This script requires [FFmpeg](https://ffmpeg.org). You can install it on your system using the following commands.

Windows:
```
winget install ffmpeg
```
macOS:
```
brew install ffmpeg
```
