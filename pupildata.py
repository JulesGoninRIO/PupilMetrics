import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import fmin
from pathlib import Path
import read # pupillometry code

class PupilData:

    def __init__(self,folder_path,machine,process_state,settings):
        process_state[0],process_state[1] = 'Treating: ','start'
        self.settings,self.folder_path,self.machine = settings,folder_path,machine
        self.errors = ['','']
        self.names,self.eyes,self.dates,self.hours = ['Average of recordings'],[],[],[]
        self.color_names,self.color_codes,self.is_strong = [],[],[]
        self.raw,self.flash_times = [],[]
        for file in Path(folder_path[:-1]).glob('*'):
            try:
                read.Reader(self,file,machine)
                if self.flash_times and len(self.flash_times[0])!=len(self.flash_times[-1]):
                    raise Exception('flash number different from 1st recording')
            except Exception as err:
                self.errors[0] += str(file)[len(folder_path):]+'\n'
                self.errors[1] += '{} -- {}\n'.format(str(file)[len(folder_path):],err)
        self.folder_path_name = folder_path[-folder_path[::-1][1:].index('/')-1:-1] 
        length = [len(signal) for signal in self.raw]
        for i in range(len(self.raw)): # delete big outliers points
            for j in range(max(length)):
                if j<length[i]:
                    if self.raw[i][j]>10 or self.raw[i][j]<0.2: # keep pupil size between 0.2-10mm
                        self.raw[i][j] = np.nan
                else:
                    self.raw[i] += [np.nan]
                
    def interpolate(self,signal_0): # linear interpolation, complete begin/end with first/last value
        signal = np.copy(signal_0)
        t,t_nan = 0,0
        n = len(signal)
        while t < n:
            if np.isnan(signal[t]):
                while t<n-1 and np.isnan(signal[t]):
                    t += 1
                if t_nan == 0:
                    signal[:t] = signal[t]
                elif t == n-1:
                    signal[t_nan:] = signal[t_nan]
                else :
                    a = (signal[t]-signal[t_nan])/(t-t_nan)
                    signal[t_nan:t] = [signal[t_nan]+a*x for x in range(t-t_nan)]
            else:
                t_nan = t
            t += 1
        return signal

    # treat signal from main artefacts using acceleration/speed detection
    def no_artefact(self):
        (n,m) = np.shape(self.flash_times)
        mouse = 2*self.machine=='Neuroptics' # adapt threshold to mouse pupil size
        A_max = self.settings[0]*30/self.f**2/(1+mouse) # acceleration threshold 90 mm/s^2
        V_max = self.settings[0]*2/self.f/(1+mouse) # speed threshold : 6 mm/s
        t_flash1,t_flash2 = int(1.2*self.f),int(3.3*self.f) # times to be specific after flash : 1.5-3.3s
        t_line_max = self.f//8 # time to detect line signal (acc=0) : 0.125s
        self.artefact_free = []
        for i in range(n): # for every recording
            signal = np.copy(self.raw[i])
            self.fill(signal) # interpolation for not complete recording
            speed = np.gradient(signal)
            acc = np.gradient(speed)
            flash,k = self.flash_times[i][0],0 # flash,index of flash 
            t_line = 0 # count line signal length
            for t in range(len(signal)):
                if acc[t] == 0:
                    t_line += 1
                else:
                    t_line = 0
                if abs(acc[t]) > A_max or abs(speed[t]) > V_max: # non biological pupil movement
                    signal[t] = np.nan
                if t_line > t_line_max : # line signal too long is artefact
                    signal[t-t_line:t] = np.nan
                if t > flash+t_flash1:
                    if t < flash+t_flash2:
                        if acc[t] < -A_max/4 and speed[t] < V_max/2 and not mouse: 
                            signal[t] = np.nan # specific shape recovery
                    elif k < m-1:
                        k += 1
                        flash = self.flash_times[i][k]
            for k,flash in enumerate(self.flash_times[i]):
                if self.is_strong[k]: # avoid cutting the contraction for strong stimuli/contraction
                    signal[flash-int(0.25*self.f):flash] = self.raw[i][flash-int(0.25*self.f):flash]
            self.artefact_free += [self.fill(signal)] # interpolation

    # complete artefact detection from removed points and interpolate signal 
    def fill(self,signal):
        t_btw = self.f//4 # range between detected points to interpolate : 0.25s
        n = len(signal)
        for K in [8,4,2,1]: # iterate with increasing t_btw 
            artefact = True # state True if we are in an artefact
            t_nan = 0 # index of artefact begin 
            for t in range(n):
                if not artefact:
                    if np.isnan(signal[t]):
                        t_nan = t
                        artefact = True
                elif t<t_nan+t_btw/K or t>n-t_btw/K:
                    if np.isnan(signal[t]):
                        signal[t_nan:t] = np.nan 
                        t_nan = t
                else:
                    artefact = False
        return self.interpolate(signal) # linear interpolation

    # fit custom pupil curve to recording artefact_free by acceleration detection
    # run is quite long, ~1-2s per recording: n_flash*~100tries*(~30*end_signal()+fit~300points)
    def fit_signal(self,process_state):
        self.fitted = []
        (n,m) = np.shape(self.flash_times)
        for i in range(n): # for every recording
            signal = self.artefact_free[i]
            process_state[1] = str(i+1)+'/'+str(n) # update pupil loading text
            fitted_signal = np.zeros(len(signal))
            tf = int(0.25*self.f) # delay added for pupil reaction and drop begin
            for k in range(m): # for every flash
                flash = self.flash_times[i][k]+tf
                if k-m+1:
                    imax = self.flash_times[i][k+1]+tf
                else: 
                    imax = len(signal)
                base_diam = np.mean(signal[flash-2*tf:flash]) # base diameter around flash
                if not k: # complete first seconds of recording
                    fitted_signal[:flash] = base_diam
                end_diam = np.mean(signal[imax-2*tf:imax]) # base diameter around next flash
                min_diam = np.min(signal[flash:flash+3*self.f]) # diameter of the peak
                t_min = np.argmin(signal[flash:flash+3*self.f])+flash # latency index of the peak
                def f_signal(exp,t1,t2): # return fit with parameter exp between t1-t2
                    drop = 1+0.2*exp[0] # exponent drop variation formula
                    rec = 1.5**(-exp[1]) # exponent recovery variation formula
                    S = (base_diam-min_diam)/abs(flash-t_min)**drop # constant for diameter
                    T = (imax-2*tf-t_min)**rec # constant for end time
                    def end_signal(t): # compute difference between fit and end_diam for switch shape time t
                        t_d,t_r = t**drop,t**rec
                        return abs(S*(drop/rec*t_d/t_r*(T-t_r)+t_d)+min_diam-end_diam)
                    t0 = fmin(end_signal,self.f//3,disp=False,ftol=0.01,xtol=0.01) # switch shape time found
                    K = drop/rec*t0**(drop-rec) # constant for derivative continuity at t0
                    C = t0**drop-K*t0**rec # constant for continuity at t0
                    def f_signal_t(t): # return fit depending time section 
                        if t < flash: # baseline
                            return base_diam
                        elif t < t_min+t0 : # drop
                            return S*abs(t-t_min)**drop+min_diam   
                        else : # recovery after t0
                            return S*(K*(t-t_min)**rec+C)+min_diam 
                    return [f_signal_t(t) for t in range(t1,t2)]
                i1,i2 = max(t_min-self.f,flash),min(t_min+3*self.f,imax) # time range to fit around t_min
                def e_signal(exp): # compute difference between fit try and recording
                    return np.sum(np.square((f_signal(exp,i1,i2)-signal[i1:i2])))
                exp = fmin(e_signal,[3,15],disp=False,maxfun=100*self.settings[2]**2) # exponents found 
                fitted_signal[flash-2*tf:imax] = f_signal(exp,flash-2*tf,imax) # fill fit curve
            self.fitted += [fitted_signal]
    
    # treat signal from non-steep artefacts from artefact_free signal and fit 
    # detect on purpose too many drops and register them in drops for the user to choose in the GUI
    def no_drop(self):
        (n,m) = np.shape(self.flash_times)
        self.drop_free,self.drops = [],[]
        for i in range(n): # for every recording
            signal = self.artefact_free[i]
            diff = [self.fitted[i][0]-signal[0]]
            for e in (self.fitted[i][1:]-signal[1:]):
                diff += [0.1*e+0.9*diff[-1]] # smooth filtered difference between fit and recording
            signal_drop = np.copy(signal)
            section = np.ones(len(signal)) # index where drops can be detected
            for flash in self.flash_times[i]:
                section[flash:flash+2*self.f] = 0 # prevent detecting drop at the pupil peak contraction
            peaks_0,sizes = find_peaks(diff,prominence=0.05) # finds peaks in diff higher than 0.05mm
            peaks = [['','',-1]] # list of peaks (['','',-1] for initialisation)
            for peak in peaks_0:
                if section[peak]:
                    i1,i2 = peak,peak # range index that increase around the peak while the drop is regular
                    while i1>1 and section[i1] and diff[i1-1]<=diff[i1]:
                        i1 -= 1
                    while i2<len(signal)-2 and section[i2] and diff[i2+1]<=diff[i2]:
                        i2 += 1
                    signal_drop[i1:i2] = (i2-i1)*[np.nan] # drop remove
                    if np.sum(np.square(self.interpolate(signal_drop[i1-1:i2+1])-signal[i1-1:i2+1])) > self.f/30/self.settings[1]: 
                        if i1 <= peaks[-1][2]: # group overlapping drops
                            peaks[-1][2] = i2 
                        else: # drop big enough 
                            peaks += [[i1,peak,i2]] # peak,indexs around 
                    else:
                        signal_drop[i1:i2] = signal[i1:i2]
            self.drop_free += [self.interpolate(signal_drop)] # interpolation
            self.drops += [peaks[1:]]
