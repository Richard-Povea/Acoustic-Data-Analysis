from abc import ABC, abstractmethod
from numpy import sqrt
from pandas import DataFrame, Series, Timestamp, read_csv, to_datetime
from re import search
from typing import Literal
from data.data_management import outliers_to_median
from documents.documents import BaseLine

def get_receiver_name(file_number:str, receivers_data:DataFrame):
        idx = receivers_data.isin((file_number,))
        return receivers_data[idx].dropna(axis=0, how='all').index.values[0]

class Vibrations(ABC):
    COLUMNS = ('Start Time', 'X_AP', 'Y_AP', 'Z_AP', 'PVS')
    def __init__(self, file_path, baseline:BaseLine):
        self.file_path = file_path
        self.baseline = baseline
        self._nonOutliersData = DataFrame()

    @property
    def receiver(self):
        return self.baseline.find_receiver_from_fileNumber(self.file_number)

    @property
    def start_time(self)->Timestamp:
        return self.process_data()['Start Time'].min()
    
    @property
    def period(self)->str:
        hour = self.start_time.hour
        if 7<hour and hour<21:
            return 'Diurno'
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
        non_outliers = self.process_data()
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
        ppvs = self.process_data()
        max_pvs = ppvs['PVS'].idxmax()
        return max_pvs

    @property
    @abstractmethod
    def file_number(self):
        """ Return the file number of the Vibrations object. """
        pass

    @abstractmethod
    def _load_data(self):
        """Método abstracto para cargar datos."""
        pass

    @abstractmethod
    def process_data(self)->DataFrame:
        """ 
        Returns a DataFrame representation of the measurement data. 

        Columns are 'Start Time', 'X_AP', 'Y_AP', 'Z_AP' and 'PVS'

        Returns:
            _type_: DataFrame
        """
        pass

class RIONVibrations(Vibrations):

    def __init__(self, file_path:str, baseline:BaseLine):
        super().__init__(file_path, baseline)
        self._data = self._load_data()
        self.summary = self.process_data()
    @property
    def file_number(self):
        return str(search(r'_(\d){4}_', self.file_path.name).group()[1:-1])

    def _load_data(self)->DataFrame:
        # Implementación específica para cargar datos de archivos RION
        data = read_csv(self.file_path, 
                        skiprows=1)
        data['Start Time'] = to_datetime(data['Start Time'],
                                 yearfirst=True)
        return data
    def process_data(self)->DataFrame:
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

    def __getitem__(self, key:Literal['X_AP', 'Y_AP', 'Z_AP'])->Series:
        return self._data[key]

class SENTRYVibrations(Vibrations):
    def _load_data(self):
        # Implementación específica para cargar datos de archivos SENTRY
        print(f"Loading SENTRY data from {self.file_path}")

    def process_data(self):
        # Implementación específica para procesar datos de archivos SENTRY
        print("Processing SENTRY data...")

