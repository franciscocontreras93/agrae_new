import numpy as np
import pandas as pd
import os

base_path = r'D:\GeoSIG\aGrae\Data'
file_name = 'TSM_2.csv'
file_path = os.path.join(base_path,file_name)

class aGraeTSM2():
    def __init__(self,file_path) -> None:
        self.df = pd.read_csv(file_path)
        self.df_eca2 = self.df[self.df['ECa2'] >= 0]
        self.df_eca4 = self.df[self.df['ECa4'] >= 0]

        pass

    def stats(self,field_name:str):
        df = self.df[self.df[field_name] >= 0]
        ts_min_max = [20,30]
        ts_media = (sum(ts_min_max ) / len(ts_min_max))
        stats = {
            'min' : df[field_name].min(),
            'max' : df[field_name].max(),
            'mean' : df[field_name].mean(),
            'arithmetic_mean' : (df[field_name].min() + df[field_name].max()) / 2,
            'median' : df[field_name].median(),
            'mode' : df[field_name].mode()[0],
            'std':  df[field_name].std(),
            'skewness_coef' : 3 * ( df[field_name].mean() - df[field_name].median() ) /  df[field_name].std(),
            'min-median_factor' : df[field_name].min() / df[field_name].median(),
            'max-median_factor' : df[field_name].max() / df[field_name].median(),
            'ts_media' : ( sum(ts_min_max ) / len(ts_min_max) ),    
            'mean_new_range' : self.median_new_range((3 * ( df[field_name].mean() - df[field_name].median() ) /  df[field_name].std()),ts_min_max),
            'adjust_factor' : df[field_name].median()/self.median_new_range((3 * ( df[field_name].mean() - df[field_name].median() ) /  df[field_name].std()),ts_min_max),
            'min_new_range': self.median_new_range((3 * ( df[field_name].mean() - df[field_name].median() ) /  df[field_name].std()),ts_min_max) * (df[field_name].min() / df[field_name].median()),
            'max_new_range': self.median_new_range((3 * ( df[field_name].mean() - df[field_name].median() ) /  df[field_name].std()),ts_min_max) * (df[field_name].max() / df[field_name].median())
        }

    

        return stats
    
    def median_new_range(self,coeficient,ts):
        if coeficient < 0: return ts[0] * abs(coeficient) + 1
        else: return ts[1] * abs(coeficient) + 1

    def slope(self,stats):
        x = np.array([stats['min'],stats['max']])
        y = np.array([stats['min_new_range'],stats['max_new_range']])
        
        stdv_x = np.sqrt(np.var(x))
        stdv_y = np.sqrt(np.var(y))

        sum_xy = sum((x-x.mean()) * (y-y.mean()))
        sum_x_sqr = sum((x-x.mean())**2)
        sum_y_sqr = sum((y-y.mean())**2)
        correlation = sum_xy / np.sqrt(sum_x_sqr * sum_y_sqr)
        slope = (stdv_y / stdv_x) * correlation
        if len(np.intersect1d(x,y)) > 0: intersection = np.intersect1d(x,y)[0] 
        else: intersection = 0

        
        
        return slope,intersection
    
    def calculate(self):
        stats_ECa2 = self.stats('ECa2')
        stats_ECa4 = self.stats('ECa4')
        slope_eca2,intersection_eca2 =  self.slope(stats_ECa2)
        slope_eca4,intersection_eca4 =  self.slope(stats_ECa4)

        self.df['CE01'] = self.df['ECa2'] * slope_eca2 + intersection_eca2
        self.df['CE02'] = self.df['ECa4'] * slope_eca4 + intersection_eca4

        # print(slope_eca4,intersection_eca4)
        # print(self.df)
        return self.df

    

    




    

    
# df = pd.read_csv(file_path)
# df_eca2 = df[df['ECa2'] >= 0]
# df_eca4 = df[df['ECa4'] >= 0]
# value = df_eca2['ECa2'].mode()
# eca4_min = df_eca2['ECa4'].min()

tool =  aGraeTSM2(file_path)
stats_ECa2 = tool.stats('ECa2')
stats_ECa4 = tool.stats('ECa4')
slope,intersect = tool.slope(stats_ECa4)

print(stats_ECa2)





df = tool.calculate()
# df.to_csv(os.path.join(base_path,'tsm_processed.csv'))


