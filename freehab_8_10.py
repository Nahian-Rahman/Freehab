#### Adaptive Threshold #################
#### EMG reversed #######################
#### falling edge start, rising edge stop


## IMPORT Library ###################################################################
#####################################################################################
import math 
import time
import copy
from time import sleep, strftime, gmtime
from time import perf_counter
import sys, os
import openzen
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv
import serial
import string
import numpy as np
import keyboard
import threading
import pandas
import pandas as pd
from datetime import datetime
import nidaqmx
from nidaqmx.constants import Edge
from nidaqmx.constants import AcquisitionType 

from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
#from nidaqmx import AnalogOutputTask

from nidaqmx.constants import (
LineGrouping)
import pickle
from datetime import datetime
import scipy.io

import multiprocessing as mp
import math
from collections import deque

## Function: record IMU data ######################################################################
def file_record():
#############       Recording file for analog inputs      #############
    global fa, timestr  
    timestr = time.strftime("%Y%m%d-%H%M%S")
############################     IMU files      #######################

    global f1, f2, f3, f4, f5 # files
    # timestr = time.strftime("%Y%m%d-%H%M%S")
    global LogFile1, LogFile2, LogFile3, LogFile4, LogFile5
    LogFile1 = "LP_1"+"_"+timestr+".csv"   # filename of output data file
    f1=open(LogFile1,'w')
    data = ["rtTime"]  + ["R Thigh Angle"] + ["R Thigh Angle (unwrap)"]
    for ele in data:
                        f1.write(str(ele)+',')
    f1.write('\n')
 
    LogFile2 = "LP_2"+"_"+timestr+".csv"   # filename of output data file
    f2=open(LogFile2,'w')
    data = ["rsTime"]  + ["R Shank Angle"] + ["R Shank Angle (unwrap)"] 
    for ele in data:
                        f2.write(str(ele)+',')
    f2.write('\n')
 
    LogFile3 = "LP_3"+"_"+timestr+".csv"   # filename of output data file
    f3=open(LogFile3,'w')
    data = ["ltTime"]  + ["L Thigh Angle"] + ["L Thigh Angle (unwrap)"] 
    for ele in data:
                        f3.write(str(ele)+',')
    f3.write('\n')
 
    LogFile4 = "LP_4"+"_"+timestr+".csv"   # filename of output data file
    f4=open(LogFile4,'w')
    data = ["lsTime"]  + ["L Shank Angle"] + ["L Shank Angle (unwrap)"] 
    for ele in data:
                        f4.write(str(ele)+',')
    f4.write('\n')
 
    LogFile5 = "LP_5"+"_"+timestr+".csv"   # filename of output data file
    f5=open(LogFile5,'w')
    data = ["hTime"]  + ["Hip Angle X"] + ["Hip Angle Rot"] 
    for ele in data:
                        f5.write(str(ele)+',')
    f5.write('\n')
 
## Function: enable IMU connection (from the Supplier's library) ##################################################
def connectSensors():
    global quit
    error, client = openzen.make_client()
    if not error == openzen.ZenError.NoError:
        print ("Error while initializinng OpenZen library")
        quit = True
        sys.exit(1)

    sensor1MacID = "00:04:3E:86:26:E7"   # right thigh
    sensor2MacID = "00:04:3E:4B:31:C3"   # right shank
    sensor3MacID = "00:04:3E:86:27:24"   # left thigh
    sensor4MacID = "00:04:3E:86:27:9A"   # left shank
    sensor5MacID = "00:04:3E:86:27:E0"   # hip

    print ("Connecting to Sensors")
    # Connect to sensor1
    
    while True:
        error, sensor1 = client.obtain_sensor_by_name("Bluetooth", sensor1MacID)
        print("Trying to connect Right Thigh...press E to quit")
        if keyboard.is_pressed("e"):
            quit = True
            sys.exit(1)
        if not error != openzen.ZenError.NoError: 
            break
    #if not error == openzen.ZenError.NoError:
    #    print ("Error connecting to right thigh", sensor1MacID)
    #    quit = True
    #    sys.exit(1)
    imu1 = sensor1.get_any_component_of_type(openzen.component_type_imu)

    # Connect to sensor2
    while True:
        error, sensor2 = client.obtain_sensor_by_name("Bluetooth", sensor2MacID)
        print("Trying to connect Right Shank...press E to quit")
        if keyboard.is_pressed("e"):
            quit = True
            sys.exit(1)
        
        
        if not error != openzen.ZenError.NoError:
            break
            #print ("Error connecting to right shank", sensor2MacID)
            #quit = True
            #sys.exit(1)
    imu2 = sensor2.get_any_component_of_type(openzen.component_type_imu)

    # Connect to sensor3
    while True:
        error, sensor3 = client.obtain_sensor_by_name("Bluetooth", sensor3MacID)
        print("Trying to connect Left Thigh...press E to quit")
        if keyboard.is_pressed("e"):
            quit = True
            sys.exit(1)
        
        if not error != openzen.ZenError.NoError:
            break
            #print ("Error connecting to left thigh", sensor3MacID)
            #quit = True
            #sys.exit(1)
    imu3 = sensor3.get_any_component_of_type(openzen.component_type_imu)

    while True:
        error, sensor4 = client.obtain_sensor_by_name("Bluetooth", sensor4MacID)
        print("Trying to connect Left Shank...press E to quit")
        if keyboard.is_pressed("e"):
            quit = True
            sys.exit(1)
        if not error != openzen.ZenError.NoError:
            break
            #print ("Error connecting to left shank", sensor4MacID)
            #quit = True
            #sys.exit(1)
    imu4 = sensor4.get_any_component_of_type(openzen.component_type_imu)
    
    while True:
        error, sensor5 = client.obtain_sensor_by_name("Bluetooth", sensor5MacID)
        print("Trying to connect Hip...press E to quit")
        if keyboard.is_pressed("e"):
            quit = True
            sys.exit(1)
        if not error != openzen.ZenError.NoError:
            #print ("Error connecting to hip", sensor5MacID)
            #quit = True
            #sys.exit(1)
            break
    imu5 = sensor5.get_any_component_of_type(openzen.component_type_imu)

    print ("Sensors Connected")

    # Set stream frequency
    streamFreq = 100 # Hz
    error = imu1.set_int32_property(openzen.ZenImuProperty.SamplingRate, streamFreq)
    error, freq = imu1.get_int32_property(openzen.ZenImuProperty.SamplingRate)
    print("Sampling rate sensor1: {}".format(freq))

    error = imu2.set_int32_property(openzen.ZenImuProperty.SamplingRate, streamFreq)
    error, freq = imu2.get_int32_property(openzen.ZenImuProperty.SamplingRate)
    print("Sampling rate sensor2: {}".format(freq))

    error = imu3.set_int32_property(openzen.ZenImuProperty.SamplingRate, streamFreq)
    error, freq = imu3.get_int32_property(openzen.ZenImuProperty.SamplingRate)
    print("Sampling rate sensor3: {}".format(freq))

    error = imu4.set_int32_property(openzen.ZenImuProperty.SamplingRate, streamFreq)
    error, freq = imu4.get_int32_property(openzen.ZenImuProperty.SamplingRate)
    print("Sampling rate sensor4: {}".format(freq))
    
    error = imu5.set_int32_property(openzen.ZenImuProperty.SamplingRate, streamFreq)
    error, freq = imu5.get_int32_property(openzen.ZenImuProperty.SamplingRate)
    print("Sampling rate sensor5: {}".format(freq))

    # Sync sensors
    print ("Sensors sync")
    imu1.execute_property(openzen.ZenImuProperty.StartSensorSync)
    imu2.execute_property(openzen.ZenImuProperty.StartSensorSync)
    imu3.execute_property(openzen.ZenImuProperty.StartSensorSync)
    imu4.execute_property(openzen.ZenImuProperty.StartSensorSync)
    imu5.execute_property(openzen.ZenImuProperty.StartSensorSync)
    # wait a moment for the synchronization commands to arrive
    time.sleep(3)

    # clear internal openzen event queue to remove existing data
    while True:
        zenEvent = client.poll_next_event()
        if zenEvent == None:
            break
    
    # set both sensors back to normal mode, sensor will start data streaming after these commands
    imu1.execute_property(openzen.ZenImuProperty.StopSensorSync)
    imu2.execute_property(openzen.ZenImuProperty.StopSensorSync)
    imu3.execute_property(openzen.ZenImuProperty.StopSensorSync)
    imu4.execute_property(openzen.ZenImuProperty.StopSensorSync)
    imu5.execute_property(openzen.ZenImuProperty.StopSensorSync)
    print("Sync completed")

    return (client, sensor1, imu1, sensor2, imu2, sensor3, imu3, sensor4, imu4, sensor5, imu5)



imu_state = {}

def update_unwrap(imu_id, IMU_angle):

    if imu_id not in imu_state:
        imu_state[imu_id] = {
            "last_raw": IMU_angle,
            "unwrapped": IMU_angle
        }
        return IMU_angle

    last_raw = imu_state[imu_id]["last_raw"]
    unwrapped = imu_state[imu_id]["unwrapped"]

    dtheta = IMU_angle - last_raw

    if dtheta > 180:
        dtheta -= 360
    elif dtheta < -180:
        dtheta += 360

    unwrapped += dtheta

    imu_state[imu_id]["last_raw"] = IMU_angle
    imu_state[imu_id]["unwrapped"] = unwrapped

    return unwrapped


## Function: acquire IMUs (from Supplier's library) #####################################################


def data_acquisition(client, imu1, imu2, imu3, imu4, imu5, IMU_11,IMU_22,IMU_33, IMU_44, IMU_55, IMU_1z, IMU_2z,IMU_3z,IMU_4z,IMU_5z):
    global imu1_data, imu1_dt, imu2_data, imu2_dt,imu3_data, imu3_dt,imu4_data, imu4_dt,imu5_data, imu5_dt, quit, f1,f2, f3, f4, f5
    
    global rt, rs, lt, ls, hip
    global record_start
    global s1, s2, s3, s4, s5, t1now, t2now ,t3now, t4now, t5now
    print("Data data_acquisition thread started")
    global LogFile1, LogFile2, LogFile3, LogFile4, LogFile5
    global IMU_1, IMU_2, IMU_3, IMU_4, IMU_5
    local = 0
    detected_time = perf_counter()
    
    while not quit:
        zenEvent = client.wait_for_next_event()

        # check for IMU1 event
        if zenEvent.event_type == openzen.ZenEventType.ImuData:
         if   zenEvent.sensor == imu1.sensor and \
            zenEvent.component.handle == imu1.component.handle:

            imu_data = zenEvent.data.imu_data
            data = copy.copy(imu_data.r[0])    # .r[0] -x, .r[2] - z
            IMU_1 = data
            #IMU_11.value = data
            IMU_11.value = update_unwrap("rthigh",IMU_1)
            IMU_1z.value = copy.copy(imu_data.r[2])
            rt = data
            ts = copy.copy(imu_data.timestamp)
            if (s1 ==1 and record_start==1):
                  s1 = 0
                  t1now = imu_data.timestamp
            
           # data1 = [ts - t1now] + [perf_counter()- detected_time] + [data] 
            data1 = [ts - t1now]  + [data] + [IMU_11.value]
            
            if record_start == 1:
                for ele in data1:
                        f1.write(str(ele)+',')
                f1.write('\n')
 
        # check for IMU2 event
        #elif zenEvent.event_type == openzen.ZenEventType.ImuData and \
         elif   zenEvent.sensor == imu2.sensor and \
            zenEvent.component.handle == imu2.component.handle:

            imu_data = zenEvent.data.imu_data
            data = copy.copy(imu_data.r[0])
            IMU_2 = data
           # IMU_22.value = data
            IMU_22.value = update_unwrap("rshank",IMU_2)
            IMU_2z.value = copy.copy(imu_data.r[2])            
            rs = data
            ts = copy.copy(imu_data.timestamp)
            if (s2 ==1 and record_start==1):
                  s2 = 0
                  t2now = imu_data.timestamp
            #data2 = [ts - t2now] + [perf_counter()- detected_time] + [data] 
            data2 = [ts - t2now]  + [data] + [IMU_22.value]
      
            if record_start == 1:
                for ele in data2:
                        f2.write(str(ele)+',')
                f2.write('\n')
 
        #elif zenEvent.event_type == openzen.ZenEventType.ImuData and \
         elif   zenEvent.sensor == imu3.sensor and \
            zenEvent.component.handle == imu3.component.handle:
            
            imu_data = zenEvent.data.imu_data
            data = copy.copy(imu_data.r[0])
            IMU_3 = data
            lt = data
            #IMU_33.value = data
            IMU_33.value = update_unwrap("lthigh",IMU_3)
            IMU_3z.value = copy.copy(imu_data.r[2])            
            ts = copy.copy(imu_data.timestamp)
            if (s3 ==1 and record_start==1):
                  s3 = 0
                  t3now = imu_data.timestamp
           # data3 = [ts - t3now] + [perf_counter()- detected_time] + [data] 
            data3 = [ts - t3now]  + [data] + [IMU_33.value]

            if record_start == 1:
                for ele in data3:
                        f3.write(str(ele)+',')
                f3.write('\n')
        
        #elif zenEvent.event_type == openzen.ZenEventType.ImuData and \
         elif   zenEvent.sensor == imu4.sensor and \
            zenEvent.component.handle == imu4.component.handle:
            
            imu_data = zenEvent.data.imu_data
            data = copy.copy(imu_data.r[0])
            IMU_4 = data
            ls = data
           # IMU_44.value = data
            IMU_44.value = update_unwrap("lshank",IMU_4)
            IMU_4z.value = copy.copy(imu_data.r[2])            
            ts = copy.copy(imu_data.timestamp)
            if (s4 ==1 and record_start==1):
                  s4 = 0
                  t4now = imu_data.timestamp
            #data4 = [ts - t4now] + [perf_counter()- detected_time] + [data] 
            data4 = [ts - t4now]  + [data] + [IMU_44.value]
      
            if record_start == 1:
                for ele in data4:
                        f4.write(str(ele)+',')
                f4.write('\n')
       
        #elif zenEvent.event_type == openzen.ZenEventType.ImuData and \
         elif   zenEvent.sensor == imu5.sensor and \
            zenEvent.component.handle == imu5.component.handle:

            imu_data = zenEvent.data.imu_data
            data = copy.copy(imu_data.r[0])
            IMU_5 = data
            hip = data
            #IMU_55.value = data
            IMU_55.value = update_unwrap("hip",IMU_5)
            IMU_5z.value = copy.copy(imu_data.r[2])            
            ts = copy.copy(imu_data.timestamp)
            if (s5 ==1 and record_start==1):
                  s5 = 0
                  t5now = imu_data.timestamp
           # data5 = [ts - t5now] + [perf_counter()- detected_time] + [data] 
            data5 = [ts - t5now]  + [data] + [IMU_5z.value]

            if record_start == 1:
                for ele in data5:
                        f5.write(str(ele)+',')
                f5.write('\n')
 
        time.sleep(0.001)

    print("Data data_acquisition thread terminated")

