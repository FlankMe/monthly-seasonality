"""
Created on Sun Nov  5 18:53:46 2017

Rudimentary analysis of seasonal patterns in indices/time series.
For other series, just modify the target series, START, and END variables. 

It assumes that the file dataDump.csv is already in the folder.
Alternatively, it runs the script bloombergDownload.py to be found on
https://github.com/FlankMe/monthly-seasonality/blob/master/bloombergDownload.py

@author: Riccardo
"""

import numpy as np
import pandas as pd
from scipy import stats
import time; np.random.seed(int(time.time()))

# Load the relevant data 
START = '2007-02-01'
END = '2017-10-31'
securities = ['ASWABUND Index', 'ASWABOBL Index', 'ASWASHTZ Index']
SIGNIFICANCE = 0.10
try:
    df = pd.DataFrame.from_csv('dataDump.csv').astype(float).loc[
        pd.date_range(START, END, freq='B'), securities]
except: 
    import bloombergDownload
    df = bloombergDownload.SaveToFile(securities).astype(float).loc[
        pd.date_range(START, END, freq='B')]

# Define the target series and calculate the differences  
df = df['ASWABUND Index']
df = df.dropna().diff().dropna()
df.index = pd.to_datetime(df.index)
yRange = np.unique(df.index.year)
mRange = range(1,13)
xTicks = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# OPTIONAL: Drop the data of changes around the futures rolls
# Alternatively, one could adjust manually for the roll
if True:
    for y in yRange:
        for m in ['-03-', '-06-', '-09-', '-12-']:
            df = df.drop(df[str(y)+m+'06':str(y)+m+'10'].index)

# Construct a data frame of years x months, pre-filled with nan values
yearsXmonths_df = pd.DataFrame(data=np.ones(shape=(len(yRange), len(mRange))),
                           index=yRange,
                           columns=mRange) * np.nan
                              
# Sum up the absolute changes and fill the years x months data frame
for y in yRange:
    for m in mRange:
        change = df[(df.index.year == y) & 
                               (df.index.month == m)].sum()
        if change: 
            yearsXmonths_df[m][y] = np.round(change, 2)

# Create the data frames that will contain the info about monthly changes
trimmed_means_df = pd.DataFrame(index=mRange)
p_value_df = pd.DataFrame(index=mRange)

## Print histograms of the monthly changes
#yearsXmonths_df.hist(figsize=(12,12), sharex=True, sharey=True, bins=5)

''' 
Calculate the means and exclude the outliers
This part is somewhat subjective, so feel free to modify the code to the 
method you find most satisfactory.
'''
trimmed_means_df['0% Trimmed Mean'] = np.round(yearsXmonths_df.mean(), 3)

for p in [10, 25]:
    # Calculate the thresholds for the p-trimmed data frame
    threshold_low = np.array([np.percentile(yearsXmonths_df[m].values[
        ~np.isnan(yearsXmonths_df[m].values)], p) 
        for m in mRange]) * np.ones(yearsXmonths_df.shape)
    threshold_high = np.array([np.percentile(yearsXmonths_df[m].values[
        ~np.isnan(yearsXmonths_df[m].values)], 100 - p) 
        for m in mRange]) * np.ones(yearsXmonths_df.shape)
                    
    # Save the data frame with the data without the extreme values    
    temp_YxM_df = yearsXmonths_df[(yearsXmonths_df >= threshold_low) &
                                 (yearsXmonths_df <= threshold_high)]
    trimmed_means_df[str(p)+'% Trimmed Mean'] = np.round(temp_YxM_df.mean(), 3)

trimmed_means_df['50% Trimmed Mean'] = np.round(yearsXmonths_df.median(), 3)

# Test whether the seasonal pattern is statistically significant 

# To test for the mean, calculate the t-statistic and two-tailed p-value
mean = yearsXmonths_df.values[~np.isnan(yearsXmonths_df.values)].mean()
t_statistic = (yearsXmonths_df.mean() - mean) / ( 
    yearsXmonths_df.std() / np.sqrt(yearsXmonths_df.count()) )
p_value_df['Mean t-test p-value'] = np.round(stats.t.sf(
    np.abs(t_statistic), yearsXmonths_df.count() - 1) * 2, 3)

# To test for the median, calculate the Wilcoxon stat and two-tailed p-value
median = np.median(yearsXmonths_df.values[~np.isnan(yearsXmonths_df.values)])
p_value_df['Median Wilcoxon p-value'] = np.array([np.round(stats.wilcoxon(
    yearsXmonths_df[m].values[~np.isnan(yearsXmonths_df[m].values)] - median)
    [1], 3) for m in mRange])

# Count the signals at a specific significance level
percSignal = ((p_value_df < SIGNIFICANCE).sum().sum() / 
            float(p_value_df.count().sum()))

# Highlight the p-values that pass the test
for c in p_value_df.columns:
    for r in p_value_df.index:
        if p_value_df[c][r] <= SIGNIFICANCE: 
            p_value_df[c][r] = '**' + str(p_value_df[c][r])
            
# Plot the differently trimmed monthly means
import matplotlib.pyplot as plt
plt.figure(figsize=(12,7.4))
plt.title('Monthly means for progressively trimmed data series')
plt.plot(np.ones(len(trimmed_means_df.index)+1) * 0, 'k--')
plt.plot(np.ones(len(trimmed_means_df.index)+1) * median, 'r+', label='Overall Median')
for i in range(len(trimmed_means_df.columns)):
    plt.plot(trimmed_means_df[trimmed_means_df.columns[i]], 'b', 
             alpha=(i+1.0) / len(trimmed_means_df.columns))
plt.legend(loc="best")
plt.xticks(trimmed_means_df.index, xTicks)
maxY = max(abs(trimmed_means_df.values.min()), 
           abs(trimmed_means_df.values.max()))
plt.ylim((-maxY,maxY))
plt.show()

# Full the data frame with the 1-sigma range and min/max values
conf_interv_df = pd.DataFrame(index=mRange)
conf_interv_df['Min'] = yearsXmonths_df.min()
conf_interv_df['Mu-1s'] = yearsXmonths_df.mean() - yearsXmonths_df.std()
conf_interv_df['Mu+1s'] = yearsXmonths_df.mean() + yearsXmonths_df.std()
conf_interv_df['Max'] = yearsXmonths_df.max()

# Rename the months and print the results 
p_value_df.index = trimmed_means_df.index = xTicks
print  p_value_df
#print '\n\n', trimmed_means_df, '\n\n', conf_interv_df
print 'Seasonalities at', SIGNIFICANCE, \
      'significance level are detected', np.round(percSignal, 2), 'times'
      
