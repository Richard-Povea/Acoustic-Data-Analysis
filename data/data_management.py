from pandas import Series, DataFrame, ExcelWriter
from io import BytesIO

def get_outliers(data:Series, k_factor:int=1.5)->Series:
    seventy_fifth = data.quantile(0.75)
    twenty_fifth = data.quantile(0.25)

    # Obtain IQR
    iqr = seventy_fifth - twenty_fifth

    # Upper and lower thresholds
    upper = seventy_fifth + (k_factor * iqr)
    lower = twenty_fifth - (k_factor * iqr)

    # Subset the dataset
    outliers = data[(data < lower) | (data > upper)]
    return outliers

def outliers_to_median(data:Series, outliers:Series=None)->Series:
    if not outliers:
        outliers = get_outliers(data)
    median = data.median()
    data.loc[outliers.index] = median
    return data

def export_data(df:DataFrame):
    buffer = BytesIO()
    with ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Vibration Summary')
        writer.close()
    return buffer
