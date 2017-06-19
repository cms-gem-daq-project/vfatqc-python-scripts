#!/bin/env python

# Imports
import sys, os
import numpy as np
#import root_numpy as rp

#Use Median absolute deviation (MAD) to reject outliers
#See: http://stackoverflow.com/questions/22354094/pythonic-way-of-detecting-outliers-in-one-dimensional-observation-data
#And also: http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
def rejectOutliers(arrayData, thresh=3.5):    
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
	pass
        
    median = np.median(arrayData, axis=0)
        
    diff = np.sum((arrayData - median)**2, axis=-1)
    diff = np.sqrt(diff)
        
    med_abs_deviation = np.median(diff)
        
    modified_z_score = 0.6745 * diff / med_abs_deviation
        
    arrayMask = (modified_z_score < thresh) #true if points are not outliers, false if points are outliers
    arrayData = np.multiply(arrayData, arrayMask) #Now outliers are set to zero
        
    return arrayData[(arrayData > 0)] #Return only the non-outlier versions

#Use Median absolute deviation (MAD) to reject outliers
#See: https://github.com/joferkington/oost_paper_code/blob/master/utilities.py
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlier(arrayData, thresh=3.5):
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
	pass

    median = np.median(arrayData, axis=0)

    diff = np.sum((arrayData - median)**2, axis=-1)
    diff = np.sqrt(diff)

    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh
