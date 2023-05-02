import numpy as np
from scipy.signal import savgol_filter
import plot # pupillometry code

class Updater:
    
    # add means, measures, derivatives and signal range to data
    # computes measures and plot everything 
    def __init__(self,data,running): 
        self.data = data
        self.settings = data.settings
        for M in [data.raw,data.artefact_free,data.drop_free,data.fitted,data.flash_times]:
            M.insert(0,np.nanmean(M,axis=0))
        (n,m) = np.shape(data.flash_times)
        self.n,self.m = n,m
        data.measures = np.zeros((n,m,7))
        self.flash_forgot = np.zeros((n,m,2),dtype=np.int64)
        self.signal_updated = np.ones((n,m+1),dtype=np.int8)
        data.signal_range = np.zeros((n,m+1,2),dtype=np.int64)
        data.grad = [[] for i in range(n)]
        data.deriv_smooth = [[] for i in range(n)]
        data.flash_times[0] = [int(flash) for flash in data.flash_times[0]]
        self.drops = [{} for i in range(n)]
        for i in range(n):
            t = min(data.flash_times[i][0],data.f)
            self.compute_measures(i,m-1)
            for k in range(m-1):    
                self.compute_measures(i,k)
                data.signal_range[i,k,:] = [data.flash_times[i][k]-t,data.flash_times[i][k+1]-t]
            data.signal_range[i,0,0] = 0
            data.signal_range[i,-2,0] = data.flash_times[i][-1]-t
            data.signal_range[i,-2:,1] = len(data.raw[i])
            if i: # not for mean signal
                k = 0
                [a,b] = self.data.signal_range[i,k]
                for [i1,peak,i2] in data.drops[i-1]:
                    while peak > b:
                        k += 1
                        [a,b] = self.data.signal_range[i,k]
                    self.drops[i][peak] = [i1,i2,0,k,[self.position(peak,i,0,len(data.raw[i])),self.position(peak,i,a,b)]]
                for k in range(m):
                    self.flash_forgot[i,k,1] = 165+data.flash_times[i][k]/len(data.raw[i])*760
        self.treated = [np.copy(data.artefact_free),np.copy(data.drop_free),np.copy(data.fitted)]
        self.treated = [np.nan*self.treated[0]]+self.treated
        self.plot = plot.Plotter(data,running)
        self.ticks_history = []
        self.distribution_updated = True
        self.saved = False
        
    def position(self,peak,i,a,b): # positions to place validation buttons in the interface
        ymin = min(np.nanmin(self.data.raw[i][a:b]),min(self.data.artefact_free[i][a:b]),min(self.data.drop_free[i][a:b]))
        ymax = max(np.nanmax(self.data.raw[i][a:b]),max(self.data.artefact_free[i][a:b]),max(self.data.drop_free[i][a:b]))
        return (170+(peak-a)/(b-a)*760,100+(ymax-self.data.artefact_free[i][peak])/(ymax-ymin)*270)
        
    def compute_measures(self,i,k): # computes measures for recording i and flash k
        f = self.data.f
        if not self.flash_forgot[i,k,0]:
            flash = self.data.flash_times[i][k]
            base_diam = np.mean(self.data.drop_free[i][flash-int(0.25*f):flash]) 
            signal = self.data.drop_free[i]/base_diam*100 # use %
            flash71 = flash+int(7.1*f)
            if k<self.m-1:
                end_flash = self.data.flash_times[i][k+1]
            else:
                end_flash = len(signal)
            if flash71<end_flash:
                six_rec = 100-np.mean(signal[flash+7*f:flash71]) # % between 7-7.1s
            else: # if another flash or recording end before 6s
                six_rec = np.nan
            if not self.data.is_strong[k]:
                end_flash = flash+3*f
            MCA = 100-np.min(signal[flash:end_flash]) # % at the peak / latency
            latency = (np.argmin(signal[flash:end_flash])+2.42)/f
            self.data.grad[i] = np.gradient(self.data.drop_free[i])*f
            try:
                x = self.settings[3] # smooth derivative
                deriv_smooth = savgol_filter(self.data.grad[i],17+2*x,9-x)
            except:
                deriv_smooth = np.nan*np.zeros(len(self.data.drop_free[i]))
            self.data.deriv_smooth[i] = deriv_smooth
            dAMP = np.max(deriv_smooth[flash+int(0.5*f):flash+int(2.25*f)]) # maximum of derivative / latency
            dLAT = (np.argmax(deriv_smooth[flash+int(0.5*f):flash+int(2.25*f)])+int(0.5*f))/f 
            dAUC = 0
            for j in range(flash+int(0.25*f),flash+int(2.25*f)):
                if deriv_smooth[j]>0 and deriv_smooth[j+1]>0:
                    dAUC += deriv_smooth[j] # integral of absolute value of derivative between 0.25-2.25s 
            self.data.measures[i,k,:] = [base_diam,MCA,latency,six_rec,dAMP,dLAT,dAUC]
        else:
            self.data.measures[i,k,:] = 7*[np.nan]
                
    def update_distribution(self):
        if not self.distribution_updated:
            self.plot.distribution_measures(self.data)
            self.distribution_updated = True
    
    def update_plot(self,i,k): 
        if not self.signal_updated[i,k]:
            self.plot.save_plot(self.data,i,k)
            self.signal_updated[i,k] = 1
                
    def valid(self,refused,i,peak):
        self.update_drop_free(i,peak,refused,1)
        self.ticks_history += [(refused,i,peak)]
        self.saved = False
        
    def unvalid(self):
        (refused,i,peak) = self.ticks_history[-1] 
        self.ticks_history.remove((refused,i,peak))
        [i1,i2,done_peak,k,positions] = self.drops[i][peak]
        self.update_drop_free(i,peak,refused,0)
        return peak,positions # return to place again modification buttons
            
    def undo(self,i,k,forgot): # come back to initial state or forget signal
        [a,b] = self.data.signal_range[i,k]
        self.data.artefact_free[i][a:b] = self.treated[1*(1-forgot)][i][a:b]
        self.data.drop_free[i][a:b] = self.treated[2*(1-forgot)][i][a:b]
        self.data.fitted[i][a:b] = self.treated[3*(1-forgot)][i][a:b]
        self.data.artefact_free[0][a:b] = np.nanmean(self.data.artefact_free[1:],axis=0)[a:b]
        self.data.drop_free[0][a:b] = np.nanmean(self.data.drop_free[1:],axis=0)[a:b]
        self.data.fitted[0][a:b] = np.nanmean(self.data.fitted[1:],axis=0)[a:b]
        for peak in self.drops[i]:
            if k in [-1,self.drops[i][peak][3]]:
                self.drops[i][peak][2] = forgot
        if k == -1:
            for k2 in range(self.m):
                self.flash_forgot[i,k2,0] = forgot
                self.update_measures(i,k2)
        else:
            self.flash_forgot[i,k,0] = forgot
            self.update_measures(i,k)
        
    def update_drop_free(self,i,peak,refused,forgot):
        [i1,i2,done_peak,k,positions] = self.drops[i][peak]
        if refused:
            self.data.drop_free[i][i1:i2] = self.treated[2-forgot][i][i1:i2]
            self.data.drop_free[0][i1:i2] = np.nanmean(self.data.drop_free[1:],axis=0)[i1:i2]
            self.update_measures(i,k)
        self.drops[i][peak][2] = forgot
                
    def update_measures(self,i,k):
        self.signal_updated[[0,0,i,i],[k,-1,k,-1]] = 0 # all plots to modify
        self.saved = False
        self.distribution_updated = False
        self.compute_measures(i,k)