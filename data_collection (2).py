import time
import io
import pandas as pd
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
import csv
import sys
import numpy as np
import os
import sys
import smbus
from imusensor.MPU9250 import MPU9250
from datetime import datetime
import math
import warnings
warnings.simplefilter(action='ignore')

# Load the public and private keys
adbkey = '/home/mse/key'
with open(adbkey) as f:
    priv = f.read()
with open(adbkey + '.pub') as f:
     pub = f.read()
signer = PythonRSASigner(pub, priv)

local_path="/home/mse/wifi_logs/"

# Connect
#device1 = AdbDeviceTcp('192.168.1.8', 5555, default_transport_timeout_s=9.)
#device2 = AdbDeviceTcp('192.168.1.17', 5555, default_transport_timeout_s=9.)
device1 = AdbDeviceTcp('10.91.36.169', 5555, default_transport_timeout_s=9.)
device2 = AdbDeviceTcp('10.91.23.251', 5555, default_transport_timeout_s=9.)
device1.connect(rsa_keys=[signer], auth_timeout_s=0.1)
device2.connect(rsa_keys=[signer], auth_timeout_s=0.1)
device_dict={1:device1, 2:device2}
avg_df=pd.DataFrame(columns=['WindowStart', 'WindowEnd','Device1_AvgDist','Device2_AvgDist'])



def start_log(device_num):
     device=device_dict[device_num]
     device.shell('input keyevent 37') #start new session
     #time.sleep(0.5)
     device.shell('input keyevent 47') #start collection

def stop_log(device_num):
     device=device_dict[device_num]
     device.shell('input keyevent 46') #stop collection


def pull_log(device_num):
     device=device_dict[device_num]
     if device_num==1:
          log_file=device.shell('ls /storage/emulated/0/Android/data/com.welwitschia.wifirttscanX/files/logfiles')
          path1='/storage/emulated/0/Android/data/com.welwitschia.wifirttscanX/files/logfiles/'+log_file
     elif device_num==2:
          log_file=device.shell('ls /storage/emulated/0/Android/data/com.example.wifirttscanX/files/log')
          path1='/storage/emulated/0/Android/data/com.example.wifirttscanX/files/log/'+log_file
          #log_file=device.shell('ls /storage/emulated/0/Android/data/com.welwitschia.wifirttscanX/files/logfiles')
          #path1='/storage/emulated/0/Android/data/com.welwitschia.wifirttscanX/files/logfiles/'+log_file
     command=str('cat '+path1) #be extra mindful of the backslash
     
     buffer1= device.shell(command)
     #print(buffer1)
     #device.shell('input keyevent 46') #stop collection
     #time.sleep(0.5)
     device.shell('input keyevent 31') #delete all log files; this equals clearing buffer
     #time.sleep(0.5)

     log_file=local_path+"dev"+str(device_num)+log_file.rstrip()
     f=open(log_file,'w')
     f.write(buffer1)
     f.close()
     return log_file
     
def attach_log(log_file1,log_file2, log_imu=None):
     global avg_df
     df1=pd.read_csv(log_file1, index_col=False)
     df1=process_log(df1)
     df2=pd.read_csv(log_file2, index_col=False)
     df2=process_log(df2)

     if not df1.empty:
          start_time=df1['time_in_ms'].iloc[0] #use device1's first data point as absolute zero
          end_time=df1['time_in_ms'].iloc[-1] 
          if (not df2.empty) & (df2['time_in_ms'].iloc[-1]>end_time):
               end_time=df2['time_in_ms'].iloc[-1]
     elif (not df2.empty):
          start_time=df2['time_in_ms'].iloc[0] 
          end_time=df2['time_in_ms'].iloc[-1]
     else:
          return
          
     df_box=pd.DataFrame(columns=['WindowStart', 'WindowEnd','time_in_ms','Distance','Device'])
     
     time=start_time
     while time<end_time:
          df_slice1=df1.loc[(df1['time_in_ms']>=time) & (df1['time_in_ms']<=(time+500))]
          if not df_slice1.empty:
               df_slice1['WindowStart']=time
               df_slice1['WindowEnd']=time+500
               df_slice1['Device']=1
               df_box=pd.concat([df_box,df_slice1], ignore_index=True)
          df_slice2=df2.loc[(df2['time_in_ms']>=time) & (df2['time_in_ms']<=(time+500))]
          if not df_slice2.empty:
               df_slice2['WindowStart']=time
               df_slice2['WindowEnd']=time+500
               df_slice2['Device']=2
               df_box=pd.concat([df_box,df_slice2], ignore_index=True)

          time+=500
     #print(df_box)
     
     df_grouped=df_box.groupby(['WindowStart', 'WindowEnd','Device'])['Distance'].agg(['mean'])
     df_grouped=df_grouped.reset_index()
     
     df_grouped_wind=df_grouped.groupby(['WindowStart', 'WindowEnd'])
     

     #avg_temp=pd.DataFrame(columns=['WindowStart', 'WindowEnd','Device1_AvgDist','Device2_AvgDist'])
     for name, group in df_grouped_wind:
          df_dev1=group.loc[group['Device']==1]
         
          if not df_dev1.empty:
               mean1=df_dev1['mean'].values[0]
               #print("mean from 1", mean1)
          else:
               mean1=np.nan
          df_dev2=group.loc[group['Device']==2]     
          if not df_dev2.empty:
               mean2=df_dev2['mean'].values[0]
          else:
               mean2=np.nan
          avg_temp=pd.DataFrame([[group['WindowStart'].values[0], group['WindowEnd'].values[0], mean1,mean2]],columns=['WindowStart', 'WindowEnd','Device1_AvgDist','Device2_AvgDist'])
          #print(avg_temp)
          avg_df=pd.concat([avg_df,avg_temp], ignore_index=True)
          
     #print(avg_df)


