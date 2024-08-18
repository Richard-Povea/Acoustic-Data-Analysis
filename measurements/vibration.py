from abc import ABC, abstractmethod
from numpy import sqrt
from pandas import DataFrame, read_csv, to_datetime
from re import search
from typing import Optional, List
from data.data_management import outliers_to_median
from documents.documents import BaseLine
from enum import Enum

class Axis(Enum):
    x_axis = 'X'
    y_axis = 'Y'
    z_axis = 'Z'
    pvs_axis = 'PVS'

class DataType(Enum):
    rion = 'Rion'

class FormatData(ABC):
    @property
    def data(self):
        return self.formatted_data()
    @abstractmethod
    def formatted_data(self,
                       weighted:Optional[bool]=True
                       )->DataFrame:
        """ 
        Returns a DataFrame representation of measurement data. 

        Columns are 'Start Time', 'X', 'Y', 'Z' and 'PVS'

        Returns:
            _type_: DataFrame
        """
        pass

class RionFormatter(FormatData):
    def __init__(self, data:DataFrame):
        self._original_data = data

    def formatted_data(
            self,
            weighted:Optional[bool]=True
            ) -> DataFrame:
        if weighted:
            axis = {
                'X':'X_APW',
                'Y':'Y_APW',
                'Z':'Z_APW'
                }
        else:
            axis = {
                'X':'X_AP',
                'Y':'Y_AP',
                'Z':'Z_AP'
                }
        data = self._original_data.copy()
        data['PVS'] = sqrt(data[axis['X']]**2 + 
                           data[axis['Y']]**2 + 
                           data[axis['Z']]**2)
        return data[['Start Time',
                     axis['X'],
                     axis['Y'],
                     axis['Z'],
                     'PVS']].rename(
                         columns={
                             axis['X']:'X',
                             axis['Y']:'Y',
                             axis['Z']:'Z',
                         }
                     )

    def __frequencies(self):
        #Implement this method to get frequency values
        pass

class MeasurementInfo(ABC):
    @abstractmethod
    def start_time():
        pass
    @abstractmethod
    def end_time():
        pass
    @abstractmethod
    def measurement_length():
        pass

class RionMeasurementInfo(MeasurementInfo):
    def __init__(self, data:DataFrame) -> None:
        self._data = data

    @property
    def start_time(self):
        return self._data['Start Time'].min()
    
    @property
    def end_time(self):
        return self._data['Start Time'].max()

    @property
    def measurement_length(self): 
        return self.end_time() - self.start_time()

class Summary:
    def __init__(self, 
                 formatted_data:FormatData):
        self._formatted_data = formatted_data
        self.data = formatted_data.data

    def peak(self):
        return self.data.loc[self.idxpeak()]

    def idxpeak(self):
        return self.data[['X',
                          'Y',
                          'Z']].idxmax()
    
    def idxmin(self):
        return self.data[['X',
                          'Y',
                          'Z']].idxmin()

    @property
    def data(self)->DataFrame:
        return self._data
    
    @data.setter
    def data(self, value:DataFrame):
        self._data = value

    def _non_outliers_axis(self,
                          data:DataFrame,
                          axis:Axis):
        non_outliers = outliers_to_median(data[axis.value])
        data.loc[
                non_outliers.index,
                Axis.x_axis.value
                ] = non_outliers

    def replace_outliers(self):
        """
        Replace outliers with the median values.

        Returns:
            _type_: Summary class
        """
        data = self.data.copy()
        self._non_outliers_axis(
            data=data,
            axis=Axis.x_axis
        )
        self._non_outliers_axis(
            data=data,
            axis=Axis.y_axis
        )
        self._non_outliers_axis(
            data=data,
            axis=Axis.z_axis
        )
        self._non_outliers_axis(
            data=data,
            axis=Axis.pvs_axis
        )
        self.data = data
        return self

    def pvs_by_interval(
            self,
            axis:Optional[Axis|List[Axis]]=None,
            interval:Optional[int]=1
            ):
        """
        Max value for the given interval.

        Parameters
        ----------
        Args:
            interval (Optional[int], optional):
                Number of seconds to calculate pvs value. 
                Defaults None return by interval of 1 second.
            axis (Optional[Axis|List[Axis]], optional):
                Specific axis to calculate pvs value. Defaults None return all Axis.

        Returns:
            _type_: DataFrame
        """
        data = self.data.copy()
        data['id'] = (data.index)//(interval*10)
        by_interval:DataFrame = data.groupby('id').max()[
            ['Start Time',
             'X', 
             'Y', 
             'Z']
             ]
        if axis == None:
            return by_interval
        elif isinstance(axis, Axis):
            return by_interval[
                ['Start Time',
                 axis.value
                 ]
                 ]
        else:
            raise ValueError(
                f"{self.interval} is not a valid axis."
                )
    
class Vibration(ABC):
    @abstractmethod
    def info(self):
        pass
    
    @abstractmethod
    def formatted_data(self):
        """ 
        Returns a DataFrame representation of measurement data. 

        Columns are 'Start Time', 'X', 'Y', 'Z' and 'PVS'

        Returns:
            _type_: DataFrame
        """
        pass

    @abstractmethod
    def file_number(self)->str:
        pass

class RionVibration(Vibration):
    def __init__(
            self,
            data_path:str
                ):
        self._data_path = data_path
        self._data = self._load_data(data_path)
        self.summary = Summary(self.formatted_data)

    def _load_data(self, data_path:str):
        data = read_csv(
            data_path,
            skiprows=1
            )
        data['Start Time'] = to_datetime(
            data['Start Time'],
            yearfirst=True
            )
        return data
    
    @property
    def info(self):
        return RionMeasurementInfo(self._data)
    
    @property
    def formatted_data(self):
        return RionFormatter(self._data)

    @property
    def file_number(self):
        return str(
            search(
                r'_(\d){4}_', self._data_path
                ).group()[1:-1])

class VibrationDirectory(Vibration):
    def __init__(self):
        self.children = {}

    def add(self, child:Vibration):
        self.children[child.file_number()] = child

class SENTRYVibrations(Vibration):
    def _load_data(self):
        # Implementación específica para cargar datos de archivos SENTRY
        print(f"Loading SENTRY data from {self.file_path}")

    def process_data(self):
        # Implementación específica para procesar datos de archivos SENTRY
        print("Processing SENTRY data...")
