from pandas import DataFrame, Series, Timestamp, read_csv
from numpy import sqrt
from typing import Literal
from .data_management import outliers_to_median
from re import search

class RionFile:
    def __init__(self, filepath:str):
        self._data = read_csv(filepath, skiprows=1, parse_dates=['Start Time'])
        self._nonOutliersData = DataFrame()
        self.file_name = str(search(r'_(\d){4}_', filepath.name).group()[1:-1])
        
    def __getitem__(self, key:Literal['X_AP', 'Y_AP', 'Z_AP'])->Series:
        return self._data[key]

    @property
    def ppv(self):
        """ 
        Returns a DataFrame representation of the measurement data. 

        Columns are 'Start Time', 'X_AP', 'Y_AP', 'Z_AP' and 'PVS'

        Returns:
            _type_: DataFrame
        """
        self._data['fix'] = (self._data['Address']-1)//10
        ppvs:DataFrame = self._data.groupby('fix')[['Start Time', 'X_AP', 'Y_AP', 'Z_AP']]
        ppvs = ppvs.max()
        ppvs['PVS'] = sqrt(ppvs['X_AP']**2 + ppvs['Y_AP']**2 + ppvs['Z_AP']**2)
        return ppvs.rename(columns={'X_AP': 'X_PPV', 'Y_AP': 'Y_PPV', 'Z_AP':'Z_PPV'})
    
    @property
    def start_time(self)->Timestamp:
        return self._data['Start Time'].min()
    
    @property
    def period(self)->str:
        hour = self.start_time.hour
        if 7<hour and hour<21:
            return 'Diurno'
        else:
            return 'Nocturno'

    @property
    def outliers_to_median(self):
        """
        Replace outliers with median values for

        Returns:
            _type_: DataFrame with outliers replaced by median values
        """
        if not self._nonOutliersData.empty:
            return self._nonOutliersData
        non_outliers = self.ppv()
        non_outliers['X_PPV'] = outliers_to_median(data=non_outliers['X_PPV'])
        non_outliers['Y_PPV'] = outliers_to_median(data=non_outliers['Y_PPV'])
        non_outliers['Z_PPV'] = outliers_to_median(data=non_outliers['Z_PPV'])
        non_outliers['PVS'] = outliers_to_median(data=non_outliers['PVS'])
        self._nonOutliersData = non_outliers
        return non_outliers

    @property
    def max_pvs(self)->Series:
        """

        Returns:
            _type_: Series with the maximum value of the measurement.
        """
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
