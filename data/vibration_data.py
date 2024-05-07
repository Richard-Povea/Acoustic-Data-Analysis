from pandas import DataFrame, Series, read_csv
from scipy.stats.mstats import winsorize
from numpy import sqrt
from typing import Literal
from .data_management import outliers_to_median

class RionFile:
    def __init__(self, filepath:str):
        self._data = read_csv(filepath, skiprows=1, parse_dates=['Start Time'])
        self._nonOutliersData = None

    def ppv(self):
        """_summary_

        Args:
            interval (int, optional): Interval time to calculate PPV. Defaults to 1 ms.

        Returns:
            _type_: DataFrame
        """
        self._data['fix'] = (self._data['Address']-1)//10
        ppvs:DataFrame = self._data.groupby('fix')[['Start Time', 'X_AP', 'Y_AP', 'Z_AP']]
        ppvs = ppvs.max()
        ppvs['PVS'] = sqrt(ppvs['X_AP']**2 + ppvs['Y_AP']**2 + ppvs['Z_AP']**2)
        return ppvs.rename(columns={'X_AP': 'X_PPV', 'Y_AP': 'Y_PPV', 'Z_AP':'Z_PPV'})
    
    def __getitem__(self, key:Literal['X_AP', 'Y_AP', 'Z_AP'])->Series:
        return self._data[key]
    
    @property
    def outliers_to_median(self):
        if self._nonOutliersData:
            return self._nonOutliersData
        non_outliers = self.ppv()
        non_outliers['X_PPV'] = outliers_to_median(data=non_outliers['X_PPV'])
        non_outliers['Y_PPV'] = outliers_to_median(data=non_outliers['Y_PPV'])
        non_outliers['Z_PPV'] = outliers_to_median(data=non_outliers['Z_PPV'])
        non_outliers['PVS'] = outliers_to_median(data=non_outliers['PVS'])
        self._nonOutliersData = non_outliers
        return non_outliers

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
