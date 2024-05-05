from pandas import DataFrame, Series, read_csv
from scipy.stats.mstats import winsorize
from numpy import sqrt
from typing import Literal

class RionFile:
    def __init__(self, filepath:str):
        self.data = read_csv(filepath, skiprows=1, parse_dates=['Start Time'])

    def ppv(self, interval:int=1):
        """_summary_

        Args:
            interval (int, optional): Interval time to calculate PPV. Defaults to 1 ms.

        Returns:
            _type_: DataFrame
        """
        self.data['fix'] = (self.data['Address']-1)//10
        ppvs:DataFrame = self.data.groupby('fix')[['Start Time', 'X_AP', 'Y_AP', 'Z_AP']]
        ppvs = ppvs.max()
        ppvs['PVS'] = sqrt(ppvs['X_AP']**2 + ppvs['Y_AP']**2 + ppvs['Z_AP']**2)
        return ppvs.rename(columns={'X_AP': 'X_PPV', 'Y_AP': 'Y_PPV', 'Z_AP':'Z_PPV'})
    
    def __getitem__(self, key:Literal['X_AP', 'Y_AP', 'Z_AP'])->Series:
        return self.data[key]
    
    def outliers(self, k_factor:int=1.5):
        ppv = self.ppv()
        # Calculate the percentiles
        seventy_fifth = ppv['PVS'].quantile(0.75)
        twenty_fifth = ppv['PVS'].quantile(0.25)

        # Obtain IQR
        iqr = seventy_fifth - twenty_fifth

        # Upper and lower thresholds
        upper = seventy_fifth + (k_factor * iqr)
        lower = twenty_fifth - (k_factor * iqr)

        # Subset the dataset
        outliers = ppv[(ppv['PVS'] < lower) | (ppv['PVS'] > upper)]
        return outliers
    
    def reduce_outliers(self):
        """Change the outliers values for the median

        Returns:
            _type_: _description_
        """
        median_value = self.ppv()['PVS'].median()
        dataframe = self.ppv()
        dataframe.loc[self.outliers().index, ['X_PPV', 'Y_PPV', 'Z_PPV','PVS']] = median_value
        return dataframe

    @property
    def summary(self):
        ppvs = self.ppv()
        max_pvs = ppvs['PVS'].idxmax()
        return ppvs.loc[max_pvs]
    @property
    def describe(self):
        return self.ppv()['PVS'].describe()    
    @property
    def std(self):
        return self.ppv()['PVS'].std()

if __name__ == '__main__':
    print("Package main program")
