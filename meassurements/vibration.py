from abc import ABC, abstractmethod
from numpy import sqrt
from pandas import DataFrame, Series, Timestamp, read_csv
from re import search
from typing import Literal

class Vibrations(ABC):
    def __init__(self, file_path, receiver):
        self.file_path = file_path
        self.receiver = receiver
        self._nonOutliersData = DataFrame()
        self._load_data()

    @property
    @abstractmethod
    def file_number(self):
        """ Return the file number of the Vibrations object. """
        pass

    @property
    def start_time(self)->Timestamp:
        return self.process_data['Start Time'].min()

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

    def __init__(self, file_path:str, receiver:str):
        super().__init__(file_path, receiver)

    def file_number(self):
        return str(search(r'_(\d){4}_', self.filepath.name).group()[1:-1])

    def _load_data(self)->DataFrame:
        # Implementación específica para cargar datos de archivos RION
        return read_csv(self.filepath, skiprows=1, parse_dates=['Start Time'])

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