## Function: calculate FSR period ####################################################

## Function: calculate FSR period ####################################################

def Period_FSR(heelR,heelL,toeR,toeL, HPeriod_available_R, HPeriod_available_L,HeelRp, HeelLp,Allexit,TPeriod_available_R, TPeriod_available_L,ToeRp, ToeLp,gaitR, gaitL):
    
     # Right heel
     heelcountR = 0         # Right heel strike count
     heelcountR_flag = 0    # Flag to enable state change
     heelcountTime_R =0     # exact time of strike
     Previous_heelcountTime_R = 0   
     timeHeelR = 0          # period between strike
     timeHeelR_avg = 0      # average of period between last three strikes
     heel_periods_R = deque(maxlen=3) # list for last three periods - Right heel
    
     # Left heel
     heelcountL, heelcountL_flag, heelcountTime_L, Previous_heelcountTime_L, timeHeelL, timeHeelL_avg = 0,0,0,0,0,0
     heel_periods_L = deque(maxlen=3) # list for last three periods - Left heel

     # Right toe
     toecountR, toecountTime_R, Previous_toecountTime_R, timetoeR, timetoeR_avg, forToeR = 0,0,0,0,0,0 
     toecountR_flag = 1   
     # Left toe
     toecountL, toecountTime_L, Previous_toecountTime_L, timetoeL, timetoeL_avg, forToeL = 0,0,0,0,0,0 
     toecountL_flag = 1
     
     try: # add try: to identify problem when the codes fail.
      #print("Came to FSR...", flush=True)
      while not Allexit.value:
        ## Right heel strike #########################################################
         HeelStateR = copy.copy(heelR.value)
        # print("1", flush=True)   
        # HeelStateR indicates heel is touched
         if HeelStateR == 1 and heelcountR_flag == 0:
             heelcountR_flag = 1
             heelcountTime_R = perf_counter() # stores the exact time of heel strike
             if heelcountR == 0:
                  gaitR.value = heelcountTime_R # gaitR is global variable for the exact time of heel strike
             forToeR = copy.copy(heelcountTime_R) # to use in the toe off time calculation
             heelcountR = heelcountR +1  # increase counter by 1
            # Prev_heelcountTime_R = perf_counter()
             #print("here")   
             if heelcountR> 1:
                  time_bet_heel_R = heelcountTime_R - Previous_heelcountTime_R # time between two consecutive heel strikes
                  #timeHeelR = timeHeelR + time_bet_heel_R # running sum of intervals
                  heel_periods_R.append(time_bet_heel_R) # add to the list, autmoatically removes the oldest entry if more than 3
            #### OLD METHOD ####
            #  if heelcountR == 3:
            #      timeHeelR_avg = timeHeelR/3 
            #      timeHeelR = 0
            #      heelcountR = 0 
            #      gaitR.value =  perf_counter()
            #  Previous_heelcountTime_R = heelcountTime_R

              ### NEW METHOD --- START ###
             if len(heel_periods_R) == 3: # when the length of the list reaches 3, start calculating average
                    timeHeelR_avg = sum(heel_periods_R) / 3
                    gaitR.value =  perf_counter()
             Previous_heelcountTime_R = heelcountTime_R
               ### NEW METHOD --- END ###

         if HeelStateR == 0 and heelcountR_flag == 1:
              heelcountR_flag = 0
              # timeHeel is actually the gait period
              #print("here")

         if timeHeelR_avg != 0:
              HPeriod_available_R.value = 1
              HeelRp.value = copy.copy(timeHeelR_avg)
              timeHeelR_avg = 0   

        ## Left heel strike #########################################################
         HeelStateL = copy.copy(heelL.value)
         #print("here")   
         if HeelStateL == 1 and heelcountL_flag == 0:
             heelcountL_flag = 1
             heelcountTime_L = perf_counter()
             forToeL = copy.copy(heelcountTime_L)
             heelcountL = heelcountL +1  
            # Prev_heelcountTime_R = perf_counter()
             #print("here")   
             if heelcountL> 1:
                  time_bet_heel_L = heelcountTime_L - Previous_heelcountTime_L 
                  #timeHeelL = timeHeelL + time_bet_heel_L 
                  heel_periods_L.append(time_bet_heel_L) # add to the list, autmoatically removes the oldest entry if more than 3
             #if heelcountL == 3:
              #   timeHeelL_avg = timeHeelL/3 
               #  timeHeelL = 0
                # heelcountL = 0   
             #Previous_heelcountTime_L = heelcountTime_L
             ### NEW METHOD --- START ###
             if len(heel_periods_L) == 3: # when the length of the list reaches 3, start calculating average
                    timeHeelL_avg = sum(heel_periods_L) / 3
                    gaitL.value =  perf_counter()
             Previous_heelcountTime_L = heelcountTime_L
               ### NEW METHOD --- END ###
         if HeelStateL == 0 and heelcountL_flag == 1:
              heelcountL_flag = 0
              
              #print("here")

         if timeHeelL_avg != 0:
              HPeriod_available_L.value = 1
              HeelLp.value = copy.copy(timeHeelL_avg)
              timeHeelL_avg = 0   

        ## Right toe off #########################################################
        # update time of every completed three gaits
        # timetoe is the time from the gait starts till toe off
         ToeStateR = copy.copy(toeR.value)
         #print("here")   
         if ToeStateR == 0 and toecountR_flag == 0:
             toecountR_flag = 1
             toecountTime_R = perf_counter() - forToeR
             toecountR = toecountR +1  
              
             if toecountR> 1:
                  #time_bet_toe_R = toecountTime_R - Previous_toecountTime_R 
                  timetoeR = previousTimetoeR + toecountTime_R 
             previousTimetoeR = toecountTime_R
             if toecountR == 3:
                 timetoeR_avg = timetoeR/3 
                 timetoeR = 0
                 toecountR = 0
                 previousTimetoeR = 0   
             Previous_toecountTime_R = toecountTime_R
         if ToeStateR == 1 and toecountR_flag == 1:
              toecountR_flag = 0
              
              #print("here")

         if timetoeR_avg != 0:
              TPeriod_available_R.value = 1
              ToeRp.value = copy.copy(timetoeR_avg)
              timetoeR_avg = 0              

        ## Left toe off #########################################################       
         ToeStateL = copy.copy(toeL.value)
         #print("here")   
         if ToeStateL == 0 and toecountL_flag == 0:
             toecountL_flag = 1
             toecountTime_L = perf_counter() - forToeL
             toecountL = toecountL +1  
              
             if toecountL> 1:
                  #time_bet_toe_R = toecountTime_R - Previous_toecountTime_R 
                  timetoeL = previousTimetoeL + toecountTime_L 
             previousTimetoeL = toecountTime_L
             if toecountL == 3:
                 timetoeL_avg = timetoeL/3 
                 timetoeL = 0
                 toecountL = 0
                 previousTimetoeL = 0   
             Previous_toecountTime_L = toecountTime_L
         if ToeStateL == 1 and toecountL_flag == 1:
              toecountL_flag = 0
              
              #print("here")

         if timetoeL_avg != 0:
              TPeriod_available_L.value = 1
              ToeLp.value = copy.copy(timetoeL_avg)
              timetoeL_avg = 0              
       #  print(' {:.3f},     {:.3f}'.format(float(HeelRp.value),  float(HeelLp.value)), end ='\r' ) 
              
     except Exception as e:
            import traceback
            print("FSR crashed", e , flush=True )
            traceback.print_exc()
## Function: calculates Actuation time based on Period #######################################
def Timesforwalk(HPeriod_available_R, HPeriod_available_L,HeelRp, HeelLp,Allexit,TPeriod_available_R, TPeriod_available_L,ToeRp, ToeLp,gaitR, gaitL, Rallow, Lallow, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL, supportTimeRAn, unsupportTimeRAn, supportTimeLAn,unsupportTimeLAn, rStrength, lStrength, rLength, lLength):
          rhflaglocal, rtflaglocal, sr = 0, 0, 0
          lhflaglocal, ltflaglocal, sl = 0, 0, 0

          # If Allexit.value = 0, true
          while not Allexit.value:
                   # print("2", flush=True) 
                    if HPeriod_available_R.value == 1:
                        Rhtime = copy.copy(HeelRp.value)   
                        rhflaglocal = 1 
                        HPeriod_available_R.value = 0
                    #    print("Heel period received")

                    if TPeriod_available_R.value == 1:
                        Rttime = copy.copy(ToeRp.value)
                        rtflaglocal = 1
                        TPeriod_available_R.value = 0
                    #    print("Toe period received")

                    if rhflaglocal == 1 and rtflaglocal == 1:
                        rhflaglocal = 0
                        rtflaglocal = 0
                        Rallow.value = 1
                        #GaitR = copy.copy(gaitR)r
                        #front 40-60
                        supportTimeR.value= (rStrength.value)*Rhtime #((Rttime/Rhtime) - 0.2 +r 0.2)*Rhtime # Toe off start # 0.7
                        unsupportTimeR.value= (rLength.value)*Rhtime#((Rttime/Rhtime) - 0.1)*Rhtime #90% of total period #((Rttrime/Rhtime) + 0.1)*Rhtime #0.2
                        #back 10-45
                        supportTimeRAn.value= (rStrength.value)*Rhtime #0% of total period#((Rttime/Rhtime) - 0.15)*Rhtime
                        unsupportTimeRAn.value= (rLength.value)*Rhtime#((Rttime/Rhtime) - 0.25)*Rhtime # Toe off 
                        # print(Rhtime, Rttime, supportTimeR,unsupportTimeR, supportTimeRAn,  unsupportTimeRAn )

                    if HPeriod_available_L.value == 1:
                            Lhtime = copy.copy(HeelLp.value)
                            lhflaglocal = 1 
                            HPeriod_available_L.value = 0
                          #  print("Left Heel period received")

                    if TPeriod_available_L.value == 1:
                            Lttime = copy.copy(ToeLp.value)
                            ltflaglocal = 1
                            TPeriod_available_L.value = 0
                         #   print("Left Toe period received")

                    if lhflaglocal == 1 and ltflaglocal == 1:
                            lhflaglocal = 0
                            ltflaglocal = 0
                            Lallow.value = 1
                            #GaitR = copy.copy(gaitR)
                            supportTimeL.value= (lStrength.value)*Lhtime#((Lttime/Lhtime) - 0.2 + 0.2)*Lhtime
                            unsupportTimeL.value= (lLength.value)*Lhtime#0.6*Lhtime #((Lttime/Lhtime) + 0.1)*Lhtime
                            supportTimeLAn.value= (lStrength.value)*Lhtime #((Lttime/Lhtime) - 0.15)*Lhrtime
                            unsupportTimeLAn.value= (lLength.value)*Lhtime #((Lttime/Lhtime) + 0.2)*Lhtime
                           
                           # supportTimeL.value= 0 #((Lttime/Lhtime) - 0.2 + 0.2)*Lhtime
                          #  unsupportTimeL.value= 0 #0.6*Lhtime #((Lttime/Lhtime) + 0.1)*Lhtime
                          #  supportTimeLAn.value= 0 #((Lttime/Lhtime) - 0.15)*Lhrtime
                          #  unsupportTimeLAn.value= 0 #((Lttime/Lhtime) + 0.2)*Lhtime
                           
                           
                           # print(Lhtime, Lttime, supportTimeL,unsupportTimeL, supportTimeLAn,  unsupportTimeLAn )

                    if keyboard.is_pressed('q'):
                            #GaitR = copy.copy(gaitR)
                            supportTimeL.value= 0
                            unsupportTimeL.value= 0
                            supportTimeLAn.value= 0
                            unsupportTimeLAn.value= 0
                            supportTimeR.value= 0
                            unsupportTimeR.value= 0
                            supportTimeRAn.value= 0
                            unsupportTimeRAn.value= 0 
            
## Function: execute the actuators' actuation ###########################################            

