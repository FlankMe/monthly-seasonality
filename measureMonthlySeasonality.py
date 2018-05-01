"""
Rudimentary analysis of seasonal patterns in indices/time series.
For other series, just modify the variables: securities, START, END, and target. 

It assumes that the file dataDump.csv is already in the folder.
If it cannot find the data it needs, it runs the script bloombergDownload.py 
which can be found on
https://github.com/FlankMe/monthly-seasonality/blob/master/bloombergDownload.py

@author: Riccardo Rossi
"""

import numpy as np
import pandas as pd
from scipy import stats


# Primary settings
fromFile = 'dataDump.csv'
securities = ['ASWABUND Index', 'ASWABOBL Index', 'ASWASHTZ Index']
START = '2007-02-01'
END = '2017-10-31'
SIGNIFICANCE = 0.20     # Relevant for statistical tests
TrimmedMeansThresholds = [0, 10, 25, 50]


# /------------------------------------------------------------------/
# SUPPORTING FUNCTIONS, SCROLL DOWN TO THE MAIN SCRIPT
# /------------------------------------------------------------------/
      
def loadData(START, END, fromFile, securities=[]):
    try:
        assert fromFile, "Unspecified CSV file to load data from"
        RawData = pd.DataFrame.from_csv(fromFile).astype(float)
        RawData = RawData.loc[pd.date_range(START, END, freq='B')]
        if securities:
            RawData = RawData[securities]
    except: 
        import bloombergDownload
        RawData = bloombergDownload.SaveToFile(securities).astype(float).loc[
            pd.date_range(START, END, freq='B')]
    
    return RawData
    

def dropObservations(RawData, years, MonthsInScope, DaysInScope):
  
    for year in years:
        for month in MonthsInScope:
            startFutureRoll, endFutureRoll = DaysInScope
            StartingDateToDrop = str(year)+month+startFutureRoll
            EndingDateToDrop = str(year)+month+endFutureRoll
            IndicesToDrop = RawData[StartingDateToDrop : EndingDateToDrop].index
            RawData = RawData.drop(IndicesToDrop)
    return RawData


def sumUpChangesWithinRanges(RawData, years, months):
    
    # Construct a data frame of years x months, pre-filled with nan values
    changes_perYear_perMonth = pd.DataFrame(data=np.ones(shape=(len(years), 
                                                                len(months))),
                                            index=years,
                                            columns=months) * np.nan

    # Sum up the absolute changes and fill the years x months data frame
    for year in years:
        for month in months:
            rangeToInspect = ((RawData.index.year == year) & 
                              (RawData.index.month == month))
            measuredChange = RawData[rangeToInspect].sum()
            
            # Only trascript the amount if it exists, otherwise leave NaN                                        
            if measuredChange: 
                changes_perYear_perMonth[month][year] = measuredChange
    
    return changes_perYear_perMonth


def calculateMonthlyAverageChanges(changes_perYear_perMonth, TrimmedMeansThresholds):
    # Calculate the monthly means for differently trimmed datasets
  
    # Define the data frames that will host the monthly changes 
    MonthlyAverageChanges = pd.DataFrame(index=changes_perYear_perMonth.columns)

    for threshold in TrimmedMeansThresholds:

        # Calculate the threshold amounts for each %-threshold of the data 
        lowPercentile, highPercentile = [], []
        for month in months:

            changesInSpecificMonth = changes_perYear_perMonth[month].values
            validEntriesInSpecificMonth = ~np.isnan(changesInSpecificMonth)

            lowPercentile.append(np.percentile(changesInSpecificMonth[validEntriesInSpecificMonth], 
                                               threshold))
            highPercentile.append(np.percentile(changesInSpecificMonth[validEntriesInSpecificMonth], 
                                                100 - threshold))
        
        lowestAmount = np.array(lowPercentile) * np.ones(changes_perYear_perMonth.shape)
        highestAmount = np.array(highPercentile) * np.ones(changes_perYear_perMonth.shape)
           
        # Save the trimmed data  
        dataInScope = ((changes_perYear_perMonth >= lowestAmount) 
                       & (changes_perYear_perMonth <= highestAmount))
        TrimmedChanges_perYear_perMonth = changes_perYear_perMonth[dataInScope]
        category = str(threshold)+'% Trimmed Mean'
        MonthlyAverageChanges[category] = TrimmedChanges_perYear_perMonth.mean()
    
    # Best to include the median (or 50% trimmed mean) manually to avoid data loss
    medianChangeIsRequired = (50 in TrimmedMeansThresholds)
    if medianChangeIsRequired:
        MonthlyAverageChanges['50% Trimmed Mean'] = changes_perYear_perMonth.median()
    
    # Improve formatting of the results
    MonthlyAverageChanges = np.round(MonthlyAverageChanges, 3)
    
    return MonthlyAverageChanges