def process_log(df):
     df=df[:-1]
     df['time_in_ms']=df['Time'].apply(lambda x: int(x[:2])*3600000+ int(x[3:5])*60000+ int(x[6:8])*1000+ int(x[9:]))
     df=df[['Time','Distance', 'time_in_ms']]
     df=df.drop(df[df.Distance==0].index)
     df=df.sort_values(by='time_in_ms')
     return df

def plannedPathMode():
     
     while(1):
          time.sleep(3)
          print("start")
          start_log(1)
          start_log(2)
          time.sleep(10) #measure for ~10 sec
          stop_log(1)
          stop_log(2)
          print("stopping")
          log1=pull_log(1)
          log2=pull_log(2)
          
          attach_log(log1, log2)
          time.sleep(2) 
          time.sleep(3.5) #measured movement time of robot
def imuBasicMode():
     address = 0x68
     bus = smbus.SMBus(1)
     imu = MPU9250.MPU9250(bus, address)
     imu.begin()
     logging=False
     imu.readSensor()
     old_x=imu.AccelVals[0]
     old_y=imu.AccelVals[1]
     start= time.time()
     while True:
          imu.readSensor()
          #imu.computeOrientation()          
          if (abs(imu.AccelVals[0]-old_x)>0.1) | (abs(imu.AccelVals[1]-old_y)>0.1):
               #imu starts to move
               stop_log(1)
               stop_log(2)
               log1=pull_log(1)
               log2=pull_log(2)
               attach_log(log1, log2)
               logging=False
          else:
               #imu stops moving
               if logging==False:
                    start_log(1)
                    start_log(2)
                    logging=True
          old_x=imu.AccelVals[0]
          old_y=imu.AccelVals[1]
          time.sleep(0.5)
     
def imuAdvancedMode():
     while(1):
          start_log(1)
          start_log(2)
          log_imu=start_imu()
          stop_log(1)
          stop_log(2)
          
          log1=pull_log(1)
          log2=pull_log(2)
          
          attach_log(log1, log2,log_imu)

          time.sleep(3.5) #measured movement time of robot
def start_imu():
     df_imu=pd.DataFrame(columns=['time_in_ms','imu_Heading','imu_Distance'])
     address = 0x68
     bus = smbus.SMBus(1)
     imu = MPU9250.MPU9250(bus, address)
     imu.loadCalibDataFromFile("/home/mse/calib.json")
     imu.begin()
     start= time.time()
     
     while (time.time())-start<10:
          imu.readSensor()
          now=datetime.now()
          imu.computeOrientation()
          angle=math.atan2(imu.MagVals[1],imu.MagVals[0])
          if angle>=0:
               angle=angle*(180/math.pi)
          else:
               angle=(angle+2*math.pi)*(180/math.pi)
          if (angle>350):
               angle=360-angle

          now_ms=(now.hour*3600000)+(now.minute*60000)+(now.second*1000)
          df_temp=pd.DataFrame([[now_ms,angle,np.nan]],columns=['time_in_ms','imu_Heading','imu_Distance'] )
          df_imu=pd.concat([df_imu,df_temp], ignore_index=True)
          time.sleep(0.2)
     print(df_imu)
     return(df_imu)

          
def main():   
     args=sys.argv[1:]
     if args[0]=='-m':
          if args[1]=='0':
               print('here')
               plannedPathMode()
          elif args[1]=='1':
               imuBasicMode()
          elif args[1]=='2':
               imuAdvancedMode()


if __name__=="__main__":
     main()
          
          
          
          
          
          
          
          
          
          
          
          
          
          