sit_memory = {
    'prev_rk': None,
    'prev_lk': None,
    'prev_rt': None,
    'prev_lt': None,
    'base_rk': None,
    'base_lk': None,
    'trend': 0,
    'cooldown': 0,
    'frame_count': 0
}
def Activity(heelR,heelL,toeR,toeL,Allexit, Rallow, Lallow, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL, supportTimeRAn, unsupportTimeRAn, supportTimeLAn,unsupportTimeLAn, R, L, RR, LL, Emg_sig, r_pressed, IMU_11, IMU_22, IMU_33, IMU_44, IMU_5z, IMU_55, Applied_pressure, Stage_of_user, rSitThigh, rSitShank, lSitThigh, lSitShank, rStandThigh, rStandShank, lStandThigh, lStandShank, psRu, psRd, psLu, psLd, UserInfoGiven):
    # Setting Arduino (run once)
    # lab COM3, home COM15, portenta COM53, Neq Due 15
    arduino = serial.Serial('COM15', 115200, parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS, timeout=.1) #115200
    # command to arduino to execute the EMG and actuators
    z = '<3, 0.0, 0.0, 0.0, 0.0, 0.0>'
    arduino.write(bytes(z, "utf-8"))
    time.sleep(2)

    ## Internal Function: set applied pressure
    def apply_pressure(e, r, l, rm, lm): # e = EMG, r = right actuator 1, rm = right actuator 2, ...
       z = '<' + str(e) +',' + str(r) +',' +  str(l) +',' + str(rm) +',' + str(lm) + '>'
     #print(z)
       arduino.write(bytes(z, "utf-8"))











    def detect_sit_intention(IMU_11, IMU_22, IMU_33, IMU_44, UserInfoGiven):
        global sit_memory

        rk = IMU_22.value - IMU_11.value
        lk = IMU_44.value - IMU_33.value
        rt = IMU_11.value
        lt = IMU_33.value

        # Initialise
        if sit_memory['prev_rk'] is None:
            sit_memory['prev_rk'] = rk
            sit_memory['prev_lk'] = lk
            sit_memory['prev_rt'] = rt
            sit_memory['prev_lt'] = lt
            sit_memory['base_rk'] = rk
            sit_memory['base_lk'] = lk
            return 0

        drk = rk - sit_memory['prev_rk']
        dlk = lk - sit_memory['prev_lk']
        drt = rt - sit_memory['prev_rt']
        dlt = lt - sit_memory['prev_lt']

        sit_memory['prev_rk'] = rk
        sit_memory['prev_lk'] = lk
        sit_memory['prev_rt'] = rt
        sit_memory['prev_lt'] = lt

        # Update standing baseline slowly when not detecting
        alpha = 0.995
        sit_memory['base_rk'] = alpha * sit_memory['base_rk'] + (1 - alpha) * rk
        sit_memory['base_lk'] = alpha * sit_memory['base_lk'] + (1 - alpha) * lk

        if sit_memory['cooldown'] > 0:
            sit_memory['cooldown'] -= 1
            sit_memory['trend'] = 0
            return 0

        # Knee flexion relative to standing baseline
        rk_from_stand = rk - sit_memory['base_rk']
        lk_from_stand = lk - sit_memory['base_lk']

        # These must be larger than standing sway
        knee_flexion_threshold = 0.01
        motion_threshold = 0.001

        both_knees_flexed_from_stand = (
            rk_from_stand > knee_flexion_threshold and
            lk_from_stand > knee_flexion_threshold
        )

        both_knees_currently_flexing = (
            drk > motion_threshold and
            dlk > motion_threshold
        )

        trunk_sit_motion = (
            drt < -motion_threshold or
            dlt < -motion_threshold
        )

        if both_knees_flexed_from_stand and both_knees_currently_flexing and trunk_sit_motion:
            sit_memory['trend'] += min(drk, dlk)
        else:
            sit_memory['trend'] *= 0.5

        threshold = 0.01

        if sit_memory['trend'] > threshold and UserInfoGiven.value == 1:
            sit_memory['trend'] = 0
            sit_memory['cooldown'] = 80
            return 1

        return 0
    """
    def detect_sit_intention(IMU_11, IMU_22, IMU_33, IMU_44, UserInfoGiven,
                            memory={'prev_rk': None, 'prev_lk': None, 'prev_rt': None, 'prev_lt': None, 'trend': 0}):

        rk = IMU_22.value - IMU_11.value
        lk = IMU_44.value - IMU_33.value
        rt = IMU_11.value
        lt = IMU_33.value

        # first frame init
        if memory['prev_rk'] is None:
            memory['prev_rk'] = rk
            memory['prev_lk'] = lk
            memory['prev_rt'] = rt
            memory['prev_lt'] = lt
            memory['trend'] = 0
            return 0

        # differences
        drk = rk - memory['prev_rk']
        dlk = lk - memory['prev_lk']
        drt = rt - memory['prev_rt']
        dlt = lt - memory['prev_lt']

        # update memory
        memory['prev_rk'] = rk
        memory['prev_lk'] = lk
        memory['prev_rt'] = rt
        memory['prev_lt'] = lt

        # accumulate trend (allow partial leg movement)
        memory['trend'] += max(drk, 0) + max(dlk, 0) - min(drt, 0) - min(dlt, 0)

        # thresholds tuned for tiny IMU signals
        threshold = 0.005  # very small, above noise

        # debug print
        if UserInfoGiven.value == 1:    
           pass 
           #  print(f"trend={memory['trend']:.4f}, drk={drk:.4f}, dlk={dlk:.4f}, drt={drt:.4f}, dlt={dlt:.4f}")

        if memory['trend'] > threshold and UserInfoGiven.value == 1:
            sit_intent = 1
            memory['trend'] = 0  # reset after detection
        else:
            sit_intent = 0

        return sit_intent

    """

    last_heelR = 0
    last_heelL = 0
    gaittimeR = None
    gaittimeL = None    
# --- process_leg updates actuator1.value and actuator2.value (side-effect) ---
    def process_leg(heel_value, last_heel, gaittime, supportTime, unsupportTime,
                    actuator1, actuator2, level, side=''):
        # 1) Debounce: update gaittime only on rising edge (0 -> 1)
        if heel_value == 1 and last_heel == 0:
            gaittime = perf_counter()
            # Debug: uncomment to see rising edges
            # print(f"{side} rising edge at {gaittime:.4f}")

        # 2) If we've never had a heel strike, keep actuators OFF
        if gaittime is None:
            actuator1.value = 0
            actuator2.value = 0
            return heel_value, gaittime

        # 3) Time since last heel strike
        currenttime = perf_counter() - gaittime

        # 4) Gate actuator setpoints based on support window
        #if supportTime.value <= currenttime <= unsupportTime.value:
        if   unsupportTime.value == 0 or  supportTime.value == 0:
           
            actuator1.value = 0        # was level
            actuator2.value = 0        # was level
            #print("here")
        elif  currenttime >= supportTime.value and currenttime <= unsupportTime.value:
           
            actuator1.value = level        # was level
            actuator2.value = level         # was level
            #print("here")
        else:
            actuator1.value = 0.0    # was 0
            actuator2.value = 0.0    # was 0
           # print("not here")
        # 5) Return updated last_heel and gaittime (so caller saves them)
        return heel_value, gaittime
    standing_done = 0
    walk_allow = 0
    standToSit_allow = 0
    Sit_to_stand = 0
    previous_stage = Stage_of_user.value
    quitDuringLean = 0
    while not Allexit.value :
                    # --- Determine state each loop ---
        
        #print(f"State={state}, Pressure={pressure}, Vel={ang_vel:.2f}")
      #  print(f" State={state}, Pressure={pressure}, Hip Raw ={raw_yaw}")

        #print(f" Hip Raw ={raw_yaw} , Yaw={last_filtered:.2f}")
        Stage = Stage_of_user.value 
        # Detect transition from Stage 2 to Stage 1.5
        standToSit_trigger = (previous_stage == 2 and Stage == 1.5)

        # Update previous stage
        previous_stage = Stage
        quitDuringLean = 0 
        if Stage == 1 and Sit_to_stand == 1: # participant is sitting...
            boostup = 1
            StS_pressure = 0.8
            MaxP         = 1.2
            valueRdif = rStandThigh.value - rSitThigh.value
            valueLdif = lStandThigh.value - lSitThigh.value
            ExR90 = rSitThigh.value + 0.9* valueRdif
            ExL90 = lSitThigh.value + 0.9* valueLdif
            endPressure = 0.15
            if r_pressed.value == 1: 
                Emg_sig.value = 0
                standing_done = 0
                hip_initial = IMU_55.value 
                # record hiplean
                apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                print("\nwating to stand...\n")    
                if boostup == 0:
                       # R.value = StS_pressure
                       # RR.value = StS_pressure
                       # L.value = StS_pressure
                       # LL.value = StS_pressure
                        done = 0
                elif  boostup == 1:
                       # R.value = MaxP
                       # RR.value = MaxP
                       # L.value = MaxP
                       # LL.value = MaxP
                        done = 1

                while not Allexit.value:
                    if keyboard.is_pressed('q'):
                                  Emg_sig.value =0
                                  r_pressed.value = 0
                                  apply_pressure(Emg_sig, 0,0,0,0)
                                  quitDuringLean = 1
                                  break
                    hip_current =  IMU_55.value
                    if hip_initial - hip_current >= 7:
                        current_time = perf_counter()
                       # apply_pressure(Emg_sig.value, R.value, L.value, RR.value, LL.value)
                        print("\nStanding in progress...\n")
                        break
                if quitDuringLean ==0:  
                  while  (perf_counter() - current_time) <=10:
                             
                        

                             if keyboard.is_pressed('q'):
                                  r_pressed.value = 0
                                  Emg_sig.value = 3
                                  apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                                  break
                             #print("I am here")
                             if done == 1:
                                    R.value = MaxP
                                    RR.value = MaxP
                                    L.value = MaxP
                                    LL.value = MaxP
                                    if psRd.value >= 0.7* MaxP *100 :
                                        RR.value = StS_pressure
                                    if psRu.value >= 0.7* MaxP *100 :
                                         R.value = StS_pressure
                                    if psLd.value >= 0.7* MaxP *100 :
                                        LL.value = StS_pressure
                                    if psLu.value >= 0.7* MaxP *100 :
                                         L.value = StS_pressure
                                    if perf_counter() - current_time> 0.25:
                                         done = 0

                             else:
                                R.value = StS_pressure
                                RR.value = StS_pressure
                                L.value = StS_pressure
                                LL.value = StS_pressure
                                positionR = IMU_11.value - rSitThigh.value
                                if positionR <0: positionR = 0
                                positionL = IMU_33.value - lSitThigh.value
                                if positionL <0: positionL = 0
                                stateNowR = positionR/valueRdif
                                stateNowL = positionL/valueLdif 
                                switch1 = 0.7
                                switch2 = 0.8
                                if stateNowR <= switch1 :
                                    R.value = StS_pressure
                                    RR.value= StS_pressure
                                if stateNowL <= switch1 :
                                    L.value = StS_pressure
                                    LL.value= StS_pressure
                                if stateNowR >= switch1 and stateNowR <= switch2 :
                                        # Linear fit -> create an equation
                                        x1 = valueRdif * switch1
                                        x2 = valueRdif * switch2 # tstand 
                                        y1 = StS_pressure #BAM_up
                                        y2 = 0
                                        slope = (y2-y1)/(x2-x1)
                                        
                                        # if  Thigh_state_corrected_current < tstand:
                                        x= positionR
                                        y = slope *(x- x2) +y2   
                                        R.value = y
                                        RR.value= y
                                if stateNowL >= switch1 and stateNowL <= switch2 :
                                        # Linear fit -> create an equation
                                        x1 = valueLdif * switch1
                                        x2 = valueLdif * switch2 # tstand 
                                        y1 = StS_pressure #BAM_up
                                        y2 = 0
                                        slope = (y2-y1)/(x2-x1)
                                        
                                        # if  Thigh_state_corrected_current < tstand:
                                        x= positionL
                                        y = slope *(x- x2) +y2   
                                        L.value = y
                                        LL.value= y
                                if stateNowR >= switch2 : 
                                        R.value = 0
                                        RR.value=  0
                                if stateNowL >= switch2 : 
                                        L.value = 0
                                        LL.value= 0
                                if IMU_11.value >=  ExR90:
                                    R.value = 0
                                    RR.value=  0
                                    L.value = 0
                                    LL.value= 0
                                    
                                    apply_pressure(Emg_sig.value, 0, 0, 0, 0)

                                    break      
                                if IMU_33.value >=  ExL90:
                                    R.value = 0
                                    RR.value=  0
                                    L.value = 0
                                    LL.value= 0
                                    apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                                    break     
                             apply_pressure(Emg_sig.value, R.value, L.value, RR.value, LL.value)
                     #if 
               # Emg_sig.value = 0
                apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                R.value = 0
                RR.value=  0
                L.value = 0
                LL.value= 0
                print("\nStand up done, press N to enter other modes (walking, stand to sit,...), s to sit to stand again,  q to quit recording\n")
                while True:
                    # print("Stand up done, enter to walk, q to quit recording")
                     apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                     if keyboard.is_pressed('q'):
                                  r_pressed.value = 0
                                  Emg_sig.value = 3
                                  apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                                  R.value = 0
                                  RR.value=  0
                                  L.value = 0
                                  LL.value= 0
                                                    
                                  print("\nstanding done... need to press r again to have any actuation") 
                                  if Stage_of_user.value !=1:
                                        standing_done = 1
                                  else:
                                            standing_done = 0
                                  break
                     if keyboard.is_pressed('n'):
                          print("\nstanding done... recording continues in all modes...unless press q")
                          print("\n Press w to get walking support...k to withdraw it...")
                          if Stage_of_user.value !=1:  
                            #print("\nstanding done... actuation will continues in all modes...")
                            standing_done = 1
                          else:
                            
                             standing_done = 0  
                          break
                     
                     if keyboard.is_pressed('s'):
                          standing_done = 0
                          print("\nEnter when participant is Sitted and ready to stand...\n")
                          while True:
                                     if keyboard.is_pressed('enter'):
                                        break
                          break
                #r_pressed.value = 0
                        
                        # 5 degree hip lean start actuation
               # break    
                   # break
        
        else: #Stage != 1:  # not sitting.
                    # print(Stage)

                
                
                if standToSit_trigger and standToSit_allow == 1:

                    print("\nSitting intention detected\n")

                    SitDownPressure = 0.30
                    SitTolerance = 5
                    Emg_sig.value = 0
                    while True:

                        # Calculate pressure based on thigh angles
                        Pr = (
                            (rStandThigh.value - IMU_11.value)
                            * SitDownPressure
                            / (rStandThigh.value - rSitThigh.value)
                        )

                        Pl = (
                            (lStandThigh.value - IMU_33.value)
                            * SitDownPressure
                            / (lStandThigh.value - lSitThigh.value)
                        )

                        # Limit pressure between 0 and 30
                        Pr = max(0, min(Pr, SitDownPressure))
                        Pl = max(0, min(Pl, SitDownPressure))

                        # Emergency stop
                        if keyboard.is_pressed('q'):
                            R.value = 0
                            RR.value = 0
                            L.value = 0
                            LL.value = 0

                            apply_pressure(Emg_sig.value, 0, 0, 0, 0)
                            print("Emergency stop")
                            break

                        # Check sitting completion
                        # Thigh angle decreases from standing to sitting
                        right_sitting_done = (
                            IMU_11.value <= rSitThigh.value + SitTolerance
                        )

                        left_sitting_done = (
                            IMU_33.value <= lSitThigh.value + SitTolerance
                        )

                        if right_sitting_done or left_sitting_done:

                                # Stop pneumatic assistance
                                R.value = 0
                                RR.value = 0
                                L.value = 0
                                LL.value = 0
                                Emg_sig.value = 0
                                # Keep the current EMG trigger unchanged
                                apply_pressure(Emg_sig.value, 0, 0, 0, 0)

                                standing_done = 0

                                print("\nSitting completed.")
                                print("Pneumatic assistance stopped.")
                                print("EMG recording continues. Press q to stop recording.\n")

                                # Keep EMG recording active until q is pressed
                                while not Allexit.value:

                                    R.value = 0
                                    RR.value = 0
                                    L.value = 0
                                    LL.value = 0

                                    apply_pressure(Emg_sig.value, 0, 0, 0, 0)

                                    if keyboard.is_pressed('q'):

                                        r_pressed.value = 0

                                        # Stop EMG recording
                                        Emg_sig.value = 3

                                        apply_pressure(Emg_sig.value, 0, 0, 0, 0)

                                        print("\nEMG recording stopped by pressing q.\n")
                                        break

                                break
                        # Apply pressure only when enabled
                        if r_pressed.value == 1:

                            R.value = Pr
                            RR.value = Pr

                            L.value = Pl
                            LL.value = Pl

                        else:
                            R.value = 0
                            RR.value = 0
                            L.value = 0
                            LL.value = 0

                        # Debug information
                        print(
                            f"IMU_R={IMU_11.value:.2f}, "
                            f"IMU_L={IMU_33.value:.2f}, "
                            f"Pr={Pr:.2f}, "
                            f"Pl={Pl:.2f}, "
                            f"R={R.value:.2f}, "
                            f"L={L.value:.2f}, "
                            f"Enable={r_pressed.value}"
                        )

                        # Send pressure commands
                        apply_pressure(
                            Emg_sig.value,
                            R.value,
                            L.value,
                            RR.value,
                            LL.value
                        )
                                
                
                    
                else:    # not in transition ...can walk and turn....
                        pressure = Applied_pressure.value  # in turning applied pressure will be 0
                        if Rallow.value == 1:
                            # IMPORTANT: assign the returned tuple back!
                            last_heelR, gaittimeR = process_leg(
                                heelR.value, last_heelR, gaittimeR,
                                supportTimeR, unsupportTimeR,
                                R, RR, level=pressure, side='R'
                            )

                        if Lallow.value == 1:
                            last_heelL, gaittimeL = process_leg(
                                heelL.value, last_heelL, gaittimeL,
                                supportTimeL, unsupportTimeL,
                                L, LL, level=pressure, side='L'
                            )
                    #  print(pressure, flush=True)
                        # APPLY once per loop with the current actuator setpoints
                        if r_pressed.value == 1 and walk_allow == 1:
                            apply_pressure(Emg_sig.value, R.value, L.value, RR.value, LL.value)
                            #print("Walking...")
                        else:
                           # Emg_sig.value = 0
                            R.value = 0
                            RR.value=  0
                            L.value = 0
                            LL.value= 0
                            apply_pressure(Emg_sig.value , 0, 0, 0, 0)
        if keyboard.is_pressed('w') and walk_allow == 0:
             walk_allow = 1
             print("\n walk support activated")
        if keyboard.is_pressed('k') and walk_allow == 1:
             walk_allow = 0
             print("\n No walk support")
        if keyboard.is_pressed('o') and standToSit_allow == 0:
             standToSit_allow = 1
             print("\n Stand to sit support activated")
        if keyboard.is_pressed('p') and standToSit_allow == 1:
             standToSit_allow = 0
             print("\n Stand to sit support Deactivated...")
        if keyboard.is_pressed('z') and Sit_to_stand == 0 :
             #    Emg_sig.value = 0
                Sit_to_stand = 1
                print("\nSit to stand allowed... Press x to cancel")
        if keyboard.is_pressed('x') and Sit_to_stand == 1:
             #    Emg_sig.value = 0
                Sit_to_stand = 0
                print("\nSit to stand NOT allowed... Press z to enable")

    # Safety shutoff after loop ends
    Emg_sig.value = 3
    R.value = 0
    RR.value=  0
    L.value = 0
    LL.value= 0
    apply_pressure(Emg_sig.value , 0, 0, 0, 0)
    arduino.close()

