from pandas import DataFrame, merge, read_excel
from enum import Enum
from typing import Literal, Optional, List
from streamlit.runtime.uploaded_file_manager import UploadedFile

class NotFilesError(Exception):
    pass
class FileNotFoundError(Exception):
    pass

class SheetName(Enum):
    PROJECT = "DATOS"
    INFO = "Información"
    VIB_DAY = "VIBRACIÓN - Diurno"
    VIB_NIGHT = "VIBRACIÓN - Nocturno"
    NOISE_DAY = "RUIDO - Diurno"
    NOISE_NIGHT = "RUIDO - Nocturno"

#Get the list of receivers from a excel file
def get_receivers_path(uploaded_files:List[UploadedFile]|None):
    if not uploaded_files:
        raise NotFilesError(f'No files were uploaded')
    receivers_path = [file for file in uploaded_files if file.name.endswith('.xlsx')]
    if receivers_path.__len__() == 0:
        raise FileNotFoundError('File with extension ".xlsx" cannot be found')
    return receivers_path[0]

def get_sheet_name(measurement:Literal['Vibration', 'Noise']):
    if measurement=='Noise':
        return SheetName.NOISE_DAY.value, SheetName.NOISE_NIGHT.value
    if measurement=='Vibration':
        return SheetName.VIB_DAY.value, SheetName.VIB_NIGHT.value

class BaseLine:
    INDEX_NAME = 'Receivers'
    RECEIVERS_COL = 'A'
    MEMORIES_COL = 'E'
    def __init__(self, path:str, 
                 receivers_col:Optional[str]=None, 
                 memories_col:Optional[str]=None):
        self.path = path
        self._receivers = None
        self._modify_columns(receivers_col, memories_col)
    
    def _modify_columns(self, receivers_col:str|None, memories_col:str|None):
        if receivers_col:
            self.RECEIVERS_COL = receivers_col
        if memories_col:
            self.MEMORIES_COL = memories_col

    def _read_data(self, sheet_name:SheetName)->DataFrame:
        return read_excel(self.path, 
                          sheet_name, 
                          index_col=0, 
                          usecols="{},{}".format(self.RECEIVERS_COL,
                                                 self.MEMORIES_COL))
    
    def _merge_data(self, measurement:Optional[Literal['Vibration', 'Noise']]='Vibration')->DataFrame:
        day_sheetName, night_sheetName = get_sheet_name(measurement)
        day:DataFrame = self._read_data(day_sheetName).dropna()
        night:DataFrame = self._read_data(night_sheetName).dropna()
        day.index.name = self.INDEX_NAME
        if not night.size:
            return day.set_index(self.INDEX_NAME)
        receivers = merge(day, 
                          night, 
                          left_index=True, 
                          right_index=True).rename(columns={"Memoria_x":"Diurno",
                                                            "Memoria_y":"Nocturno"})
        receivers['Diurno'] = receivers['Diurno'].apply(lambda x: str(int(x)).zfill(4))
        receivers['Nocturno'] = receivers['Nocturno'].apply(lambda x: str(int(x)).zfill(4))
        return receivers
    
    @property	
    def receivers(self):
        if not isinstance(self._receivers, DataFrame):
            self._receivers = self._merge_data()
            return self._receivers
        return self._receivers
        
    @property
    def receivers_as_dict(self):
        return self.receivers['Diurno'].to_dict(), self.receivers['Nocturno'].to_dict()

    def find_receiver_from_fileNumber(self, fileNumber: int|str):
        try:
            idx = self.receivers.isin((fileNumber,))
            return self.receivers[idx].dropna(axis=0, how='all').index.values[0]    
        except IndexError:
            return None

class Receiver:
    def __init__(self,name:str):
        self.name = name
        self._day_file_number = None
        self._night_file_number = None

class VibrationLB:
    def __init__(self, base_line:BaseLine):
        self.base_line = base_line
