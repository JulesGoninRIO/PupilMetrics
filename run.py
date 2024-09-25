import pupildata,updater
import tkinter as tk,threading
from tkinter import messagebox
from PIL import Image,ImageTk
from imageio import get_reader
from traceback import format_exc
from time import sleep
import os

class RunnerWindow(tk.Toplevel):
    
    def __init__(self,app):
        super().__init__()
        self.resizable(width=False,height=False) # prevent resize 
        self.title("Please wait")
        self.app_path = os.getcwd()+'/files/' # path to get logo, pupil-gif and review
        self.process_state = [' ',''] # current process state
        threading.Thread(target=self.play_gif).start()
        threading.Thread(target=self.process,args=(app,)).start()
        self.mainloop() # main loop waiting tkinter 
        
    def play_gif(self): # update pupil gif and state text and close winload when process done
        gif = get_reader(self.app_path+"pupil.gif") # load pupil gif
        gif_images = [ImageTk.PhotoImage(Image.fromarray(image)) for image in gif.iter_data()]
        pupil = tk.Label(self,image=gif_images[0])
        pupil.pack() # pupil gif image
        i = 0
        process_state_seen = []
        while self.process_state[0]: # until process done
            if self.process_state != process_state_seen: # new state process, text update
                state = tk.Text(self,width=15,height=1,relief=tk.FLAT)
                state.insert(tk.INSERT,self.process_state[0]+self.process_state[1])
                state.place(x=60,y=210)
                process_state_seen = [self.process_state[0],self.process_state[1]]
            if self.process_state[1] != 'pause':
                pupil.config(image=gif_images[i])
                pupil.image = gif_images[i] # update pupil gif
                i = (i+1)%6 # gif has 6 images
            sleep(0.2) # wait 0.2s
        self.destroy()
        
    def process(self,app): # process data and show if errors
        try:
            data = pupildata.PupilData(app.folder_path,app.machine,self.process_state,app.settings)
            if not data.raw:
                raise Exception(data.errors[1])
            if data.errors[0]:
                self.process_state[1] = 'pause'
                warn = "These files can't be read: \n"
                ques = "\nDo want you still want to process other files ?"
                if not messagebox.askyesno('Warning',warn+data.errors[0]+ques):
                    raise Exception(data.errors[1])
            data.no_artefact()
            if not app.settings[-1] or app.settings[-2]:
                data.fit_signal(self.process_state)
            if not app.settings[-1]:
                data.no_drop()
            os.mkdir(app.folder_path+'figures')
            app.update = updater.Updater(data,self.process_state)
            app.save()
            app.load()
        except Exception as err:
            log = open(self.app_path+'log.txt',"a")
            log.write(format_exc()) # write whole error in log file
            log.write('\n')
            log.close()
            messagebox.showerror('Data not processed',err)
            for i in [0,1,2,3,5]:
                app.menu1.entryconfigure(i,state='normal')
        self.process_state = ['','']