def calculatePValues(changes_perYear_perMonth):

    # Define the data frames that will host the p-values
    PValues = pd.DataFrame(index=changes_perYear_perMonth.columns)
    validEntries = ~np.isnan(changes_perYear_perMonth.values)

    # To test for the mean, calculate the t-statistic and two-tailed p-value
    mean = changes_perYear_perMonth.values[validEntries].mean()
    std = changes_perYear_perMonth.std() / np.sqrt(changes_perYear_perMonth.count())
    TStatisticInVector = (changes_perYear_perMonth.mean() - mean) / std
    OneTailedPValue = stats.t.sf(np.abs(TStatisticInVector), 
                                 changes_perYear_perMonth.count() - 1)
    TwoTailedPValue = OneTailedPValue * 2
    PValues['Mean t-test p-value'] = TwoTailedPValue
    
    # To test for the median, calculate the Wilcoxon stat and two-tailed p-value
    wilcoxonInVector = []
    median = np.median(changes_perYear_perMonth.values[validEntries])
    for month in months:
        validEntriesInSpecificMonth = ~np.isnan(changes_perYear_perMonth[month].values)
        change = changes_perYear_perMonth[month].values[validEntriesInSpecificMonth] 
        wilcoxonInVector.append(stats.wilcoxon(change - median)[1])

    PValues['Median Wilcoxon p-value'] = np.array(wilcoxonInVector)
    return PValues


def plotResults(MonthlyAverageChanges, title):

    import matplotlib.pyplot as plt
    months_in_char = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    validEntries = ~np.isnan(changes_perYear_perMonth.values)
    median = np.median(changes_perYear_perMonth.values[validEntries])
              
    plt.figure(figsize=(12,7.4))
    plt.plot(np.ones(len(MonthlyAverageChanges.index)+1) * 0, 'k--')
    plt.plot(np.ones(len(MonthlyAverageChanges.index)+1) * median, 'r+', label='Overall Median')

    for i in range(len(MonthlyAverageChanges.columns)):
        degreeOfDarkness = (i+1.0) / len(MonthlyAverageChanges.columns)
        plt.plot(MonthlyAverageChanges[MonthlyAverageChanges.columns[i]], 
                 'b', alpha=degreeOfDarkness)

    plt.xticks(MonthlyAverageChanges.index, months_in_char)
    maxY = max(abs(MonthlyAverageChanges.values.min()), 
               abs(MonthlyAverageChanges.values.max()))
    plt.ylim((-maxY,maxY))

    plt.legend(loc="best")
    plt.title(title)
    plt.show()

def printPValuesInImprovedFormat(PValues, significance):
    
    # Rename the months and print the results 
    months_in_char = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    PValues.index = months_in_char

    PValues = np.round(PValues, 2).astype(str)                                                  
    
    # Highlight the p-values that pass the test
    for column in PValues.columns:
        for row in PValues.index:
            existingValue = PValues[column][row]
            if float(existingValue) <= significance: 
                PValues[column][row] = '**' + existingValue
    
    print  PValues    
    
def countPercentageOfSignals(PValues, significance):

    numberOfSignals = (PValues < significance).sum().sum()
    percOfSignals = float(numberOfSignals) / PValues.count().sum()
    percOfSignals = np.round(percOfSignals, 3)     # improving print format

    print 'Seasonalities at', significance*100, \
      '% significance level are detected', percOfSignals*100, '% times'

def calculateConfidenceIntervals(changes_perYear_perMonth):

    confidenceIntervals = pd.DataFrame(index=months)

    minimum = changes_perYear_perMonth.min()
    maximum = changes_perYear_perMonth.max()
    mean = changes_perYear_perMonth.mean()
    std = changes_perYear_perMonth.std()

    confidenceIntervals['Min'] = minimum
    confidenceIntervals['Mu-1s'] = mean - std
    confidenceIntervals['Mu+1s'] = mean + std
    confidenceIntervals['Max'] = maximum
    
    return confidenceIntervals 

      
# /------------------------------------------------------------------/
# MAIN SCRIPT
# /------------------------------------------------------------------/
    
# Load data and define the target series
RawData = loadData(START, END, fromFile, securities)

target = RawData['ASWABUND Index']
RawData = target
RawData = RawData.dropna().diff().dropna()
RawData.index = pd.to_datetime(RawData.index)
years = np.unique(RawData.index.year)
months = range(1,13)

# Settings on dropping data
ShouldDropDataAroundFutureRoll = True
MonthsOfFutureRoll = ['-03-', '-06-', '-09-', '-12-']
DaysStartAndEndOfFutureRoll = ['06', '10']

# Drop the data of changes around the futures rolls
# Alternatively, one could adjust manually for the roll
if ShouldDropDataAroundFutureRoll:
    RawData = dropObservations(RawData, 
                               years, 
                               MonthsOfFutureRoll, 
                               DaysStartAndEndOfFutureRoll)

changes_perYear_perMonth = sumUpChangesWithinRanges(RawData, years, months)

MonthlyAverageChanges = calculateMonthlyAverageChanges(changes_perYear_perMonth, 
                                                       TrimmedMeansThresholds)

PValues = calculatePValues(changes_perYear_perMonth)

chartTitle = 'Monthly average moves for progressively trimmed data series'
plotResults(MonthlyAverageChanges, chartTitle)

confidenceIntervals = calculateConfidenceIntervals(changes_perYear_perMonth)
printPValuesInImprovedFormat(PValues, SIGNIFICANCE)
countPercentageOfSignals(PValues, SIGNIFICANCE)