## Function: start recording DAQ ###################################################
def record_daq(Allexit, record_start_fd, c_time, LogFile, Lr, Ll, psRu, psRd, psLu,psLd, FSRrh, FSRrt, FSRlh, FSRlt, switch, heelR,heelL,HeelRp, HeelLp,toeR,toeL, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL, IMU_11, IMU_22, IMU_33, IMU_44, IMU_55, IMU_1z, IMU_2z, IMU_3z, IMU_4z, IMU_5z, rSitThigh, rSitShank, lSitThigh, lSitShank,   rStandThigh,  rStandShank, lStandThigh,  lStandShank,  hipStand,   rStrength,  lStrength, rLength, lLength, R, L, RR, LL, Emg_sig
):      # varaibles need to change
    
    ## Convert funtion: Pressure sensors ###########################################
    def Volt_to_kPa(v):
         kPa = 73.3102*v - 36.7266
         return kPa
    ## Convert funtion: Load cell ##################################################
    def Volt_to_newton(v):
         Newton = 57.8137*v - 19.9659
         return Newton
    
    # DAQ initialisation (run once)
    n = 5 # n = 5 lab, 1 at home
    taskAI = nidaqmx.Task()
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai0".format(n), min_val=0, max_val= 5)    # Loadcell right
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai1".format(n), min_val=0, max_val= 5)    # Loadcell left
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai2".format(n), min_val=0, max_val= 5)    # Pressure sensor right up
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai3".format(n), min_val=0, max_val= 5)    # Pressure sensor right down
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai4".format(n), min_val=0, max_val= 5)    # Pressure sensor left up
    
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai5".format(n), min_val=0, max_val= 5)    # Pressure sensor left down
    
    
    
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai6".format(n), min_val=0, max_val= 5)    # FSR left heel
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai7".format(n), min_val=0, max_val= 5)    # FSR left toe
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai16".format(n), min_val=0, max_val= 5)   # FSR left heel
    taskAI.ai_channels.add_ai_voltage_chan("Dev{}/ai17".format(n), min_val=0, max_val= 5)   # FSR left toe
    taskAI.timing.cfg_samp_clk_timing(1000, source="OnboardClock", active_edge=Edge.RISING, sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan= 2)  # samps_per_chan= 100
            #10 works, 13 works
    taskAI.in_stream.input_buf_size = 120000

    # Start DAQ
    taskAI.start()   
    fa=open(LogFile,'w')
    data = ["Time"]  + ["R Loadcell"] + ["L Loadcell"]  + ["Given Pressure R BAM UP"] + ["Given Pressure R BAM Down"] + ["Given Pressure L BAM UP"] + ["Given Pressure L BAM Down"] + ["Pressure R BAM UP"] + ["Pressure R BAM Down"] + ["Pressure L BAM UP"] + ["Pressure L BAM Down"] + ["Emg Signal"]+ ["FSR R Heel"] + ["FSR R Toe"] + ["FSR L Heel"] + ["FSR L Toe"] + ["heelR"] + ["heelL"] +["HeelRp"] + ["HeelLp"] +["toeR"]+["toeL"]+ ["supportTimeR"] + ["unsupportTimeR"]+ ["supportTimeL"]+ ["unsupportTimeL"] + ["R thigh"] + ["R shank"] + ["L thigh"] + ["L shank"] +  ["R knee"] + ["L knee"] + ["hip x"] + ["hip r"]  + ["rThighSit"] + ["rShankSit"] + ["lThighSit"] + ["lShankSit"] +["hipSit"] + ["rThighStand"] + ["rShankStand"] + ["lThighStand"] + ["lShankStand"] +["hipStand"]  + ["Rstrength"] + ["Lstrength"]  + ["Rlength"] + ["Llength"] 
            
    for ele in data:
        fa.write(str(ele)+',')
    fa.write('\n')
     
    record_interval = 0
    # Read DAQ ################################################################
    
    
    while not Allexit.value:
        
        Analogs = taskAI.read()
            #Analogs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
        valuex = copy.copy(Analogs)
        Lr.value           = Volt_to_newton(valuex[0])
        Ll.value           = Volt_to_newton(valuex[1])
        psRu.value         = Volt_to_kPa(valuex[2])
        psRd.value         = Volt_to_kPa(valuex[3])
        psLu.value         = Volt_to_kPa(valuex[4])
        psLd.value         = Volt_to_kPa(valuex[5])
        if switch.value == 0:
            FSRrh.value        = valuex[6]
            FSRrt.value        = valuex[7]
            FSRlh.value        = valuex[8]
            FSRlt.value        = valuex[9]

        
        # Record data to the file
        if record_start_fd.value == 1:                      
           # if perf_counter() - record_interval > 0.009:        
                # print("here")
                dataA = [perf_counter() - c_time.value] +  [Lr.value] +  [Ll.value]  + [R.value] + [RR.value]+   [L.value] + [LL.value]+ [psRu.value] + [psRd.value] + [psLu.value] + [psLd.value] +  [Emg_sig.value] +[FSRrh.value] + [FSRrt.value] + [FSRlh.value] + [FSRlt.value]  + [heelR.value] + [heelL.value] +[HeelRp.value] + [HeelLp.value] +[toeR.value]+[toeL.value]+ [supportTimeR.value] + [unsupportTimeR.value]+ [supportTimeL.value]+ [unsupportTimeL.value] + [IMU_11.value] + [IMU_22.value] + [IMU_33.value] + [IMU_44.value] + [IMU_22.value - IMU_11.value] + [IMU_44.value - IMU_33.value] + [IMU_55.value] + [IMU_5z.value]  + [rSitThigh.value] + [rSitShank.value] + [lSitThigh.value] + [lSitShank.value] +  [rStandThigh.value] + [rStandShank.value] + [lStandThigh.value] + [lStandShank.value]  + [hipStand.value]  + [rStrength.value] + [lStrength.value] + [rLength.value] + [lLength.value]
                for ele in dataA:
                    fa.write(str(ele)+',')
                fa.write('\n')

                record_interval = perf_counter()
  
    fa.close()
    taskAI.stop()
    taskAI.close()




def Pressure_foot(Allexit, FSRrh, FSRrt, FSRlh, FSRlt):

    Pressure_serialL = serial.Serial(
        'COM14',  #COM59-- white, COM14---Black
        460800,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.005
    )

    time.sleep(2)

    Pressure_serialR = serial.Serial(
        'COM3',  # COM61-- white    COM3 -- Black
        460800,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.005
    )

    time.sleep(2)

    Pressure_serialL.reset_input_buffer()
    Pressure_serialR.reset_input_buffer()

    P1 = P2 = P3 = P4 = 0.0

    def parse_pressure_line(line):
        try:
            parts = line.split()
            values = {}

            for p in parts:
                if ":" in p:
                    key, val = p.split(":")
                    values[key] = float(val)

            return values

        except Exception as e:
            print(f"Parse error: {e}, line={line}")
            return None

    def read_latest(serial_port):
        latest_line = None

        # Read all available lines and keep only the newest complete one
        while serial_port.in_waiting > 0:
            try:
                line = serial_port.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    latest_line = line
            except Exception:
                pass

        return latest_line

    while not Allexit.value:

        # -------------------------------
        # LEFT foot: COM14
        # -------------------------------
        lineL = read_latest(Pressure_serialL)

        if lineL:
            valuesL = parse_pressure_line(lineL)

            if valuesL is not None:
                if "P1" in valuesL:
                    P3 = valuesL["P1"]   # left heel
                if "P2" in valuesL:
                    P4 = valuesL["P2"]   # left toe

        # -------------------------------
        # RIGHT foot: COM3
        # -------------------------------
        lineR = read_latest(Pressure_serialR)

        if lineR:
            valuesR = parse_pressure_line(lineR)

            if valuesR is not None:
                if "P1" in valuesR:
                    P1 = valuesR["P1"]   # right heel
                if "P2" in valuesR:
                    P2 = valuesR["P2"]   # right toe

        FSRrh.value = P1
        FSRrt.value = P2
        FSRlh.value = P3
        FSRlt.value = P4

    Pressure_serialL.close()
    Pressure_serialR.close()


