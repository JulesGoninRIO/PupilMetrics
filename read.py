from pandas import read_table,read_csv
from matplotlib.pyplot import get_cmap
import numpy as np

class Reader:
    
    def __init__(self,data,file,machine):
        d_reader = {'NeuroLight':self.read_NeuroLight
                    ,'Diagnosys':self.read_Diagnosys,
                    'Neuroptics':self.read_Neuroptics}
        d_reader[machine](data,file)
    
    def read_NeuroLight(self,data,file):
        df = read_table(file)
        if file.name.split(' ')[1][:4] == 'DATA':
            data.raw += [[d/100 for d in df['DIAM']]]
            flashes = []
            ok = not data.color_names
            for i,col in enumerate(df['EVENT']):
                if col != ' ' and col != 'Black':
                    flashes += [i]
                    if ok:
                        data.color_names += [col]
                        i1,i2 = col.index('('),col.index(')')
                        data.color_codes += [get_cmap(col[:i1]+'s')(0.8-int(col[i1+1:i2])/200)]
                        data.is_strong += [int(col[i1+1:i2])<60]
            data.flash_times += [flashes]
            data.names += [file.name.split(' ')[0]]
        else:
            data.f = int(df['[PARAM]'][15][5:])
            eye = int(df['[PARAM]'][14][4:])
            data.eyes += [eye*'right'+(1-eye)*'left']
            data.dates += [df['[PARAM]'][1][5:]]
            data.hours += [df['[PARAM]'][2][5:]]

    def read_Diagnosys(self,data,file): 
        data.f = 100
        data.names += [file.name]
        df = read_table(open(file,encoding="utf-8",errors='ignore'),sep='\t')
        j2 = df.columns.get_loc('Data Table')
        ii,i = 4,0
        signal,flashes = [],[25]
        while type(df.iloc[ii,j2+1]) == type(''):
            if df.iloc[ii,j2+2] == '1':
                j = int(df.iloc[ii,j2+1])
                flashes += [flashes[-1]+i//10]
                i = 0
                ok = True
                while ok:
                    try:
                        int(df.iloc[i+2,j-1])
                        signal += [float(df.iloc[i+2,j])]
                    except:
                        ok = False
                    i += 10
            ii += 1
        data.raw += [signal]
        data.flash_times += [flashes[1:]]
        date = df.iloc[6,df.columns.get_loc('Header Table')+1]
        data.dates += [date[:date.index(' ')]]
        data.hours += [date[date.index(' ')+1:]]
        if not data.color_names:
            j1 = df.columns.get_loc('Stimulus Table')
            for i in range(int(df.iloc[7,1])-1):
                col = df.iloc[i+3,j1+1]
                data.color_names += [col]
                if ' ' in col:
                    i_ = col.index(' ')
                    if col[:i_:] in ['Red','Blue']:
                        col_ = col[:i_]+'s'
                    elif col[i_+1:] in ['Red','Blue']:
                        col_ = col[i_+1:]+'s'
                    else:
                        col_ = 'Greys'
                else:
                    col_ = 'Greys'
                col_intensity = float(df.iloc[i+3,j1+2]) # cd/m2
                data.color_codes += [get_cmap(col_)(0.65+np.log10(col_intensity)/10)]
                data.is_strong += [col_intensity>1]

    def read_Neuroptics(self,data,file): # load Neuroptics mouse Corinne data
        data.f = 31
        data.names += [file.name]
        df = read_csv(file,sep="\s+|\t",header=None,names=[i for i in range(1000)],engine='python')
        signal = []
        i = 30
        while df.iloc[i,2] != None:
            signal += [float(df.iloc[i,2])]
            i += 1
        data.raw += [signal]
        data.flash_times += [[16]]
        data.color_codes += [get_cmap('Greys')(0.25)]
        data.is_strong += [False]
        data.color_names = ['? flash ?']