# Help

__Data format__:  
folder containing only recordings of the same machine and same protocol (can lead to text display “format error” or “shape error”) 
To load faster (from ~20s to 1-2s), copy the folder ‘foxexe’ from T/studies on your computer, and go to ‘forexe/dist/app/app.exe’ to create a new shortcut  
-----------
__How to use the interface__:  
Click on select (top left menu), select the machine, a window open to select the folder of recordings (NeuroLight or Diagnosys)  
A waiting window appear if you have not yet processed data (3-10s process per recording depending on length frequency and quality)  
You see now mean recording with a horizontal slider at index 0 bellow, move the slider (or press -> keyboard) to see individual recordings  
You can know validate/refuse artefacts corrections and save data (export/data on menu)  
-----------
__Group button__: zoom to single flash (a vertical slider appears bind with keyboard -> up/down to change flash)  
__Fit button__: to see how the software fits recording (purple curve now, green before)  
__Green v button__: valid an artefact detection, select final green curve  
__Orange x button*__: reject an artefact detection, select intermediate orange curve  
The orange intermediate curve becomes then final green  
__Red X button*__: reject a flash or whole recording for the one on top left  
All treatments disappeared and removed from means/distributions 
__Undo all button*__: go back to initial treatments for the recording you see  
__Undo button*__: undo last click on green v or orange x button  
__*__ updates plots/means/measures/distributions and take 1-2s (screen freezes)  
----------- 
__Settings__ are saved inside the interface, if data have been processed with different settings, you can choose to see previous settings or run and replace with new settings  
Settings are advanced and are useful to run faster while developing the method  
__Delete threshold__: acceleration threshold to detect and delete points (default: medium)  
Changes the amount of artefact detected by 1st step, misses can be compensated by 2nd step but low level may delete reel part of recording
__Drop detection__: minimal size to detect drops and propose artefacts (default: medium)
Changes the amount of artefacts detected by 2nd step, high level may miss small artefacts and low level may detect too much artefacts and lead to many user rejections
__Fit precision__: maximum time/iteration to fit recordings (default: high)
Low level makes the process faster, especially for worst recordings
The precision of the fit is not the most relevant to detect drops
__Derivative smoothing__: smoothing level of Savitzky-Golay filter (default: medium)
Uses 8 to 4 polynomial order interpolation for 19 to 27 window points
__See fit__: not plotting fit makes improve a little plot time (default: yes)
__See zoom__: not plotting individual flash makes improve a lot plot time (default: yes)
