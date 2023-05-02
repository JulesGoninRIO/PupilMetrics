import tkinter as tk
import numpy as np
import os

class SettingsWindow(tk.Toplevel):
    
    def __init__(self,settings):
        super().__init__()
        self.resizable(width=False,height=False)
        self.geometry("270x280")
        self.title("Settings")
        settings_names = [' delete\nthreshold','  drop\ndetection','   fit\nprecision','derivative\nsmoothing']
        self.settings,self.settings_new = settings,[tk.IntVar() for i in range(4)]
        self.see_fit,self.zoom = tk.IntVar(value=settings[-1]),tk.IntVar(value=settings[-2])
        levels = tk.Text(self,width=17,height=1,relief=tk.FLAT,bg='light grey')
        levels.insert(tk.INSERT,'low  medium  high')
        levels.place(x=108,y=10)
        for i in range(4):
            setting_text = tk.Text(self,width=10,height=2,relief=tk.FLAT,bg='light grey')
            setting_text.insert(tk.INSERT,settings_names[i])
            setting_text.place(x=10,y=50*i+40)
            self.settings_new[i].set(settings[i])
            tk.Scale(self,from_=1,to=5,showvalue=False,variable=self.settings_new[i],length=150,orient='horizontal').place(x=100,y=50*i+50)
        tk.Checkbutton(self,text='Show fit',variable=self.see_fit,bg='light grey').place(x=20,y=240)
        tk.Checkbutton(self,text='Show zoom',variable=self.zoom,bg='light grey').place(x=100,y=240)
        tk.Button(self,text='Valid',bg='light blue',command=self.valid_settings).place(x=210,y=240)
        self.mainloop() 
        
    def valid_settings(self): # save settings, close settings window
        self.settings[:] = [setting.get() for setting in self.settings_new]+[self.zoom.get(),self.see_fit.get()]
        np.save(os.getcwd()+'/files/settings.npy',self.settings)
        self.destroy()