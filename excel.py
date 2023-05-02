from xlsxwriter import Workbook
import numpy as np 

class Excel(): # write and save data in .xlsx 
    def __init__(self,path,data): 
        self.workbook = Workbook(path)
        self.data = data
        (self.n,self.m,self.l) = np.shape(self.data.measures)
        self.fonts = []
        for col in self.data.color_codes:
            bg = ('#%02x%02x%02x'%(int(col[0]*255),int(col[1]*255),int(col[2]*255)))[1:]
            self.fonts += [self.workbook.add_format({'bg_color':bg,'bold':True}),
                        self.workbook.add_format({'bg_color':bg})]
        self.default,self.bold = self.workbook.add_format(),self.workbook.add_format({'bold':True})
        self.write_infos()
        sheet_mesures = self.workbook.add_worksheet('Measures')
        self.write_data('Data',-1)
        for k in range(self.m):
            self.write_data(self.data.color_names[k],k)
            self.write_measures(sheet_mesures,k)
        self.workbook.close()
        
    def write(self,sheet,j,i,x,font): # write x at data(j,i) if possible
        try: 
            sheet.write(j,i,x,font)
        except: 
            return
    
    def write_infos(self): # infos sheet
        sheet = self.workbook.add_worksheet('Infos')
        infos = [self.data.names[1:],self.data.eyes,self.data.dates,self.data.hours]
        infos_names = ['names','eye','date','hour']
        for i in range(len(infos)):
            self.write(sheet,0,i,infos_names[i],self.bold)
            for j in range(len(infos[i])):
                self.write(sheet,j+1,i,infos[i][j],self.default)
        
    def write_data(self,name,k): # flash k sheet
        sheet = self.workbook.add_worksheet(name)
        sheet.write(0,0,'time',self.bold)
        n0 = self.n+3
        for i in range(len(self.data.drop_free)):
            sheet.write(0,i+1,self.data.names[i],self.bold)
            sheet.write(0,i+n0,self.data.names[i]+' (fit)',self.bold)
            a,b = self.data.signal_range[i,k]
            pup = self.data.drop_free[i][a:b]
            fit = self.data.fitted[i][a:b]
            for j in range(len(pup)):
                if not i:
                    sheet.write(j+1,0,j/self.data.f,self.default)
                if k>-1 and j==self.data.flash_times[i][k]-a:
                    font = self.fonts[2*k+1]
                    sheet_d = self.workbook.get_worksheet_by_name('Data')
                    self.write(sheet_d,self.data.flash_times[i][k]+1,i+1,pup[j],font)
                    self.write(sheet_d,self.data.flash_times[i][k]+1,i+n0,fit[j],font)
                else:
                    font = self.default
                self.write(sheet,j+1,i+1,pup[j],font)
                self.write(sheet,j+1,i+n0,fit[j],font)
        
    def write_measures(self,paras,k): # measures sheet
        [font_bold,font] = self.fonts[2*k:2*(k+1)]
        measures = ['baseline','MCA','latency','6s constriction','dAMP','dLAT','dAUC']
        j0 = k*(self.l+2)
        paras.write(j0,0,self.data.color_names[k],font_bold)
        for j in range(len(measures)):
            paras.write(j0+j+1,0,measures[j],font_bold)
        for i in range(self.n):
            paras.write(j0,i+1,self.data.names[i],font_bold)
            for j in range(self.l):
                self.write(paras,j0+j+1,i+1,self.data.measures[i,k,j],font)