"""
def Pressure_foot(Allexit,  FSRrh, FSRrt, FSRlh, FSRlt):
     
    Pressure_serialL = serial.Serial('COM14', 460800,    # left 
             parity=serial.PARITY_NONE,
             stopbits=serial.STOPBITS_ONE,
             bytesize=serial.EIGHTBITS, 
             timeout=.1)
    
    time.sleep(2)
    Pressure_serialR = serial.Serial('COM3', 460800,    # left 
             parity=serial.PARITY_NONE,
             stopbits=serial.STOPBITS_ONE,
             bytesize=serial.EIGHTBITS, 
             timeout=.1)
    time.sleep(2)

    def read_pressure():
        line = Pressure_serialL.readline().decode('utf-8').strip()  # decode bytes → string
        if line:  # make sure it's not empty
            try:
                parts = line.split()  # ['P1:991.865', 'P2:991.849', ...]
                values = {p.split(":")[0]: float(p.split(":")[1]) for p in parts}
                
                # Extract variables
                P3 = values.get("P1")
                P4 = values.get("P2")
                #P1 = values.get("P1")
                #P2 = values.get("P2")

                #print(f"P1: {P1}, P2: {P2}, P3: {P3}, P4: {P4}")
                #return P1, P2, P3, P4
            except Exception as e:
                print(f"Parse error: {e}, line={line}")
        line = Pressure_serialR.readline().decode('utf-8').strip()  # decode bytes → string
        if line:  # make sure it's not empty
            try:
                parts = line.split()  # ['P1:991.865', 'P2:991.849', ...]
                values = {p.split(":")[0]: float(p.split(":")[1]) for p in parts}
                
                # Extract variables
                #P3 = values.get("P1")
                #P4 = values.get("P2")
                P1 = values.get("P1")
                P2 = values.get("P2")

                #print(f"P1: {P1}, P2: {P2}, P3: {P3}, P4: {P4}")
                #return P1, P2, P3, P4
            except Exception as e:
                print(f"Parse error: {e}, line={line}")
            return P1, P2, P3, P4
    while not Allexit.value:
            Pressures = read_pressure()
            FSRrh.value, FSRrt.value, FSRlh.value, FSRlt.value = Pressures


    Pressure_serialL.close()
    Pressure_serialR.close()
"""

