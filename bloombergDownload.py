"""
Download data from Bloomberg and copy on file
First, you will need to install TIA: just type 'pip install tia' on cmd 
prompt
"""

import numpy as np
import pandas as pd

def SaveToFile(securities=False):
    # Choose the key parameters
    start = '1/1/2000'
    end = '10/31/2017'
    if not securities:
        securities = [ 
                'EUSA10 Index', 
                'USSW10 Index',
                'BPSW10 Index',
                'ASWABUND Index', 
                'ASWABOBL Index',
                'ASWASHTZ Index',
                'ASWEBUND Index', 
                'ASWEBOBL Index',
                'ASWESHTZ Index',
                'TYAISP Comdty', 
                'SX5E Index', 
                'SX7E Index', 
                'SPX Index',
                'DAX Index', 
                'UKX Index',
                'VIX Index', 
                'V2X Index', 
                'EONIA Index', 
                'EUSWEC Index', 
                'EURUSD Curncy', 
                'EURGBP Curncy',
                'GBPUSD Curncy',
                'AUDUSD Curncy',
                'AUDNZD Curncy', 
                'JPY Curncy',
                'EUR003M Index', 
                'EUSA2 Index',
                'ER1 Comdty', 
                'ER2 Comdty', 
                'ER3 Comdty', 
                'ER4 Comdty', 
                'ER5 Comdty', 
                'ER6 Comdty', 
                'ER7 Comdty', 
                'ER8 Comdty', 
                'NFP TCH Index',
                'CPURNSA% Index',
                'ECCPEMUM Index',
                ]
    
    # Load and pre-process the data
    import tia.bbg.datamgr as dm
    mgr = dm.BbgDataManager()
                
    levels_df = mgr[securities].get_historical('PX_LAST', start, end)
    levels_df.to_csv('dataDump.csv')
    
    return (levels_df)

