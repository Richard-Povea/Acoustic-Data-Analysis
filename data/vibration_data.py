from pandas import DataFrame, read_csv
from numpy import sqrt

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
        ppvs:DataFrame = self.data.groupby('fix')[['Start Time', 'X_AP', 'Y_AP', 'Z_AP']].max()
        ppvs['PVS'] = sqrt(ppvs['X_AP']**2 + ppvs['Y_AP']**2 + ppvs['Z_AP']**2)
        return ppvs.rename(columns={'X_AP': 'X_PPV', 'Y_AP': 'Y_PPV', 'Z_AP':'Z_PPV'})
    
    @property
    def summary(self):
        ppvs = self.ppv()
        max_pvs = ppvs['PVS'].idxmax()
        return ppvs.loc[max_pvs]

if __name__ == '__main__':
    print("Package main program")