class AdaptiveFSR:
    def __init__(self,
                 ema_alpha=0.2, hysteresis_frac=0.10,
                 min_contact_ms=60, min_release_ms=60, min_dwell_ms=120,
                 clip_band_min=None, clip_band_max=1e6, learn_window_steps=6):
        self.alpha = ema_alpha
        self.hfrac = hysteresis_frac
        self.min_contact = min_contact_ms / 1000.0
        self.min_release = min_release_ms / 1000.0
        self.min_dwell   = min_dwell_ms   / 1000.0

        # Will auto-choose later if None
        self.clip_band_min = clip_band_min
        self.clip_band_max = clip_band_max

        self.contact_level   = None
        self.nocontact_level = None
        self.invert = None   # auto-detect later

        self.curr_min = math.inf
        self.curr_max = -math.inf

        self.min_hist = deque(maxlen=learn_window_steps)
        self.max_hist = deque(maxlen=learn_window_steps)

        self.state = 0
        self.last_change_t = 0.0
        self.last_contact_tentative = None
        self.last_release_tentative = None

        self.mid = None
        self.lower = None
        self.upper = None

    def _update_levels_from_cycle(self):
        if self.curr_min < math.inf:
            self.min_hist.append(self.curr_min)
        if self.curr_max > -math.inf:
            self.max_hist.append(self.curr_max)

        if len(self.min_hist):
            new_contact = sorted(self.min_hist)[len(self.min_hist)//2]
            self.contact_level = (new_contact if self.contact_level is None
                                  else (1 - self.alpha) * self.contact_level + self.alpha * new_contact)
        if len(self.max_hist):
            new_noc = sorted(self.max_hist)[len(self.max_hist)//2]
            self.nocontact_level = (new_noc if self.nocontact_level is None
                                    else (1 - self.alpha) * self.nocontact_level + self.alpha * new_noc)

        # Decide orientation automatically once both levels exist
        if (self.contact_level is not None) and (self.nocontact_level is not None):
            self.invert = (self.contact_level > self.nocontact_level)

        self.curr_min = math.inf
        self.curr_max = -math.inf

    def _recompute_bands(self):
        if (self.contact_level is None) or (self.nocontact_level is None):
            self.mid = self.lower = self.upper = None
            return
        rng = max(1e-9, abs(self.nocontact_level - self.contact_level))

        # Auto-decide min band if not provided
        if self.clip_band_min is None:
            self.clip_band_min = 0.02 if rng < 50 else 5.0

        band = max(self.clip_band_min, min(self.clip_band_max, self.hfrac * rng))
        self.mid = 0.5 * (self.contact_level + self.nocontact_level)
        self.lower = self.mid - band
        self.upper = self.mid + band

    def update(self, v, t=None):
        if t is None:
            t = time.perf_counter()

        # Track extrema
        if v < self.curr_min:
            self.curr_min = v
        if v > self.curr_max:
            self.curr_max = v

        self._recompute_bands()
        dt_since_change = t - self.last_change_t

        # Bootstrap (wait until levels exist)
        if self.mid is None or self.invert is None:
            if dt_since_change > 0.25:
                self._update_levels_from_cycle()
                self._recompute_bands()
            return self.state, self.lower, self.mid, self.upper

        # --- Hysteresis + debounce + dwell ---
        if not self.invert:  # normal: contact < no-contact (FSR)
            if self.state == 0:  # no-contact
                if v >= self.lower and dt_since_change >= self.min_dwell:
                    if self.last_contact_tentative is None:
                        self.last_contact_tentative = t
                    elif (t - self.last_contact_tentative) >= self.min_contact:
                        self._update_levels_from_cycle()
                        self.state = 1
                        self.last_change_t = t
                        self.last_contact_tentative = None
                        self.curr_min = v
                        self.curr_max = v
                else:
                    self.last_contact_tentative = None
            else:  # contact
                if v <= self.upper and dt_since_change >= self.min_dwell:
                    if self.last_release_tentative is None:
                        self.last_release_tentative = t
                    elif (t - self.last_release_tentative) >= self.min_release:
                        self._update_levels_from_cycle()
                        self.state = 0
                        self.last_change_t = t
                        self.last_release_tentative = None
                        self.curr_min = v
                        self.curr_max = v
                else:
                    self.last_release_tentative = None

        else:  # inverted: contact > no-contact (Pressure sensor)
            if self.state == 0:  # no-contact
                if v <= self.upper and dt_since_change >= self.min_dwell:
                    if self.last_contact_tentative is None:
                        self.last_contact_tentative = t
                    elif (t - self.last_contact_tentative) >= self.min_contact:
                        self._update_levels_from_cycle()
                        self.state = 1
                        self.last_change_t = t
                        self.last_contact_tentative = None
                        self.curr_min = v
                        self.curr_max = v
                else:
                    self.last_contact_tentative = None
            else:  # contact
                if v >= self.lower and dt_since_change >= self.min_dwell:
                    if self.last_release_tentative is None:
                        self.last_release_tentative = t
                    elif (t - self.last_release_tentative) >= self.min_release:
                        self._update_levels_from_cycle()
                        self.state = 0
                        self.last_change_t = t
                        self.last_release_tentative = None
                        self.curr_min = v
                        self.curr_max = v
                else:
                    self.last_release_tentative = None

        return self.state, self.lower, self.mid, self.upper

class AdaptiveFSR_old:
    def __init__(self, init_contact=0.2, init_nocontact=1.0,
                 ema_alpha=0.2, hysteresis_frac=0.10,
                 min_contact_ms=60, min_release_ms=60, min_dwell_ms=120,
                 clip_band_min=0.02, clip_band_max=1e6, learn_window_steps=6):
        self.alpha = ema_alpha
        self.hfrac = hysteresis_frac
        self.min_contact = min_contact_ms / 1000.0
        self.min_release = min_release_ms / 1000.0
        self.min_dwell   = min_dwell_ms   / 1000.0
        self.clip_band_min = clip_band_min
        self.clip_band_max = clip_band_max

        self.contact_level   = init_contact
        self.nocontact_level = init_nocontact

        self.curr_min = math.inf
        self.curr_max = -math.inf

        self.min_hist = deque(maxlen=learn_window_steps)
        self.max_hist = deque(maxlen=learn_window_steps)

        self.state = 0
        self.last_change_t = 0.0
        self.last_contact_tentative = None
        self.last_release_tentative = None

        self.mid = None
        self.lower = None
        self.upper = None

# After each confirmed dwell, take the median of recent mins/maxes, then update contact_level 
# and nocontact_level with an EMA (so it adapts step-by-step but doesn’t jitter).
    def _update_levels_from_cycle(self):
        if self.curr_min < math.inf:
            self.min_hist.append(self.curr_min)
        if self.curr_max > -math.inf:
            self.max_hist.append(self.curr_max)

        if len(self.min_hist):
            new_contact = sorted(self.min_hist)[len(self.min_hist)//2]
            self.contact_level = (new_contact if self.contact_level is None
                                  else (1 - self.alpha) * self.contact_level + self.alpha * new_contact)
        if len(self.max_hist):
            new_noc = sorted(self.max_hist)[len(self.max_hist)//2]
            self.nocontact_level = (new_noc if self.nocontact_level is None
                                    else (1 - self.alpha) * self.nocontact_level + self.alpha * new_noc)

        self.curr_min = math.inf
        self.curr_max = -math.inf
# Compute the midpoint and hysteresis band (lower, upper) from the learned levels.
    def _recompute_bands(self):
        if (self.contact_level is None) or (self.nocontact_level is None):
            self.mid = self.lower = self.upper = None
            return
        rng = max(1e-9, abs(self.nocontact_level - self.contact_level))
        band = max(self.clip_band_min, min(self.clip_band_max, self.hfrac * rng))
        self.mid = 0.5 * (self.contact_level + self.nocontact_level)
        self.lower = self.mid - band
        self.upper = self.mid + band

    def update(self, v, t=None):
        """
        v: current raw sensor reading (FSR/pressure)
        t: timestamp in seconds (optional)
        """
        #print(v)
        if t is None:
            t = time.perf_counter()

        # track extrema in current dwell
        if v < self.curr_min:
            self.curr_min = v
        if v > self.curr_max:
            self.curr_max = v

        self._recompute_bands()
        dt_since_change = t - self.last_change_t

        # bootstrap
        if self.mid is None:
            if dt_since_change > 0.25:
                self._update_levels_from_cycle()
                self._recompute_bands()
            return self.state, self.lower, self.mid, self.upper

        # hysteresis + debounce + min dwell
        if self.state == 0:  # no-contact
            if v >= self.lower and dt_since_change >= self.min_dwell:
                if self.last_contact_tentative is None:
                    self.last_contact_tentative = t
                elif (t - self.last_contact_tentative) >= self.min_contact:
                    self._update_levels_from_cycle()
                    self.state = 1
                    self.last_change_t = t
                    self.last_contact_tentative = None
                    self.curr_min = v
                    self.curr_max = v
            else:
                self.last_contact_tentative = None
        else:  # contact
            if v <= self.upper and dt_since_change >= self.min_dwell:
                if self.last_release_tentative is None:
                    self.last_release_tentative = t
                elif (t - self.last_release_tentative) >= self.min_release:
                    self._update_levels_from_cycle()
                    self.state = 0
                    self.last_change_t = t
                    self.last_release_tentative = None
                    self.curr_min = v
                    self.curr_max = v
            else:
                self.last_release_tentative = None

        return self.state, self.lower, self.mid, self.upper


def low_pass_filter(new_value, last_filtered, alpha=0.1):
    return alpha * new_value + (1 - alpha) * last_filtered


## MAIN: Run the script #####################################################

from time import perf_counter


def unwrap_heading(
        IMU_angle,
        last_angle,
        unwrapped_angle,
        heading_anchor,
        last_state,
        time_now,
        pressure,
        Max_pressure,
        swaylimit=12,
        stable_time=3.0,
        stable_start=None,
        last_stable_angle=None
):
    """
    Unwrap the IMU heading and determine whether the user is
    walking or turning.

    States:
        1 = walking
        0 = turning

    Walking state:
        - Pressure follows Max_pressure.
        - If heading changes by more than swaylimit from the anchor,
          turning is detected and pressure becomes zero.

    Turning state:
        - Pressure remains zero.
        - If heading remains within 5 degrees for stable_time,
          turning is considered complete.
        - The current heading becomes the new heading anchor.
        - Pressure returns to Max_pressure.
    """

    # Use one timestamp throughout this function call
    current_time = perf_counter()

    # =========================================================
    # UNWRAP IMU HEADING
    # =========================================================

    dtheta = IMU_angle - last_angle

    if dtheta > 180:
        dtheta -= 360

    elif dtheta < -180:
        dtheta += 360

    new_unwrapped = unwrapped_angle + dtheta

    # =========================================================
    # INITIALISE RETURN VALUES
    # =========================================================

    state = last_state
    new_pressure = pressure
    new_anchor = heading_anchor

    new_stable_start = stable_start
    new_last_stable_angle = last_stable_angle

    # =========================================================
    # WALKING STATE
    # =========================================================

    if last_state == 1:

        # Keep output pressure synchronised with Max_pressure.
        # Therefore, pressing V or B immediately changes pressure.
        new_pressure = Max_pressure

        heading_difference = abs(
            new_unwrapped - heading_anchor
        )

        # Detect the beginning of a turn
        if heading_difference > swaylimit:

            state = 0
            new_pressure = 0

            # Initialise turning stability detection
            new_stable_start = None
            new_last_stable_angle = new_unwrapped

    # =========================================================
    # TURNING STATE
    # =========================================================

    elif last_state == 0:

        # Pressure must remain off while turning
        new_pressure = 0

        # Initialise the stability reference
        if last_stable_angle is None:

            new_last_stable_angle = new_unwrapped
            new_stable_start = current_time

        else:

            heading_drift = abs(
                new_unwrapped - last_stable_angle
            )

            # Heading is considered stable when its drift
            # remains below 5 degrees
            if heading_drift < 5.0:

                # Start the stability timer
                if stable_start is None:

                    new_stable_start = current_time

                # Heading has remained stable long enough
                elif current_time - stable_start >= stable_time:

                    state = 1
                    new_pressure = Max_pressure

                    # Current direction becomes the new anchor
                    new_anchor = new_unwrapped

                    # Reset stability variables
                    new_stable_start = None
                    new_last_stable_angle = None

            else:

                # Heading is still moving, so reset the timer
                new_last_stable_angle = new_unwrapped
                new_stable_start = None

    # =========================================================
    # INVALID STATE SAFETY
    # =========================================================

    else:

        state = 0
        new_pressure = 0
        new_stable_start = None
        new_last_stable_angle = new_unwrapped

    # =========================================================
    # RETURN UPDATED VALUES
    # =========================================================

    return (
        new_unwrapped,          # updated unwrapped heading
        IMU_angle,              # becomes last_angle
        state,                  # current state
        new_pressure,           # current pressure output
        new_anchor,             # updated heading anchor
        state,                  # becomes last_state
        current_time,           # updated time
        new_stable_start,       # stability timer
        new_last_stable_angle   # stability heading reference
    )
def unwrap_heading_old(IMU_angle, last_angle, unwrapped_angle,
                   heading_anchor, last_state, time_now, pressure, Max_pressure,
                   swaylimit=12, stable_time=3.0,
                   stable_start=None, last_stable_angle=None):
    """
    Unwrap heading and determine gait state with robust stability detection.

    State machine:
      - Walking (1): within sway limit -> pressure = 0.4
      - Turning (0): outside sway -> pressure= 0
        -> Once heading stops drifting for >= stable_time, 
           set new anchor and return to walking.
    """

    # --- Unwrap IMU angle ---
    dtheta = IMU_angle - last_angle
    if dtheta > 180:
        dtheta -= 360
    elif dtheta < -180:
        dtheta += 360
    new_unwrapped = unwrapped_angle + dtheta

    state = last_state
    new_pressure = pressure
    new_anchor = heading_anchor
    new_time_now = perf_counter()
    new_stable_start = stable_start
    new_last_stable_angle = last_stable_angle

    # --- Logic ---
    if last_state == 1:  # walking
        if abs(new_unwrapped - heading_anchor) > swaylimit:
            # left sway zone -> turning
            state, new_pressure = 0, 0
            new_stable_start = None
            new_last_stable_angle = new_unwrapped

    elif last_state == 0:  # turning
        # Has heading stopped drifting?
        if last_stable_angle is None:
            new_last_stable_angle = new_unwrapped
            new_stable_start = perf_counter()
        else:
            if abs(new_unwrapped - last_stable_angle) < 5.0:  # <5° drift, before it was 1deg
                if new_stable_start is None:
                    new_stable_start = perf_counter()
                elif perf_counter() - new_stable_start >= stable_time:
                    # Stable long enough -> resume walking
                    state, new_pressure = 1, Max_pressure
                    new_anchor = new_unwrapped
                    new_stable_start = None
                    new_last_stable_angle = None
            else:
                # Still drifting -> reset timer
                new_last_stable_angle = new_unwrapped
                new_stable_start = None

    return (new_unwrapped, IMU_angle, state, new_pressure,
            new_anchor, state, new_time_now, new_stable_start, new_last_stable_angle)



def within_30_percent(actual, expected):
    # Access the .value for arithmetic
    lower_bound = expected.value * 0.7
    upper_bound = expected.value * 1.3
    return lower_bound <= actual.value <= upper_bound



from time import perf_counter


class ActivityDetector:

    def __init__(self,
                 rSitThigh, rSitShank,
                 lSitThigh, lSitShank,
                 hipSit,
                 rStandThigh, rStandShank,
                 lStandThigh, lStandShank,
                 hipStand):

        # reference postures
        self.rSitThigh = rSitThigh
        self.lSitThigh = lSitThigh
        self.hipSit = hipSit

        self.rStandThigh = rStandThigh
        self.lStandThigh = lStandThigh
        self.hipStand = hipStand

        # previous knees
        self.prev_rk = None
        self.prev_lk = None
        self.sit_trend = 0
       # self.prev_hip = None

        self.last_move_time = perf_counter()

        # timing thresholds
        self.stop_delay = 0.8

        self.last_state = "STANDING"
        self.last_vv    = 2


    def detect_activity(self,
                        IMU_11, IMU_22,
                        IMU_33, IMU_44,
                        IMU_55,
                        gait_state):

        # joint angles
        right_knee = IMU_22 - IMU_11
        left_knee = IMU_44 - IMU_33

        right_thigh = IMU_11
        left_thigh = IMU_33
        hip_angle = IMU_55

        # ------------------------------------------------
        # POSTURE DETECTION
        # ------------------------------------------------

        sit_error = (
            abs(right_thigh - self.rSitThigh) +
            abs(left_thigh - self.lSitThigh) +
            abs(hip_angle - self.hipSit)
        )

        stand_error = (
            abs(right_thigh - self.rStandThigh) +
            abs(left_thigh - self.lStandThigh) +
            abs(hip_angle - self.hipStand)
        )

        if sit_error < stand_error * 0.7:
            posture = "SITTING"
        elif stand_error < sit_error * 0.7:
            posture = "STANDING"
        else:
            posture = "TRANSITION"

        # ------------------------------------------------
        # MOVEMENT DETECTION
        # ------------------------------------------------

        moving = False

        if self.prev_rk is not None:
            if abs(right_knee - self.prev_rk) > 3 or abs(left_knee - self.prev_lk) > 3:
                moving = True

        if moving:
            self.last_move_time = perf_counter()

        time_since_move = perf_counter() - self.last_move_time

        # ------------------------------------------------
        # STATE DECISION
        # ------------------------------------------------

        if posture == "SITTING":

            state = "SITTING"
            vv = 1

        elif posture == "TRANSITION":

            state = "TRANSITION"
            vv = 1.5

                        
        else:

            if gait_state == 0:
                state = "TURNING"
                vv = 4    
            elif moving:
                state = "WALKING"
                vv = 3

            elif time_since_move > self.stop_delay:
                state = "STANDING"
                vv = 2

            else:
                state = self.last_state
                vv =   self.last_vv 
        # update memory
      #  self.prev_hip = hip_angle
        self.prev_rk = right_knee
        self.prev_lk = left_knee
        self.prev_rt = right_thigh
        self.prev_lt = left_thigh
        self.last_state = state
        self.last_vv = vv

        return state, vv 

if __name__ == "__main__":
    
    switch = mp.Value('i', 1)    # 0 ----FSR, else Pressure Sensor
    while True:
        try:
            choice = int(input("Select input mode (0 = FSR, 1 = Pressure Sensor): "))
            if choice in (0, 1):
                switch.value = choice
                print(f"Mode set: {'Pressure Sensor' if choice == 1 else 'FSR'}")
                break
            else:
                print("Invalid input. Please enter 0 or 1 only.")
        except ValueError:
            print("Invalid input. Please enter a number (0 or 1).")
    
    
    # mp. = multiple processinge
    ENABLE_LIVEPLOT = 1  # 0 will not plot live
    imu_on = 1              # 1 means IMU will be attempted to connect, 0 otherwise
    
    heelR = mp.Value('i', 0) # right heel strike (HS) live state
    heelL = mp.Value('i', 0)
    toeR  = mp.Value('i', 0) # right toe strike (TS) live state
    toeL  = mp.Value('i', 0)
    HPeriod_available_R = mp.Value('i', 0) # check for three heel strike
    HPeriod_available_L = mp.Value('i', 0)
    HeelRp = mp.Value('d', 0) # average period between HS
    HeelLp = mp.Value('d', 0)
    TPeriod_available_R = mp.Value('i', 0) # check for three toe strike
    TPeriod_available_L = mp.Value('i', 0)     
    ToeRp = mp.Value('d', 0) # average period between TS
    ToeLp = mp.Value('d', 0)
    
    Allexit = mp.Value('i', 0) 

    gaitR = mp.Value('d', 0) # 
    gaitL = mp.Value('d', 0)
    Rallow = mp.Value('i', 0) # used in the sub code
    Lallow = mp.Value('i', 0)
    supportTimeR     = mp.Value('d', 0)     # when actuator R starts 
    unsupportTimeR   = mp.Value('d', 0)   # when actuator R stops
    supportTimeL     = mp.Value('d', 0)
    unsupportTimeL   = mp.Value('d', 0)
    supportTimeRAn   = mp.Value('d', 0)
    unsupportTimeRAn = mp.Value('d', 0) 
    supportTimeLAn   = mp.Value('d', 0)
    unsupportTimeLAn = mp.Value('d', 0)

    record_start_fd = mp.Value('i', 0)
    r_pressed = mp.Value('i', 0) # for recording
    
    R = mp.Value('d', 0)        # Pressure output from Digital regulator of the 1st muscle right
    L = mp.Value('d', 0)
    RR = mp.Value('d', 0)       # Pressure output from Digital regulator of the 2nd muscle right
    LL= mp.Value('d', 0)       
    Emg_sig = mp.Value('d', 3)  # trigger EMG
    Applied_pressure= mp.Value('d', 0)
    Stage_of_user =  mp.Value('d', 2)

    Lr = mp.Value('d', 0)       # Loadcell value for right leg
    Ll = mp.Value('d', 0)
    psRu = mp.Value('d', 0)     # Pressure reading 1 
    psRd = mp.Value('d', 0)     # Pressure reading 2
    psLu = mp.Value('d', 0)
    psLd = mp.Value('d', 0)
    
    IMU_11 = mp.Value('d', 0)      # x
    IMU_22 = mp.Value('d', 0)     
    IMU_33 = mp.Value('d', 0)
    IMU_44 = mp.Value('d', 0)
    IMU_55 = mp.Value('d', 0)

    IMU_1z = mp.Value('d', 0)     # z 
    IMU_2z = mp.Value('d', 0)     
    IMU_3z = mp.Value('d', 0)
    IMU_4z = mp.Value('d', 0)
    IMU_5z = mp.Value('d', 0)


    FSRrh = mp.Value('d', 0)    # FSR reading right heel (raw data)
    FSRrt = mp.Value('d', 0)
    FSRlh = mp.Value('d', 0)
    FSRlt = mp.Value('d', 0)
    c_time = mp.Value('d', 0)   # current time for DAQ


 
    rSitThigh = mp.Value('d', 0)    
    rSitShank = mp.Value('d', 0)
    lSitThigh = mp.Value('d', 0)
    lSitShank = mp.Value('d', 0)
    hipSit    = mp.Value('d', 0)   


    rStandThigh = mp.Value('d', 0)    
    rStandShank = mp.Value('d', 0)
    lStandThigh = mp.Value('d', 0)
    lStandShank = mp.Value('d', 0)
    hipStand    = mp.Value('d', 0)   
    

    rStrength = mp.Value('d', 0.4)    # starting Mary     0.4, 0.8
    rLength = mp.Value('d', 0.8)                # Tianyu  0.5, 0.9  
   
    lStrength = mp.Value('d', 0.4)   # starting  # 0.45, 0.7
    lLength = mp.Value('d', 0.8) #  0.1 0.4

    UserInfoGiven = mp.Value('d', 0)



    timeforlog = time.strftime("%Y%m%d-%H%M%S")
    LogFile = "All"+"_"+"Data"+"_"+timeforlog+".csv"


 #rSitThigh, rSitShank, lSitThigh, lSitShank,   rStandThigh,  rStandShank, lStandThigh,  lStandShank,  hipStand,   rStrength,  lStrength, rLength, lLength



## Execute Multiple Process ############################################################
    Daq = mp.Process(target=record_daq, args=(Allexit, record_start_fd, c_time, LogFile, Lr, Ll, psRu, psRd, psLu,psLd, FSRrh, FSRrt, FSRlh, FSRlt,switch,heelR,heelL, HeelRp, HeelLp,toeR,toeL, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL, IMU_11, IMU_22, IMU_33, IMU_44, IMU_55, IMU_1z, IMU_2z, IMU_3z, IMU_4z, IMU_5z,rSitThigh, rSitShank, lSitThigh, lSitShank,   rStandThigh,  rStandShank, lStandThigh,  lStandShank,  hipStand,   rStrength,  lStrength, rLength, lLength, R, L, RR, LL, Emg_sig
 ))
    # record_daq = function to record daq while updating variables
    # args = variables
    if switch.value != 0:
        Foot_pressure = mp.Process(target=Pressure_foot, args=(Allexit,  FSRrh, FSRrt, FSRlh, FSRlt))

    FSR = mp.Process(target=Period_FSR, args=(heelR,heelL,toeR,toeL,\
        HPeriod_available_R, HPeriod_available_L,HeelRp, HeelLp,Allexit,\
        TPeriod_available_R, TPeriod_available_L,ToeRp, ToeLp,gaitR, gaitL))
    # Period_FSR = get period of FSR
    T_to_walk = mp.Process(target=Timesforwalk, args=(\
        HPeriod_available_R, HPeriod_available_L,HeelRp, HeelLp,Allexit,\
        TPeriod_available_R, TPeriod_available_L,ToeRp, ToeLp,gaitR, gaitL,\
        Rallow, Lallow, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL,\
              supportTimeRAn, unsupportTimeRAn, supportTimeLAn,unsupportTimeLAn, rStrength, lStrength, rLength, lLength))
    # Timesforwalk = calculate gait period, actuation period 
    Activity_start = mp.Process(target=Activity, args=(heelR,heelL,toeR,toeL,\
        Allexit,\
        Rallow, Lallow, supportTimeR, unsupportTimeR, supportTimeL, unsupportTimeL,\
              supportTimeRAn, unsupportTimeRAn, supportTimeLAn,unsupportTimeLAn,\
                R, L, RR, LL, Emg_sig, r_pressed, IMU_11, IMU_22,IMU_33,IMU_44, IMU_5z,IMU_55, Applied_pressure,Stage_of_user, rSitThigh, rSitShank, lSitThigh, lSitShank, rStandThigh, rStandShank, lStandThigh, lStandShank, psRu, psRd, psLu, psLd, UserInfoGiven))
    # Walk = execute the actuation for walkings
   
    FSR.start() 
    print("FSR PID:", FSR.pid, "alive:", FSR.is_alive(), flush=True )
    # PID = process ID, alive = tell whether the function was executed.

    T_to_walk.start()
    print("T_to_walk PID:", T_to_walk.pid, "alive:", T_to_walk.is_alive(), flush=True )
    
    Activity_start.start()
    print("Activity start PID:", Activity_start.pid, "alive:", Activity_start.is_alive(), flush=True )

    Daq.start()   
    print("DAQ read start:", Daq.pid, "alive:", Daq.is_alive(), flush=True )

    if switch.value != 0:
         Foot_pressure.start()
         
         print("Foot Pressure Reading active:", Foot_pressure.pid, "alive:", Foot_pressure.is_alive(), flush=True )

    # Library for IMUs
    
    global quit
    global record_interval

    global IMU_1, IMU_2, IMU_3, IMU_4, IMU_5, IMU_5zz
    IMU_1, IMU_2, IMU_3, IMU_4, IMU_5, IMU_5zz = 0,0,0,0,0,0

    # IMU_1 = 0 # IMU_2 = 0 # IMU_3 = 0 # IMU_4 = 0 # IMU_5 = 0

    global time_flag
    time_flag = 0

    global record_start
    record_start = 0

    # global fa
    # global LogFile
    global f1, f2, f3, f4, f5 # files for IMUs
    global LogFile1, LogFile2, LogFile3, LogFile4, LogFile5 # internal logs for filing
    global timestr 

    global s1, s2, s3, s4, s5, t1now, t2now, t3now, t4now, t5now
    s1, s2, s3, s4, s5 = 1,1,1,1,1
    t1now, t2now, t3now, t4now, t5now = 0,0,0,0,0


    global rt, rs, lt, ls, hip
    rt, rs, lt, ls, hip = 90,90,90,90,90
    imu1_dt   = []
    imu1_data = []
    imu2_dt   = []
    imu2_data = []
    imu3_dt   = []
    imu3_data = []
    imu4_dt   = []
    imu4_data = []
    imu5_dt   = []
    imu5_data = []

    #global buffer_in 
    
    firsttime = 1
    record_interval = 0  
   
    if switch.value == 0: # FSR
        det_rh = AdaptiveFSR_old()  # Right Heel
        det_rt = AdaptiveFSR_old()  # Right Toe
        det_lh = AdaptiveFSR_old()  # Left Heel
        det_lt = AdaptiveFSR_old()  # Left Toe
    
    
    else: # pressure
        det_rh = AdaptiveFSR()  # Right Heel
        det_rt = AdaptiveFSR()  # Right Toe
        det_lh = AdaptiveFSR()  # Left Heel
        det_lt = AdaptiveFSR()  # Left Toe
         

    shared = {
    "Lr": Lr, "Ll": Ll,
    "R": R, "L": L, "RR": RR, "LL": LL,
    "psRu": psRu, "psRd": psRd, "psLu": psLu, "psLd": psLd,
    "FSRrh": FSRrh, "FSRrt": FSRrt, "FSRlh": FSRlh, "FSRlt": FSRlt,
    "heelR": heelR, "heelL": heelL, "toeR": toeR, "toeL": toeL,
    "HeelRp": HeelRp, "HeelLp": HeelLp,
    "supportTimeR": supportTimeR, "unsupportTimeR": unsupportTimeR,
    "supportTimeL": supportTimeL, "unsupportTimeL": unsupportTimeL,
    "IMU_11": IMU_11, "IMU_22": IMU_22, "IMU_33": IMU_33, "IMU_44": IMU_44, "IMU_55": IMU_55, "IMU_5z": IMU_5z 
    }

    if ENABLE_LIVEPLOT:
        from liveplot import live_plot
        plotter = mp.Process(target=live_plot, args=(shared, Allexit))
        plotter.start()
                
    # try = connect to all IMUs
    openzen.set_log_level(openzen.ZenLogLevel.Warning)
    
    detector = ActivityDetector(

    rSitThigh = rSitThigh.value,
    rSitShank = rSitShank.value,
    lSitThigh = lSitThigh.value,
    lSitShank = lSitShank.value,
    hipSit = hipSit.value,

    rStandThigh = rStandThigh.value,
    rStandShank = rStandShank.value,
    lStandThigh = lStandThigh.value,
    lStandShank = lStandShank.value,
    hipStand = hipStand.value
)

    try:      
        if (imu_on):
          (client, sensor1, imu1, sensor2, imu2, sensor3, imu3, sensor4, imu4, sensor5, imu5) = connectSensors()
          quit = False

        # If the connecton completes, ...
          data_thread = threading.Thread(target=data_acquisition, args=(client, imu1, imu2, imu3, imu4, imu5, IMU_11,IMU_22,IMU_33, IMU_44, IMU_55, IMU_1z, IMU_2z,IMU_3z,IMU_4z,IMU_5z))
          data_thread.start()
        file_record()       # only create new files if connections are successful
        c_time.value = 0 # current time
        
        #apply_pressure(0, 0.1, 0.1, 0.1, 0.1)    
        mlocal = 0
        r_pressed.value = 0
        print("\nPress R to start recording or Q to Stop or U to provide participant info or E to exit")
        print("\nZ for sit to stand support...")
        print("\nW for walk support...")
        print("\nO for stand to sit support...")
        print("\nU to provide IMU data...")
        print("\nC for provide time coefficients...")

        print("\n Right Heel - Toe - Left Heel - Toe - Right Thigh - Shank - Left Thigh - Shank - HipR - Hiplean - State - Pressure  - EMG")
        
        last_angle = 0
        unwrapped = 0
        heading_anchor = 0
        last_state = 1
        time_now = perf_counter()
        
        
        Max_pressure = 0.6 # max pressure during standing
        pressure = Max_pressure
        stable_start = None
        last_stable_angle = None
        heading_anchor = copy.copy(IMU_5z.value)

        user_info_given = 0
        gait_state = "Sitting"
        vv = 2
        Stage_of_user.value = vv

        c1 = 0
        c2 = 0
        c3 = 0
        c4 = 0

        timeforPressure = perf_counter()

        while True:
            
            raw_yaw = copy.copy(IMU_5z.value)  # from shared variable


            (unwrapped, last_angle, state, pressure,
             heading_anchor, last_state, time_now,
                stable_start, last_stable_angle) = unwrap_heading(
                   raw_yaw, last_angle, unwrapped,
                      heading_anchor, last_state, time_now, pressure, Max_pressure,
                             swaylimit=30, stable_time=.8,
                                     stable_start=stable_start,
                                         last_stable_angle=last_stable_angle
                )
            Applied_pressure.value = copy.copy(pressure)
           # print(f"Yaw={unwrapped:4.1f}, heading={heading_anchor:4.2f}, State={state}, Pressure={pressure:.2f}", end ='\r')
            #  print(f"State={state}, Pressure={pressure}, err={err_dbg:.1f} Yaw={raw_yaw:.2f}")

            # for recording ########################################################################################
            
     
            # IMU functions for detecting turning... can be placed here

            

            if keyboard.is_pressed('r'):                
                r_pressed.value = 1
                Emg_sig.value = 0
                if firsttime == 1:
                    
                    c_time.value = perf_counter() # record the current time from perf_counter()
                    record_interval = copy.copy(c_time.value)
                    firsttime = 0
                    print("\n\nRecording started -- Press Q to Stop: Press Z to get Sit to stand support, W to walk Support and O to Stand to sit support")
                    print("Right Heel - Toe - Left Heel - Toe - Right Thigh - Shank - Left Thigh - Shank - HipR - Hiplean - State - Pressure")
                record_start  = 1
                record_start_fd.value = 1
            # print("here")
            

            ## Calculate Threshold #################################################################################
            
            if True:#switch.value == 0:  ##############   FSR
                
               # if vv==1 or vv== 1.5 or vv==4:
               # now = time.perf_counter()
                
                #    state_RH, lo, mid, hi = det_rh.update(0)  # Right heel
                    
                 #   state_RT, _,  _,  _  = det_rt.update(0)  # Right toe
                    
                 #   state_LH, _,  _,  _  = det_lh.update(0)  # Left heel
                    
                #    state_LT, _,  _,  _  = det_lt.update(0)  # Left to
                #else:
                state_RH, lo, mid, hi = det_rh.update(FSRrh.value)  # Right heel
                
                state_RT, _,  _,  _  = det_rt.update(FSRrt.value)  # Right toe
                
                state_LH, _,  _,  _  = det_lh.update(FSRlh.value)  # Left heel
                
                state_LT, _,  _,  _  = det_lt.update(FSRlt.value)  # Left to
                    
                
                
                #"""
                if switch.value == 0:
                    heelR.value = 1- state_RH # inverting the state as heel strike produce 0 volt
                    toeR.value = 1- state_RT
                    heelL.value = 1- state_LH
                    toeL.value = 1- state_LT
                #"""
                else:  # pressure
                #if True:
                    heelR.value = state_RH # inverting the state as heel strike produce 0 volt
                    toeR.value = state_RT
                    heelL.value = state_LH
                    toeL.value = state_LT
                                     
           
               
           # print('     {:d},        {:d},       {:d},       {:d},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}'.format(int(heelR.value),  int(toeR.value), int(heelL.value),  int(toeL.value),float(IMU_1),  float(IMU_2), float(IMU_3),  float(IMU_4), float(IMU_5)), end ='\r' ) 
          #  print('     {:f},        {:f},       {:f},       {:f},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}'.format((FSRrh.value),  (FSRrt.value), (FSRlh.value),  (FSRlt.value),float(IMU_1),  float(IMU_2), float(IMU_3),  float(IMU_4), float(IMU_5)), end ='\r' ) 
          #  print('     {:d},        {:d},       {:d},       {:d},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}'.format(int(heelR.value),  int(toeR.value), int(heelL.value),  int(toeL.value),float(IMU_1),  float(IMU_2), float(IMU_3),  float(IMU_4), float(IMU_5)), end ='\r' ) 
           # print('     {:d},        {:d},       {:d},       {:d},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}, {:.3f}'.format(int(heelR.value),  int(toeR.value), int(heelL.value),  int(toeL.value),float(IMU_1z.value),  float(IMU_2z.value), float(IMU_3z.value),  float(IMU_4z.value), float(IMU_5z.value), float(pressure)), end ='\r' ) 
           # print('     {:d},        {:d},       {:d},       {:d},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}, {:.3f}, {}, {:.3f}'.format(int(heelR.value),  int(toeR.value), int(heelL.value),  int(toeL.value),float(IMU_11.value),  float(IMU_22.value), float(IMU_33.value),  float(IMU_44.value), float(IMU_5z.value),  float(IMU_55.value), {gait_state}, float(pressure)), end ='\r' ) 
           # print('     {:d},        {:d},       {:d},       {:d},      {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}, {:.3f}, {:1f}, {:.3f}, {:.3f}'.format(int(heelR.value),  int(toeR.value), int(heelL.value),  int(toeL.value),float(IMU_11.value),  float(IMU_22.value), float(IMU_33.value),  float(IMU_44.value), float(IMU_5z.value),  float(IMU_55.value), float(vv), float(pressure), float(Emg_sig.value)), end ='\r' ) 
            print('          {:.3f},     {:.3f},    {:.3f},    {:.3f}, {:.3f}, {:.3f}, {:1f}, {:.3f}, {:.3f}'.format(float(IMU_11.value),  float(IMU_22.value), float(IMU_33.value),  float(IMU_44.value), float(IMU_5z.value),  float(IMU_55.value), float(vv), float(pressure), float(Emg_sig.value)), end ='\r' ) 
        
         
         #   print('     {:.3f}, {:.3f}'.format( float(IMU_5z.value), float(THETA)), end ='\r' ) 
          #  print('            
            if keyboard.is_pressed('q') and r_pressed.value==1:
                        #taskAI.stop()
                        Emg_sig.value = 3
                        record_start  = 0
                        record_start_fd.value = 0
                        firsttime = 1
                
                        s1, s2, s3, s4, s5 = 1,1,1,1,1

               
                        print("\n Recording stopped")
                        r_pressed.value = 0
                                
                        # filing
                        mlocal = 0
                        print("\nPress R to record another trial, U to update participant info or E to Exit")
                        print("Right Heel - Toe - Left Heel - Toe - Right Thigh - Shank - Left Thigh - Shank - HipR - Hiplean - State - Pressure")
            
                        #while True:
                        # Analogs = taskAI.read()

            #if keyboard.is_pressed('z') :
             #    Emg_sig.value = 0
              #   print("EMG off, press R to on again")

            ## Exit the whole program ###################################################################            
            if keyboard.is_pressed('e') and r_pressed.value == 0:
                                quit = True
                                Allexit.value = 1 # to quit all mp.process
                                mlocal = 1
                                break
            
            if user_info_given ==1: 
                gait_state, vv = detector.detect_activity(
                    IMU_11.value,
                    IMU_22.value,
                    IMU_33.value,
                    IMU_44.value,
                    IMU_55.value,
                    state
                        )
                Stage_of_user.value = vv 
                
                """                   
                 statenow, rk, lk, hip, vv = detector.detect_state(
                        IMU_11.value,
                        IMU_22.value,
                        IMU_33.value,
                        IMU_44.value,
                        IMU_55.value
                    )
                 """
              #   print(f"State={statenow}, Right knee={rk:4.2f}, Left knee={lk:4.2f}, Hip={hip:4.2f}", end ='\r')
           
            current_time = perf_counter()

            if keyboard.is_pressed('v'):
                if current_time - timeforPressure > 1.0:
                    timeforPressure = current_time

                    Max_pressure = min(0.9, round(Max_pressure + 0.1, 1))

                    # Immediately update output pressure while walking
                    if state == 1:
                        pressure = Max_pressure

                    print("Max pressure increased:", Max_pressure)


            if keyboard.is_pressed('b'):
                if current_time - timeforPressure > 1.0:
                    timeforPressure = current_time

                    Max_pressure = max(0.1, round(Max_pressure - 0.1, 1))

                    # Immediately update output pressure while walking
                    if state == 1:
                        pressure = Max_pressure

                    print("Max pressure decreased:", Max_pressure)       

            
            if keyboard.is_pressed('c'):
                
                def ask_float(prompt):
                    v = input(prompt + " (or 'n' to skip): ")
                    if v.lower() == 'n' or v.strip() == "":
                        return None
                    try:
                        return float(v)
                    except:
                        print("Invalid input, skipped.")
                        return None
                
                print("\nEnter co efficients ...")

                v = ask_float("Right leg time 1")
                if v is not None: rStrength.value = v

                v = ask_float("Right leg time 2")
                if v is not None: rLength.value = v

                v = ask_float("Left leg time 1")
                if v is not None: lStrength.value = v

                v = ask_float("Left leg time 2")
                if v is not None: lLength.value = v
                
                print("\n--- You have entered ---")
                
                print(f"Right leg time 1 : {rStrength.value:.2f}")
                print(f"Right leg time 2 : {rLength.value:.2f}")
                
                print(f"Left  leg time 1 : {lStrength.value:.2f}")
                print(f"Left  leg time 2 : {lLength.value:.2f}") 
            
                print("\nenter 1 to save, 0 to cancel")
                while True:
                    try:
                        choice = int(input("Select  (0 not to save, 1 to save): "))
                        if choice in (0, 1):
                           # switch.value = choice 
                            #user_info_given = choice
                            #UserInfoGiven.value = choice
                            
                            if choice == 1:
                                 #rStrength.value = c1
                                 #rLength.value =  c2
                                 #lStrength.value = c3
                                 #lLength.value =  c4
                                 print("\n Saved")
                            else:
                                  rStrength.value = 0.4    # starting
                                  lStrength.value =  0.4   # starting
                                  rLength.value =  0.8   
                                  lLength.value = 0.8
                                  
                                  print("\n Not Saved")
                            #print ( user_info_given)
                            break
                        else:
                            print("Invalid input. Please enter 0 or 1 only.")
                    except ValueError:
                        print("Invalid input. Please enter a number (0 or 1).")



            if keyboard.is_pressed('u') and r_pressed.value == 0: 
                print("\nSit in neutral posture. Press ENTER to capture or 'n' to skip:")
                k = input()

                if k.lower() != 'n':
                    rSitThigh.value = IMU_11.value
                    rSitShank.value = IMU_22.value
                    lSitThigh.value = IMU_33.value
                    lSitShank.value = IMU_44.value
                    hipSit.value    = IMU_55.value

                    print("Sit posture captured.")
                    print(f"  R thigh : {rSitThigh.value:.2f}")
                    print(f"  R shank : {rSitShank.value:.2f}")
                    print(f"  L thigh : {lSitThigh.value:.2f}")
                    print(f"  L shank : {lSitShank.value:.2f}")
                    print(f"  Hip     : {hipSit.value:.2f}")
                else:
                    print("Sit posture skipped.")
                      
                print("\nStand upright. Press ENTER to capture or 'n' to skip:")
                k = input()

                if k.lower() != 'n':
                    rStandThigh.value = IMU_11.value
                    rStandShank.value = IMU_22.value
                    lStandThigh.value = IMU_33.value
                    lStandShank.value = IMU_44.value
                    hipStand.value    = IMU_55.value

                    print("Stand posture captured.")
                    print(f"  R thigh : {rStandThigh.value:.2f}")
                    print(f"  R shank : {rStandShank.value:.2f}")
                    print(f"  L thigh : {lStandThigh.value:.2f}")
                    print(f"  L shank : {lStandShank.value:.2f}")
                    print(f"  Hip     : {hipStand.value:.2f}")
                else:
                    print("Stand posture skipped.")
     




                
                
                detector = ActivityDetector(

                        rSitThigh = rSitThigh.value,
                        rSitShank = rSitShank.value,
                        lSitThigh = lSitThigh.value,
                        lSitShank = lSitShank.value,
                        hipSit = hipSit.value,

                        rStandThigh = rStandThigh.value,
                        rStandShank = rStandShank.value,
                        lStandThigh = lStandThigh.value,
                        lStandShank = lStandShank.value,
                        hipStand = hipStand.value
                    )
                while True:
                    try:
                        choice = int(input("Select  (0 = user_info_given, 1 = user_info_given): "))
                        if choice in (0, 1):
                           # switch.value = choice 
                            user_info_given = choice
                            UserInfoGiven.value = choice
                            print(f"Mode set: {'User info is considered as given' if choice == 1 else 'not given'}")
                            print ( user_info_given)
                            break
                        else:
                            print("Invalid input. Please enter 0 or 1 only.")
                    except ValueError:
                        print("Invalid input. Please enter a number (0 or 1).")
                

                
                
                print("\nPress R to record another trial, U to update participant info or E to Exit")
                print("\n Right Heel - Toe - Left Heel - Toe - Right Thigh - Shank - Left Thigh - Shank - HipR - Hiplean - State - Pressure  - EMG")
               

    ## If IMU connection fails, it will come here               
    except KeyboardInterrupt:
        pass
    ## If IMU connection succeeds and the program runs through, 
    finally:
        quit = True
        Allexit.value = 1 # to quit all mp.process
        if (imu_on):
            data_thread.join()
            print ("\nStreaming of sensor data complete")
            client.close()    
        f1.close()
        f2.close()
        f3.close()
        f4.close()
        f5.close()

        # To exit mp.process
        # To exit mp.process safely
        processes = [FSR, T_to_walk, Activity_start, Daq]

        if ENABLE_LIVEPLOT:
            processes.append(plotter)

        if switch.value != 0:
            processes.append(Foot_pressure)

        for p in processes:
            p.join(timeout=3)

        for p in processes:
            if p.is_alive():
                print(f"Process {p.name} did not stop. Terminating...")
                p.terminate()
                p.join(timeout=2)
                
        #old 
        #FSR.join()
        #T_to_walk.join()
        #Activity_start.join()
        #Daq.join()
        #if ENABLE_LIVEPLOT:
        #    plotter.join()
        
        #if switch.value != 0:
         #    Foot_pressure.join()
   # rd.join()


## SAVE FILES ###########################################################################
#########################################################################################

        a = pandas.read_csv(LogFile)
        b = pandas.read_csv(LogFile1)
        c = pandas.read_csv(LogFile2)
        d = pandas.read_csv(LogFile3)
        e = pandas.read_csv(LogFile4)
        f = pandas.read_csv(LogFile5)
        
        output4 = pandas.concat((a,b,c,d,e,f), axis='columns')
        
        output4 = output4.loc[:, ~output4.columns.str.contains("Unnamed")]        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_name = f"Alldata_{timestamp}.csv"
            
        output4.to_csv(file_name, index=False)                 
        
        df = pd.read_csv(LogFile)

    # Compute differences to detect time reset
        time_diff = df["Time"].diff()
        reset_indices = df.index[time_diff < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indices = [0] + reset_indices + [len(df)]

        # Create output folder
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indices) - 1):
            start_idx = reset_indices[i]
            end_idx = reset_indices[i + 1]
            trial_df = df.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"daq_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
            
            trial_df.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")
        
        dfrt = pd.read_csv(LogFile1)

    # Compute differences to detect time reset
        time_diffrt = dfrt["rtTime"].diff()
        reset_indicesrt = dfrt.index[time_diffrt < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indicesrt = [0] + reset_indicesrt + [len(dfrt)]

        # Create output folder
    # output_dir = "split_trials"
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indicesrt) - 1):
            start_idx = reset_indicesrt[i]
            end_idx = reset_indicesrt[i + 1]
            trial_df = dfrt.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"rt_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
        
            trial_df.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")

################################

        dfrs = pd.read_csv(LogFile2)

    # Compute differences to detect time reset
        time_diffrs = dfrs["rsTime"].diff()
        reset_indicesrs = dfrs.index[time_diffrs < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indicesrs = [0] + reset_indicesrs + [len(dfrs)]

        # Create output folder
        #output_dir = "split_trials"
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indicesrs) - 1):
            start_idx = reset_indicesrs[i]
            end_idx = reset_indicesrs[i + 1]
            trial_df = dfrs.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"rs_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
        
            trial_df.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")
                        
###################################
        dflt = pd.read_csv(LogFile3)

    # Compute differences to detect time reset
        time_difflt = dflt["ltTime"].diff()
        reset_indiceslt = dflt.index[time_difflt < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indiceslt = [0] + reset_indiceslt + [len(dflt)]

        # Create output folder
        #output_dir = "split_trials"
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indiceslt) - 1):
            start_idx = reset_indiceslt[i]
            end_idx = reset_indiceslt[i + 1]
            trial_df = dflt.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"lt_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
            
            trial_df.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")
                        
