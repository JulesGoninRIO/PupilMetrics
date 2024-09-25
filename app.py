import numpy as np

import os
from shutil import copy,rmtree
import pickle
from webbrowser import open_new

import tkinter as tk
from tkinter import filedialog,messagebox
from PIL import Image,ImageTk

import run,excel,settings # pupillometry code

class App(tk.Tk): # main window
        
    def __init__(self): # set up main window, tkinter widgets and menu
        super().__init__()
        self.resizable(width=False,height=False)
        self.title('Pupillometry')
        self.app_path = os.getcwd()+'/files/' 
        self.image_path = self.app_path+"logo.jpg"
        image = ImageTk.PhotoImage(Image.open(self.image_path).resize((1080,300),Image.BILINEAR))
        self.label = tk.Label(self,image=image)
        self.label.pack() 
        
        # initialize tkinter widgets
        self.settings = np.load(self.app_path+'settings.npy',allow_pickle=True)
        self.see_fit_button,self.zoom_button,self.violin_plot_button = tk.Checkbutton(),tk.Checkbutton(),tk.Checkbutton() 
        self.undo_all_button,self.forget_all_button,self.undo_button = tk.Button(),tk.Button(),tk.Button()
        self.forget_buttons,self.valid_drop_buttons,self.refuse_drop_buttons,self.measures_buttons = [],{},{},[] 
        self.horizontal_scale,self.vertical_scale = tk.Scale(),tk.Scale() 
        self.horizontal_scale_text,self.vertical_scale_text = tk.Text(),tk.Text() 
        
        menubar = tk.Menu(self) # menu architecture
        self.menu1 = tk.Menu(menubar,tearoff=0)
        self.menu1.add_command(label='NeuroLight',command=lambda:self.start('NeuroLight'))
        self.menu1.add_command(label='Diagnosys',command=lambda:self.start('Diagnosys'))
        self.menu1.add_command(label='Neuroptics',command=lambda:self.start('Neuroptics'))
        self.menu1.add_separator()
        self.menu1.add_command(label="Settings",command=lambda:settings.SettingsWindow(self.settings))
        menubar.add_cascade(label="Select",menu=self.menu1) 
        self.menu2 = tk.Menu(menubar,tearoff=0)
        self.menu2.add_command(label="Plot recordings",command=self.plots,state='disable')
        self.menu2.add_command(label="Plot derivatives",command=self.derivatives,state='disable')
        self.menu2.add_command(label="Distribution",command=self.distributions,state='disable')
        menubar.add_cascade(label="View",menu=self.menu2) 
        self.menu3 = tk.Menu(menubar,tearoff=0) 
        self.menu3.add_command(label="Data",state='disable',command=self.save_data)
        self.menu3.add_command(label="This figure",command=self.save_image)
        menubar.add_cascade(label="Export",menu=self.menu3) 
        self.menu4 = tk.Menu(menubar,tearoff=0)
        self.menu4.add_command(label="Help",command=lambda:open_new(self.app_path+"help.pdf")) 
        menubar.add_cascade(label="Info",menu=self.menu4) 
        self.config(menu=menubar)
        self.mainloop()
    
    #==============================================================================
    # Select
    
    def start(self,machine): # ask folder_path and run process if needed
        title = "Please select the "+machine+" recording folder"
        self.machine = machine
        self.folder_path = filedialog.askdirectory(title=title)+'/' # recording folder path 
        if self.folder_path == '/': # if user close the ask-directory window
            return
        if os.path.exists(self.folder_path+'figures/data.plk'): # check if already done
            ok = True # to load already processed data
            with open(self.folder_path+'figures/data.plk','rb') as inp:
                self.update = pickle.load(inp)
            if not np.all(self.update.settings==self.settings): # if settings have changed
                question = "Data has already been processed with different settings, do you want to delete and run again ?"
                ok = not messagebox.askyesno("Warning",question) 
            if ok:
                self.load() # load already processed data 
                return
        if os.path.exists(self.folder_path+'figures'):
            rmtree(self.folder_path+'figures')
        self.clean_all() 
        self.change_image(self.app_path+"logo.jpg",300)  
        self.set_menu('disable')
        run.RunnerWindow(self)
        
    def load(self): # load everything, data and variables
        self.set_menu('normal') 
        self.current_measure = 'BL' 
        self.current_signal,self.current_flash,self.current_table = tk.IntVar(value=0),tk.IntVar(value=1),tk.IntVar(value=0)
        self.zoom,self.see_fit = tk.IntVar(value=0),tk.IntVar(value=0)
        self.violin_plot,self.see_deriv = tk.IntVar(value=0),tk.IntVar(value=0)
        self.forget_buttons = [tk.Button() for k in range(self.update.m)]
        self.plots() # see plot with initial state: mean group recording
        
    def set_menu(self,state): # able/disable access to menu
        for i in range(3):
            self.menu1.entryconfigure(i,state=state)
            self.menu2.entryconfigure(i,state=state)
        self.menu1.entryconfig(4,state=state)
        self.menu3.entryconfig(0,state=state)
    
    #==============================================================================
    # View
    
    def plots(self): # see recordings
        self.see_deriv.set(0)
        self.place_zoom_button(self.change_recording) 
        if self.update.settings[-2]: # if fit curves are plotted
            self.see_fit_button = tk.Checkbutton(self,text='See fit',variable=self.see_fit,bg='magenta',command=self.change_plot)
            self.see_fit_button.place(x=120,y=25)
            
    def derivatives(self): # see derivatives
        self.see_deriv.set(1)
        self.place_zoom_button(self.change_plot) 
                   
    def distributions(self): # see distributions
        self.clean_all()
        self.violin_plot_button = tk.Checkbutton(self,text='Violin Plot',variable=self.violin_plot,bg='magenta',command=self.change_distribution(self.current_measure))
        self.violin_plot_button.place(x=20,y=25)
        measure_names = ['BL','MCA','RT','PIPR','dAMP','dLAT','dAUC']
        self.measures_buttons = [tk.Button(self,text=measure,command=self.change_distribution(measure)) for measure in measure_names]
        for k in range(len(self.measures_buttons)):
            self.measures_buttons[k].place(x=15,y=50*k+75)
        self.update.update_distribution()
        self.change_image(self.folder_path+'figures/'+self.current_measure+self.violin_plot.get()*'_v'+'.png',432)
    
    #==============================================================================
    # Export
                
    def save_image(self): # copy current image (.png) to asked path
        path = filedialog.asksaveasfilename(defaultextension='.png',initialfile='Untitled.png')
        if path:
            copy(self.image_path,path)
    
    def save_data(self): # save data (.xlsx) to asked path 
        ok_save = np.all([np.all([drop[peak][2] for peak in drop]) for drop in self.update.drops if drop])
        if not ok_save: # warning if user has not finished validation
            question = "You have not validated or refused all corrections, "
            question += "do you still want to export data (every other correction will remain) ?"
            ok_save = messagebox.askyesno("Warning",question)
        if ok_save:
            path = filedialog.asksaveasfilename(defaultextension='.xlsx',initialfile='.xlsx')
            if path:
                while os.path.exists(path):
                    try : # replace existing excel if not opened
                        os.remove(path)
                    except:
                        path = path[:-5]+'-copy.xlsx'
                excel.Excel(path,self.update.data)      
    
    #==============================================================================
    # Change Recording
    
    def change_image(self,path,shape): # change label image
       self.image_path = path 
       image = Image.open(path).resize((1080,shape),Image.BILINEAR)
       image = ImageTk.PhotoImage(image)
       self.label.configure(image=image)
       self.label.image = image
       
    # save format: 'figures/' + j(0 for mean) + m*'_' + '-'k(if flash) (+ '_d','_f') + '.png' 
    def change_plot(self,e=''): # change plot with current values (e='' for scale call)
        i,k,m,f,d,z = self.current_signal.get(),self.current_flash.get(),self.current_table.get(),self.see_fit.get(),self.see_deriv.get(),self.zoom.get()
        self.update.update_plot(i,k*z-1)
        self.change_image(self.folder_path+'figures/'+str(i)+(1-z)*m*'_'+z*('-'+str(k))+f*(1-d)*'_f'+d*'_d'+'.png',648)
                   
    def change_recording(self,e=''): # change plot and place modification buttons (e='' for scale call)
        self.change_plot()
        self.save()
        self.clean_validation_buttons() 
        i,k = self.current_signal.get(),self.current_flash.get()*self.zoom.get()-1
        if not i: # no modification button for mean recording
            return
        self.undo_all_button = tk.Button(self,text='Undo all',command=self.undo)
        self.undo_all_button.place(x=210,y=25) 
        for peak in self.update.drops[i]:
            [i1,i2,done_peak,k2,positions] = self.update.drops[i][peak]
            if k in [-1,k2] and not done_peak:
                self.place_validation_buttons(positions,peak)
        if k == -1:
            for k2 in range(self.update.m):
                [forgot,x] = self.update.flash_forgot[i,k2]
                if not forgot: # place forget button at the flash line bottom if not forgot
                    self.forget_buttons[k2] = tk.Button(self,text='X',bg='red',command=self.forget(i,k2))
                    self.forget_buttons[k2].place(x=x,y=350) 
            ok = not np.all(self.update.flash_forgot[i])
        else:
            ok = not self.update.flash_forgot[i,k,0]
        if ok:
            self.forget_all_button = tk.Button(self,text='X',bg='red',command=self.forget(i,k))
            self.forget_all_button.place(x=130,y=65) 
              
    def change_distribution(self,measure): # return function that change plot to measure
        def chg_box(): 
            self.current_measure = measure 
            self.change_image(self.folder_path+'figures/'+self.current_measure+self.violin_plot.get()*'_v'+'.png',432)
        return chg_box
    
    def place_zoom_button(self,command): # place group button and call command
        self.clean_all()
        if self.update.settings[-3]:
            self.zoom_button = tk.Checkbutton(self,text='Zoom',variable=self.zoom,bg='light blue',command=lambda:self.place_scales(command))
            self.zoom_button.place(x=20,y=25)
        self.place_scales(command)
    
    def place_scales(self,command): # place scales and call command
        self.clean_scales() 
        command()
        self.horizontal_scale = tk.Scale(self,variable=self.current_signal,from_=0,to=self.update.n-1,orient='horizontal',length=300,bg='white',command=command)
        self.horizontal_scale.place(x=390,y=600) 
        self.horizontal_scale_text = tk.Text(self,width=16,height=1,relief=tk.FLAT)
        self.horizontal_scale_text.insert(tk.INSERT,'Change Recording')
        self.horizontal_scale_text.place(x=473,y=580)
        self.bind("<Left>",lambda e:self.horizontal_scale.set(self.horizontal_scale.get()-1)) 
        self.bind("<Right>",lambda e:self.horizontal_scale.set(self.horizontal_scale.get()+1))
        if not self.zoom.get():
            m = (self.update.m-1)//5
            if not m: # scroll table scale needed when recording has more than 5 flash
                return
            self.vertical_scale = tk.Scale(self,variable=self.current_table,from_=0,to=m,showvalue=False,length=100,bg='white',command=self.change_plot)
            self.vertical_scale.place(x=100,y=420) # scroll table vertical scale
        elif self.update.settings[-3]: # individual zoom flash
            self.vertical_scale = tk.Scale(self,variable=self.current_flash,from_=1,to=self.update.m,length=150,bg='white',command=command)
            self.vertical_scale.place(x=80,y=420) 
            self.vertical_scale_text = tk.Text(self,width=6,height=2,relief=tk.FLAT)
            self.vertical_scale_text.insert(tk.END,'Change\nFlash')
            self.vertical_scale_text.place(x=20,y=480)
        self.bind("<Up>",lambda e:self.vertical_scale.set(self.vertical_scale.get()-1)) 
        self.bind("<Down>",lambda e:self.vertical_scale.set(self.vertical_scale.get()+1))
        
    #==============================================================================
    # Modify
    
    def place_validation_buttons(self,positions,peak): # put valid/refuse button at (x,y)
        def valid(refused): 
            self.valid_drop_buttons[peak].destroy()
            self.refuse_drop_buttons[peak].destroy()
            if not self.update.ticks_history:
                self.undo_button = tk.Button(self,text='Undo',command=self.unvalid)
                self.undo_button.place(x=300,y=25) 
            self.update.valid(refused,self.current_signal.get(),peak)
            self.change_plot()
        (x,y) = positions[self.zoom.get()]
        self.valid_drop_buttons[peak] = tk.Button(self,text='v',bg='light green',command=lambda:valid(0))
        self.valid_drop_buttons[peak].place(x=x,y=y) 
        self.refuse_drop_buttons[peak] = tk.Button(self,text='x',bg='orange',command=lambda:valid(1))
        self.refuse_drop_buttons[peak].place(x=x,y=y+25) 
    
    def unvalid(self): # undo last valid/refuse tick, update data and plots
        peak,positions = self.update.unvalid()
        self.place_validation_buttons(positions,peak)
        if not self.update.ticks_history: 
            self.undo_button.destroy()
        self.change_plot()
    
    def forget(self,i,k): # forget flash, update data and plots
        def f():
            self.update.undo(i,k,1)
            self.change_recording() 
        return f
    
    def undo(self): # go back to initial state for data and plots
        i,k = self.current_signal.get(),self.current_flash.get()*self.zoom.get()-1
        self.update.undo(i,k,0)
        self.change_recording() 
        
    def save(self):
        if not self.update.saved:
            with open(self.folder_path+'figures/data.plk','wb') as outp:
                pickle.dump(self.update,outp,pickle.HIGHEST_PROTOCOL)
            self.update.saved = True
        
    #==============================================================================
    # Clean
        
    def clean_all(self):
        for b in (self.measures_buttons):
            b.destroy()
        self.see_fit_button.destroy()
        self.violin_plot_button.destroy()
        self.zoom_button.destroy()
        self.clean_validation_buttons() 
        self.clean_scales() 
            
    def clean_validation_buttons(self): 
        for peak in self.valid_drop_buttons:
            self.valid_drop_buttons[peak].destroy()
        self.valid_drop_buttons = {}
        for peak in self.refuse_drop_buttons:
            self.refuse_drop_buttons[peak].destroy()
        self.refuse_drop_buttons = {}
        for b in self.forget_buttons:
            b.destroy()
            self.update.ticks_history = [] # reset ticks_history
        self.undo_all_button.destroy()
        self.forget_all_button.destroy()
        self.undo_button.destroy()
        
    def clean_scales(self):
        self.unbind("<Left>")
        self.unbind("<Right>")
        self.unbind("<Up>")
        self.unbind("<Down>")
        self.horizontal_scale.destroy()
        self.vertical_scale.destroy()
        self.horizontal_scale_text.destroy()
        self.vertical_scale_text.destroy()
        
App() # open interface