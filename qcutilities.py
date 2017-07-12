#!/bin/env python

"""
Utilities for vfatqc scans
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

# Imports
import sys, os
import numpy as np
#import root_numpy as rp

def filePathExists(searchPath, subPath):
    import glob

    dirs        = glob.glob(searchPath)
    foundDir    = False

    for path in dirs:
        if path.rfind(subPath) > 0:
            foundDir = True
            pass
        pass
    if not foundDir:
        print "Unable to find %s in location: %s"%(subPath, searchPath)
        return False
    else:
        print "Found %s"%s(subPath)
        return True

def initVFATArray(array_dtype, nstrips=128):
    list_dtypeTuple = []

    for idx in range(0,len(array_dtype)):
        if array_dtype.names[idx] == 'vfatN':   continue
        if array_dtype.names[idx] == 'vfatCh':  continue
        if array_dtype.names[idx] == 'panPin':  continue
        if array_dtype.names[idx] == 'ROBstr':  continue
        list_dtypeTuple.append((array_dtype.names[idx],array_dtype[idx]))
        pass

    return np.zeros(nstrips, dtype=list_dtypeTuple)

#Use Median absolute deviation (MAD) to reject outliers
#See: http://stackoverflow.com/questions/22354094/pythonic-way-of-detecting-outliers-in-one-dimensional-observation-data
#And also: http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
def rejectOutliersMAD(arrayData, thresh=3.5):    
    arrayOutliers = isOutlierMAD(arrayData, thresh)
    return arrayData[arrayOutliers != True]


#Use MAD to reject outliers, but consider only high or low tail
def rejectOutliersMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    arrayOutliers = isOutlierMADOneSided(arrayData, thresh, rejectHighTail)
    return arrayData[arrayOutliers != True]

#Use inter-quartile range (IQR) to reject outliers
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQR(arrayData):
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
        pass

    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    return (arrayData < (q1 - 1.5 * IQR)) or (arrayData > (q3 + 1.5 * IQR))

#Use inter-quartile range (IQR) to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQROneSided(arrayData, rejectHighTail=True):
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
        pass

    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    if rejectHighTail:
        return arrayData > (q3 + 1.5 * IQR)
    else:
        return arrayData < (q1 - 1.5 * IQR)

#Use Median absolute deviation (MAD) to reject outliers
#See: https://github.com/joferkington/oost_paper_code/blob/master/utilities.py
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMAD(arrayData, thresh=3.5):
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
        pass

    median = np.median(arrayData, axis=0)

    diff = np.sum((arrayData - median)**2, axis=-1)
    diff = np.sqrt(diff)

    med_abs_deviation = np.median(diff)

    if med_abs_deviation == 0:
        return isOutlierIQR(arrayData)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation
        return modified_z_score > thresh

#Use MAD to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    if len(arrayData.shape) == 1:
        arrayData = arrayData[:,None]
        pass

    median = np.median(arrayData, axis=0)
    diff = np.sum(arrayData - median, axis=-1)
    med_abs_deviation = np.median(np.abs(diff))


    if med_abs_deviation == 0:
        return isOutlierIQROneSided(arrayData, rejectHighTail)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation

        if rejectHighTail:
            return modified_z_score > thresh
        else:
            return modified_z_score < -1.0 * thresh