####################################################

        dfls = pd.read_csv(LogFile4)

    # Compute differences to detect time reset
        time_diffls = dfls["lsTime"].diff()
        reset_indicesls = dfls.index[time_diffls < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indicesls = [0] + reset_indicesls + [len(dfls)]

        # Create output folder
        #output_dir = "split_trials"
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indicesls) - 1):
            start_idx = reset_indicesls[i]
            end_idx = reset_indicesls[i + 1]
            trial_df = dfls.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"ls_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
        
            trial_df.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")
                        
################################################################

        dfh = pd.read_csv(LogFile5)

    # Compute differences to detect time reset
        time_diffh = dfh["hTime"].diff()
        reset_indicesh = dfh.index[time_diffh < -0.1].tolist()

        # Include start and end of DataFrame
        reset_indicesh = [0] + reset_indicesh + [len(dfh)]

        # Create output folder
        #output_dir = "split_trials"
        output_dir = f"Experiment_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Split and save each trial
        for i in range(len(reset_indicesh) - 1):
            start_idx = reset_indicesh[i]
            end_idx = reset_indicesh[i + 1]
            trial_df = dfh.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Use current timestamp or from data if available
            
            file_name = f"h_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            
            trial_df = trial_df.loc[:, ~trial_df.columns.str.contains("Unnamed")]
        
            trial_df.to_csv(file_path, index=False)
            
            print(f"Saved: {file_path}")
    ###################################################################
    # 
    # 
    #                        
    # cwd = os.getcwd() 
        #split_trials_dir = os.path.join(cwd, "..", "split_trials") 
        #input_dir = r"C:\Users\jf20027\Desktop\LocalDir\split_trials"
        #data_files = '../split_trials/'
        #csv_name = 'data.csv'
        
        base_dir = r"C:\Users\jf20027\Desktop\LocalDir"
        input_dir = os.path.join(base_dir, f"Experiment_{timestamp}")

        
        for i in range(len(reset_indices) - 1):
            
            #files = os.listdir(cwd)
            #print(cwd)
            #pd.read_csv(f"{data_files}{csv_name}")
            daq_file = os.path.join(input_dir, f"daq_{i+1}_{timestamp}.csv")
            rt_file  = os.path.join(input_dir, f"rt_{i+1}_{timestamp}.csv")
            rs_file  = os.path.join(input_dir, f"rs_{i+1}_{timestamp}.csv")
            lt_file  = os.path.join(input_dir, f"lt_{i+1}_{timestamp}.csv")
            ls_file  = os.path.join(input_dir, f"ls_{i+1}_{timestamp}.csv")
            h_file   = os.path.join(input_dir, f"h_{i+1}_{timestamp}.csv")
            
            daq_df = pd.read_csv(daq_file)
            rt_df = pd.read_csv(rt_file)
            rs_df = pd.read_csv(rs_file)
            lt_df = pd.read_csv(lt_file)
            ls_df = pd.read_csv(ls_file)
            h_df  = pd.read_csv(h_file)
            
            #file_name_daq= pandas.read_csv(f"daq_{i+1}_{timestamp}.csv")
            #file_name_rt = pandas.read_csv(f"rt_{i+1}_{timestamp}.csv")
            #file_name_rs = pandas.read_csv(f"rs_{i+1}_{timestamp}.csv")
            #file_name_lt = pandas.read_csv(f"lt_{i+1}_{timestamp}.csv")
            #file_name_ls = pandas.read_csv(f"ls_{i+1}_{timestamp}.csv")
            #file_name_h  = pandas.read_csv(f"h_{i+1}_{timestamp}.csv")
            output4 = pandas.concat((daq_df,rt_df,rs_df,lt_df,ls_df,h_df), axis='columns')
        
            output4 = output4.loc[:, ~output4.columns.str.contains("Unnamed")]        
            #output4.to_csv(f"trial_{i+1}_{timestamp}.csv", index=False)                 
        
            file_name = f"trial_{i+1}_{timestamp}.csv"
            file_path = os.path.join(output_dir, file_name)
            
            output4.to_csv(file_path, index=False)
            print(f"Saved: {file_path}")
        
        print("deleting unnecessary files...this might takes a while")
        LogFile1 = os.path.join(base_dir, f"LP_1_{timestr}.csv")
        if(os.path.exists(LogFile1) and os.path.isfile(LogFile1)):
                            os.remove(LogFile1)
        LogFile2 = os.path.join(base_dir, f"LP_2_{timestr}.csv")    
        if(os.path.exists(LogFile2) and os.path.isfile(LogFile2)):
                            os.remove(LogFile2)
                            #print("files deleted")
        LogFile3 = os.path.join(base_dir, f"LP_3_{timestr}.csv")                    
        if(os.path.exists(LogFile3) and os.path.isfile(LogFile3)):
                            os.remove(LogFile3)
        LogFile4 = os.path.join(base_dir, f"LP_4_{timestr}.csv")
        if(os.path.exists(LogFile4) and os.path.isfile(LogFile4)):
                            os.remove(LogFile4)
        
        LogFile5 = os.path.join(base_dir, f"LP_5_{timestr}.csv")                
        if(os.path.exists(LogFile5) and os.path.isfile(LogFile5)):
                            os.remove(LogFile5)
        LogFile = os.path.join(base_dir, f"All_Data_{timeforlog}.csv")
        if(os.path.exists(LogFile) and os.path.isfile(LogFile)):
                            os.remove(LogFile)
        

   # main()
    