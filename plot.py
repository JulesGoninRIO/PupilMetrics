import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
plt.ioff()
import seaborn as sns
import matplotlib 
matplotlib.rcParams.update({'font.size':12})

class Plotter:
    
    # save all plots in path: single flash and all recordings 
    # call (n+1)*(1+nflash//5+nflash) save_plot
    def __init__(self,data,process_state):
        (n,m) = np.shape(data.flash_times)
        self.path = data.folder_path+'figures/'
        self.measure_names = ['BL (mm)','MCA (%)','RT (s)',
                       'PIPR (%)','dAMP (%/s^6)','dLAT (s)','dAUC (u)']
        process_state[0] = 'Plotting: '
        for i in range(n): 
            process_state[1] = str(i)+'/'+str(n-1) # update pupil loading text
            self.save_plot(data,i)
            if data.settings[-2]: # much less plot if user do not want to see zoom
                for k in range(m): 
                    self.save_plot(data,i,k)
        process_state[1] = 'end'
        self.distribution_measures(data)       
    
    # add table of measures bellow plot
    # d=0/1 for recording/derivative, 4 measures for recording, 3 last for derivative
    # write flash k, or if k=-1 from flash 5m to 5(m+1)
    def table_measures(self,data,measures_i,ax,d,m,k):
        table = [['flash color']+self.measure_names[4*d:4+3*d]]
        col = plt.get_cmap('Greys')(0.2)
        colors = [[col for i in range(len(table[0]))]]
        if k == -1:
            for i in range(min(len(measures_i)-5*m,5)):
                table += [[data.color_names[5*m+i]]+[round(x,2) for x in measures_i[5*m+i][4*d:4+3*d]]]
                colors += [len(table[0])*[data.color_codes[5*m+i]]]
        else:
            table += [[data.color_names[k]]+[round(x,2) for x in measures_i[k][4*d:4+3*d]]]
            colors += [len(table[0])*[data.color_codes[k]]] 
        ax.axis('off')
        tab = ax.table(cellText=table,loc='upper center',cellColours=colors,cellLoc='center') 
        tab.set_fontsize(12)
        tab.scale(1,2)
        
    # draw distibutions of measures in measures
    # save 2 figures (boxplot and violin plots): 'figures/measure_name(_v).png'
    def distribution_measures(self,data):
        palette = dict(zip(data.color_names,data.color_codes))
        for j,name in enumerate(self.measure_names):
            fig = plt.figure(figsize=(15,6))
            df = DataFrame()
            for k,col in enumerate(data.color_names):
                df[col] = [measures_i[k][j] for measures_i in np.array(data.measures)]
            sns.boxplot(data=df,palette=palette) # box plot colored
            sns.swarmplot(data=df,color='k') # add point distribution
            title = name[:name.index('(')-1]
            plt.title(data.machine+' -- '+title+' -- distribution')
            plt.ylabel(name)
            fig.savefig(self.path+title+'.png')
            fig = plt.figure(figsize=(15,6))
            sns.violinplot(data=df,palette=palette) # violin plot colored
            sns.swarmplot(data=df,color='k') # add point distribution
            plt.title(data.machine+' -- '+title+' -- distribution')
            plt.ylabel(name)
            fig.savefig(self.path+title+'_v.png')
    
    # save plots for recording i: recording, recording+fit, derivative 
    # plot curves for all steps and add measure table bellow
    # flash k (k=-1 for whole), m>0 when table measure is too big to fit (flash>5) for whole recording 
    # save format: 'figures/' + i+1(0 for mean) + m*'_' + '-'k+1(if flash) (+ '_d','_f') + '.png'  
    # save is long else is fast, ~0.5s/run
    def save_plot(self,data,i,k=-1,m=0):
        fig = matplotlib.figure.Figure(figsize=(15,9)) # recording
        fig_d = matplotlib.figure.Figure(figsize=(15,9)) # derivative
        (ax1,ax2) = fig.subplots(2,1,gridspec_kw={'height_ratios':[2,1]})
        (ax1_d,ax2_d) = fig_d.subplots(2,1,gridspec_kw={'height_ratios':[2,1]})
        title = str(i)+' - '+data.names[i]
        save_name = str(i)+m*'_'
        fit,flashes,measures_i = data.fitted[i],data.flash_times[i],data.measures[i]
        (a,b) = data.signal_range[i][k] 
        time = [j/data.f for j in range(b-a)]
        ax1.plot(time,data.raw[i][a:b],label='raw')
        if not data.settings[-1]:
            ax1.plot(time,data.artefact_free[i][a:b],label='intermediate')
        ax1.plot(time,data.drop_free[i][a:b],label='final',color="g")
        end = 4*data.f*(1+k)-1 # end of derivative plot, 4s zoom for flash
        ax1_d.plot(time[:end],data.grad[i][a:b][:end],label='derivative')
        ax1_d.plot(time[:end],data.deriv_smooth[i][a:b][:end],label='smooth derivative')
        self.table_measures(data,measures_i,ax2,0,m,k)
        self.table_measures(data,measures_i,ax2_d,1,m,k)
        if k == -1: # whole recording
            for k2 in range(len(flashes)): # vertical colored flash lines
                ax1.axvline(x=flashes[k2]/data.f,color=data.color_codes[k2],linestyle='--')
                ax1_d.axvline(x=flashes[k2]/data.f,color=data.color_codes[k2],linestyle='--')
        else: # flash k
            title += ' -- '+str(k+1)+' - '+data.color_names[k]
            save_name += '-'+str(k+1)
            t = flashes[k]+(data.f-flashes[k])*bool(k) # flash is at 1s except for 1st one
            ax1.axvline(x=t/data.f,color=data.color_codes[k],linestyle='--') # vertical colored flash line
            ax1_d.axvline(x=t/data.f,color=data.color_codes[k],linestyle='--')
        ax1.set(title=data.machine+' -- '+title,xlabel='time (s)',ylabel='pupil size (mm)')
        ax1_d.set(title=data.machine+' -- '+title,xlabel='time (s)')
        ax1.legend(),ax1_d.legend()
        fig.savefig(self.path+save_name+'.png') 
        fig_d.savefig(self.path+save_name+'_d.png') 
        if data.settings[-2]: # less plot time if user do not want to see fit
            ax1.plot(time,fit[a:b],label='fitted',color="m")
            ax1.legend()
            fig.savefig(self.path+save_name+'_f.png')
        if len(flashes) > 5*(m+1): # if tables too big, repeat until we can see every flash
            self.save_plot(data,i,k,m+1)