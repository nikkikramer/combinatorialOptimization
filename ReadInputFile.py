#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 16:36:41 2021

@author: Case Team 18
"""

import pandas as pd
import re
import io 

def readInstanceFile(input_file):

    # read text input_file      
    with open(input_file, 'r') as file:
        data = file.read()
        #print(data)
    filename = input_file
    #retrieve all necessary data
    pattern_var = "DATASET\s*=\s*(.*)\n*NAME\s*=\s*(.*)\n*DAYS\s*=\s*(.*)\n*TRUCK_CAPACITY\s*=\s*(.*)\n*TRUCK_MAX_DISTANCE\s*=\s*(.*)\n*TRUCK_DISTANCE_COST\s*=\s*(.*)\n*TRUCK_DAY_COST\s*=\s*(.*)\n*TRUCK_COST\s*=\s*(.*)\n*TECHNICIAN_DISTANCE_COST\s*=\s*(.*)\n*TECHNICIAN_DAY_COST\s*=\s*(.*)\n*TECHNICIAN_COST\s*=\s*(.*)\n*MACHINES\s*=\s*(.*)\n*([\s\S]*?)LOCATIONS\s*=\s*(.*)\n*([\s\S]*?)REQUESTS\s*=\s*(.*)\n*([\s\S]*?)TECHNICIANS\s*=\s*(.*)\n*([\s\S]*?)\n*$"
    regex = re.compile(pattern_var)
    result = regex.match(data).groups()
    
    #store variables
    var_values = []
    for i in range(18):
        if i == 12 or i == 14 or i == 16:
            continue
        var_values.append(result[i])
    var_names = ['DATASET','NAME','DAYS','TRUCK_CAPACITY','TRUCK_MAX_DISTANCE','TRUCK_DISTANCE_COST','TRUCK_DAY_COST','TRUCK_COST','TECHNICIAN_DISTANCE_COST','TECHNICIAN_DAY_COST','TECHNICIAN_COST','MACHINES','LOCATIONS','REQUESTS','TECHNICIANS']
    var_dict = {'Variable': var_names, 'Value': var_values}
    df_var = pd.DataFrame(var_dict)
    #print(df_var)

    #store machine input variables in dataframe
    str_machines = io.StringIO(result[12])
    df_machines = pd.read_csv(str_machines, delim_whitespace=True, header=None, names=['machine_ID','size','idle_penalty'])
    #print(df_machines)
    
    #store location input variables in dataframe
    str_locations = io.StringIO(result[14])
    df_locations = pd.read_csv(str_locations, delim_whitespace=True, header=None, names=['loc_ID','x_loc','y_loc'])
    #print(df_locations)
    
    #store request input variables in dataframe
    str_requests = io.StringIO(result[16])
    df_requests = pd.read_csv(str_requests, delim_whitespace=True, header=None, names=['request_ID','loc_ID','first_day','last_day','machine_ID','machine_amount'])
    #print(df_requests)
    
    #store technician input variables in dataframe
    str_technicians= io.StringIO(result[18])
    df_technicians = pd.read_csv(str_technicians, delim_whitespace=True, header=None)
    cols = ['technician_ID','loc_ID','max_travel_dist','max_install_amount']
    i = 0
    for row in df_machines.iterrows():
        i += 1
        cols.append('machine_{}'.format(i))
    df_technicians.columns = cols
    df_technicians.rename(columns=dict(zip([0,1,2,3], cols)), inplace=True)
    #print(df_technicians)
    # a = df_technicians[df_technicians['technician_ID'] == 1]['max_install_amount'].item()
    # print(a)
    
    return df_var, df_machines, df_locations, df_requests, df_technicians, filename
   
def extractRequestInfo(df_requests, df_machines):
    #creating column with length of time period
    df_requests['time_window_length'] = df_requests['last_day'] - df_requests['first_day']
    
    #creating column with size of request
    machine_ID = df_requests['machine_ID']
    machine_size = []
    for index, value in machine_ID.iteritems():
        machine_size.append(int(df_machines[df_machines['machine_ID'] == value]['size']))
    machine_size = pd.Series(machine_size)
    machine_amount = df_requests['machine_amount']
    df_requests['request_size'] = machine_size*machine_amount
    
    #calculate pivot score 
    #TO DO: normalize terms & give weights to terms
    #df_requests['pivot_score'] = df_requests['time_window_length'] + df_requests['first_day']
    
    df_requests.sort_values(['first_day','time_window_length'], ascending=[True,True], inplace=True)
    
    # remaining columns in df_requests
    # ['request_ID', 'loc_ID', 'first_day', 'last_day', 'machine_ID', 'machine_amount', 'time_window_length', 'request_size']
    
    return df_requests

def main():
    # read file
    #readInstanceFile('CO_Case2021_01.txt')
    return
    
if __name__ == "__main__":
    main()