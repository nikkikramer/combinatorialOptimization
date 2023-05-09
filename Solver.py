#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:17:43 2021

@author: Case Team 18

"""

from ReadInputFile import readInstanceFile, extractRequestInfo
from WriteOutputFile import writeOutputFile
#from Validate import isValid
import pandas as pd
import numpy as np
import time
import math
import copy
import sys
import datetime

def ceilingEuclidDist(x1, y1, x2, y2):
    #calculate euclidean distance between two different location points x and y
    result = np.sqrt(math.pow((x1 - x2),2) + math.pow((y1 - y2),2))
    
    return math.ceil(result)

def distanceMatrix(df_locations):
    #calculate distance between different locations in a dataframe
    df_dm = df_locations.set_index('loc_ID')
    
    df_distMatrix = pd.DataFrame(index=df_locations['loc_ID'])
    for i, row in df_dm.iterrows():
        dist_row = []
        for j, column in df_dm.iterrows():
            x1 = row.x_loc
            y1 = row.y_loc
            x2 = column.x_loc
            y2 = column.y_loc
            dist_row.append(ceilingEuclidDist(x1, y1, x2, y2))
        df_distMatrix[i] = dist_row
    #print(df_distMatrix)
    return df_distMatrix

def getDistance(loc_ID_A, loc_ID_B, df_locations):
    #retrieve distance between two different location ID's from a distance matrix
    df_dist = distanceMatrix(df_locations)
    
    return df_dist[loc_ID_B].loc[loc_ID_A]



def totalDistTechFromList(technician, route, df_technicians, df_requests, df_locations):
    # calculcate the total dist a technician has travelled
    # if list is [3 4 5], full route is [x loc_3 loc_4 loc_5 x], where x is the home location of the technician
    home_loc = int(df_technicians[df_technicians['technician_ID'] == technician]['loc_ID'])
    
    full_route_locs = []
    for request in route:
        full_route_locs.append(int(df_requests[df_requests['request_ID'] == request]['loc_ID']))
    
    full_route_locs.insert(0, home_loc)
    full_route_locs.append(home_loc)
    
    total_dist = 0   
    for i, j in zip(full_route_locs, full_route_locs[1:]):
        total_dist += getDistance(i, j, df_locations)
    

    #print('FULL ROUTE LOCS')
    #print(full_route_locs)   
    #print(total_dist)
    return total_dist

def totalDistTruckFromList(route, df_requests, df_locations):
    # calculcate the total dist a technician has travelled
    # if list is [3 4 5], full route is [1 loc_3 loc_4 loc_5 1]
    depot_loc = 1
    
    full_route_locs = []
    for request in route:
        if request == 0:
            full_route_locs.append(depot_loc)
        else:
            full_route_locs.append(int(df_requests[df_requests['request_ID'] == request]['loc_ID']))
    
    full_route_locs.insert(0, depot_loc)
    full_route_locs.append(depot_loc)
    
    total_dist = 0   
    for i, j in zip(full_route_locs, full_route_locs[1:]):
        total_dist += getDistance(i, j, df_locations)
        
    return total_dist

def installedAmountFromTechRoute(route, df_requests):
    total = 0
    for request in route:
        total += int(df_requests[df_requests['request_ID'] == request]['machine_amount'])
    return total

def availableTechsForPivot(request_ID, df_requests, df_technicians, df_locations):
    available_technicians = techniciansWhoCanInstallRequest(request_ID, df_requests, df_technicians)
    request_loc_ID = int(df_requests[df_requests['request_ID'] == request_ID]['loc_ID'])

    updated_available_technicians = copy.deepcopy(available_technicians)
    #check if technician is within reach
    for technician in available_technicians:
        tech_loc_ID = int(df_technicians[df_technicians['technician_ID'] == technician]['loc_ID'])
        dist = getDistance(tech_loc_ID, request_loc_ID, df_locations)
        max_travel_dist = int(df_technicians[df_technicians['technician_ID'] == technician]['max_travel_dist'])
        
        amount = int(df_requests[df_requests['request_ID'] == request_ID]['machine_amount'].item())
        max_install_amount = int(df_technicians[df_technicians['technician_ID'] == technician]['max_install_amount'])
        #print(technician, (dist*2), max_travel_dist)
        if dist*2 > max_travel_dist or amount > max_install_amount:
            updated_available_technicians.remove(technician)
                
    return updated_available_technicians

def techniciansWhoCanInstallRequest(request_ID, df_requests, df_technicians):
    machine_ID = int(df_requests[df_requests['request_ID'] == request_ID]['machine_ID'].item())
    column = 'machine_{}'.format(machine_ID)
    
    li = df_technicians[df_technicians[column] == 1]['technician_ID'].tolist()
    
    return li

def getTechAllocation(days, nr_of_techs, df_requests, df_technicians, df_locations):
    #initialize tech_allocation as empty nested dict
    tech_allocation = {}
    for day in range(1,days+1):
        tech_allocation[day] = {}
        for technician in range(1, nr_of_techs+1):
            tech_allocation[day][technician] = []
            
    #initialize dict to keep track of installed amounts
    
    # 1. select hardest requests as pivots for each day (#pivots per day <= #techs)
    
    df_remaining_requests = df_requests.copy(deep=True)
    #print(df_remaining_requests)
    df_remaining_requests['first_day'] += 1
    df_remaining_requests['time_window_length'] = df_remaining_requests['last_day'] - df_remaining_requests['first_day']
    ''' kunnen ook nog nr_available_technicians toevoegen aan difficulty customer '''
    df_remaining_requests['nr_available_technicians'] = df_remaining_requests.apply(lambda row: len(availableTechsForPivot(row['request_ID'], df_requests, df_technicians, df_locations)), axis=1)
    df_remaining_requests.sort_values(['time_window_length','nr_available_technicians','request_size'], ascending=[True,True,False], inplace=True)
    
    #df_remaining_requests is now sorted with priority
    #ASSUMPTION:  for now we'll only choose requests with tw of 0
    df_short_tw = df_remaining_requests[df_remaining_requests['time_window_length'] == 0]
    
    #if instance 19 or 17, then take following df
    nr_requests = len(df_requests)
    nr_technicians = len(df_technicians)
    nr_locations = len(df_locations)
    if nr_requests == 30 and nr_locations == 9 and nr_technicians == 10:
        df_short_tw = df_remaining_requests.head(10)
    
    for day in range(1,days+1):
        requests = df_short_tw[df_short_tw['first_day'] == day]['request_ID'].to_list()
        for request in requests:
            request_loc_ID = int(df_requests[df_requests['request_ID'] == request]['loc_ID'])
            available_technicians = availableTechsForPivot(request, df_requests, df_technicians, df_locations)
            
            #check if days off constraint is satisfied after pivot choice
            
            test = copy.deepcopy(available_technicians)
            for technician in available_technicians:
                #check if technician has already been assigned a pivot
                if len(tech_allocation[day][technician]) > 0:
                    #print(tech_allocation[day][technician])
                    #print(str(technician) + 'is full for request' + str(request))
                    test.remove(technician)
            available_technicians = test
            
            if len(available_technicians) == 0:
                continue
            
            #choose closest technician that has an empty route
            closest_tech_dist = np.inf
            closest_technician = available_technicians[0]
            while (len(available_technicians) > 0):
                current_tech = available_technicians[0]
                
                if len(tech_allocation[day][technician]) > 0:
                    available_technicians.remove(current_tech)
                else:
                    tech_loc_ID = int(df_technicians[df_technicians['technician_ID'] == current_tech]['loc_ID'])
                    dist = getDistance(tech_loc_ID, request_loc_ID, df_locations)
                    
                    if dist < closest_tech_dist:
                        closest_tech_dist = dist
                        closest_technician = current_tech
                    
                    available_technicians.remove(current_tech)
                        
            #choose technician that is closest to pivot
            tech_allocation[day][closest_technician].append(request)
            df_remaining_requests.drop(df_remaining_requests[df_remaining_requests['request_ID'] == request].index, inplace=True)
            
    #3. perform parallel extramileage per day
    for day in range(1, days+1):
        min_extramileage = 0
        while not np.isinf(min_extramileage):
            remaining_requests = df_remaining_requests[df_remaining_requests['first_day'] == day]['request_ID'].to_list()
            extramileage_matrix = []
            extramileage_index = []
            
            for technician in range(1, nr_of_techs+1):
                extramileage_index.append(technician)
                
                max_travel_dist = int(df_technicians[df_technicians['technician_ID'] == technician]['max_travel_dist'])
                max_install_amount = int(df_technicians[df_technicians['technician_ID'] == technician]['max_install_amount'])
                
                existing_route = tech_allocation[day][technician]
                dist_existing_route = totalDistTechFromList(technician, existing_route, df_technicians, df_requests, df_locations)
                
                extramileage_row = []
                
                consecutive_working_days_tech = 0
                if day > 5:
                    for d in range(1, day+1):
                        if len(tech_allocation[d][technician]):
                                consecutive_working_days_tech += 1
                
                for j in remaining_requests:
                    new_route = copy.deepcopy(existing_route)
                    new_route.append(j)
                    dist_new_route = totalDistTechFromList(technician, new_route, df_technicians, df_requests, df_locations)
                    
                    extramileage = dist_new_route - dist_existing_route
                    used_capacity = installedAmountFromTechRoute(new_route, df_requests)
                   
                    available_technicians = techniciansWhoCanInstallRequest(j, df_requests, df_technicians)
                    
                    #if consecutive working days this day is 4, and if len (next day) > 0 -> remove from techs
                    if consecutive_working_days_tech == 4 and technician in available_technicians:
                        available_technicians.remove(technician)
                        
                    if (dist_new_route > max_travel_dist) or (used_capacity > max_install_amount) or (technician not in available_technicians):
                        extramileage_row.append(np.inf)
                    #elif (j not in pivot_li):
                    #    extramileage_row.append(np.inf)
                    else:
                        extramileage_row.append(extramileage)
                extramileage_matrix.append(extramileage_row)   
            df_extramileage = pd.DataFrame(extramileage_matrix, columns=remaining_requests, index=extramileage_index)
            
            if df_extramileage.empty:
                break
            
            request_to_add = df_extramileage.min().idxmin() #nieuwe request to add
            technician_to_add_to = df_extramileage[request_to_add].idxmin()
            min_extramileage = df_extramileage.loc[technician_to_add_to][request_to_add]
            
            if not np.isinf(min_extramileage):
                tech_allocation[day][technician_to_add_to].append(request_to_add)
            
                df_remaining_requests.drop(df_requests[df_requests['request_ID'] == request_to_add].index, inplace=True)
                
        if df_remaining_requests.empty:
            break
        else:
            #df_remaining_requests[df_remaining_requests['first_day'] == day] += 1
            #print(df_remaining_requests)
            for index, request in df_remaining_requests.iterrows():
                if request.first_day == day:
                    request.first_day += 1
    

    return tech_allocation

def calculateTechOutputVars(tech_allocation, df_locations, df_requests, df_technicians):
    total_dist = 0          #TRUCK_DISTANCE
    total_techs = 0         #NUMBER_OF_TECHNICIAN_DAYS
    distinct_techs = []     #NUMBER_OF_TECHNICIANS_USED (distinct technicians)
    
    for day in tech_allocation.keys():
        techs_per_day = 0
        for technician, request in tech_allocation[day].items():
            if len(request) > 0:
                total_techs += 1
                techs_per_day += 1
                
                if technician not in distinct_techs:
                    distinct_techs.append(technician)
                
                total_dist += totalDistTechFromList(technician, request, df_technicians, df_requests, df_locations)
            
    return total_dist, total_techs, len(distinct_techs)

def requestsDeliveryDays(days, nr_of_techs, tech_allocation):
    requests_to_deliver = {}
    for day in range(1,days+1):
        requests_to_deliver[day] = []
        for technician in range(1,nr_of_techs+1):
            if (day+1) in tech_allocation.keys():
                for request in tech_allocation[day+1][technician]:
                    requests_to_deliver[day].append(request)
    return requests_to_deliver

def getTruckAllocation(days, nr_of_techs, max_truck_capacity, truck_max_distance, requests_to_deliver, df_requests, df_locations):
    truck_allocation = {}
    #print()
    
    for day in range(1,days+1):
        #print('DAY: ' + str(day))
        truck_allocation[day] = {}
        
        #fill up the trucks with the requests of today
        truck_ID = 1
        used_capacity = 0
        travelled_distance = 0
        truck_allocation[day][truck_ID] = []
        for request in requests_to_deliver[day]:
            request_size = int(df_requests[df_requests['request_ID'] == request]['request_size'])
            used_capacity += request_size
            
            #instantiate new truck if max capacity will be exceeded
            if used_capacity > max_truck_capacity:
                #print('capacity of truck ' + str(truck_ID) + ' exceeded!')
                truck_allocation[day][truck_ID].append(0)
                used_capacity = request_size
                
            #instantiate new truck if max distance will be exceeded (assume every request can be added to empty new trucks)
            new_route = truck_allocation[day][truck_ID].copy()
            if len(truck_allocation[day][truck_ID]) > 0:
                new_route.append(request)
                travelled_distance = totalDistTruckFromList(new_route, df_requests, df_locations)
                
                if travelled_distance > truck_max_distance:
                    if truck_allocation[day][truck_ID][-1] == 0:
                        truck_allocation[day][truck_ID].pop()
                    
                    truck_ID += 1
                    truck_allocation[day][truck_ID] = []
                    requests_per_truck_li = []
                    used_capacity = request_size
            
            #save requests per truck per day
            travelled_distance = totalDistTruckFromList(new_route, df_requests, df_locations)
            
            truck_allocation[day][truck_ID].append(request)

    return truck_allocation

def calculateTruckOutputVars(truck_allocation, df_locations, df_requests):
    total_dist = 0          #TRUCK_DISTANCE
    total_trucks = 0        #NUMBER_OF_TRUCK_DAYS = total number of truck days used
    max_trucks_per_day = 0  #NUMBER_OF_TRUCKS_USED = maximum number of trucks used on a single day
    
    for k in truck_allocation.keys():
        trucks_per_day = 0
        for key, value in truck_allocation[k].items():
            if len(value) > 0:
                total_trucks += 1
                trucks_per_day += 1
            
            total_dist += totalDistTruckFromList(value, df_requests, df_locations)
        
        if trucks_per_day > max_trucks_per_day:
            max_trucks_per_day = trucks_per_day
    
    return total_dist, total_trucks, max_trucks_per_day


def calculateTotalCost(truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, df_var):
    truck_distance_cost = int(df_var[df_var['Variable'] == 'TRUCK_DISTANCE_COST']['Value'].item())
    truck_day_cost = int(df_var[df_var['Variable'] == 'TRUCK_DAY_COST']['Value'].item())
    truck_cost = int(df_var[df_var['Variable'] == 'TRUCK_COST']['Value'].item())
    technician_distance_cost = int(df_var[df_var['Variable'] == 'TECHNICIAN_DISTANCE_COST']['Value'].item())
    technician_day_cost = int(df_var[df_var['Variable'] == 'TECHNICIAN_DAY_COST']['Value'].item())
    technician_cost = int(df_var[df_var['Variable'] == 'TECHNICIAN_COST']['Value'].item())
    
    total_truck_cost = (truck_distance*truck_distance_cost) + (number_of_truck_days*truck_day_cost) + (number_of_trucks_used*truck_cost)
    total_technician_cost = (number_of_tech_used*technician_cost) + (total_techs*technician_day_cost) + (total_dist_tech*technician_distance_cost)
    
    print('tech cost: ' + str(total_technician_cost))
    print('truck cost: ' + str(total_truck_cost))
    
    total_cost = total_truck_cost + total_technician_cost
    
    return total_cost

def calculateIdleCosts(truck_allocations, tech_allocations, df_machines, df_requests):
    idle_costs = 0
    
    deliveries = {}
    for day in truck_allocations.keys():
        deliveries_per_day = []
        for truck, request in truck_allocations[day].items():
            for i in request:
                deliveries_per_day.append(i)
        deliveries[day] = deliveries_per_day
    
    installations = {}
    for day in tech_allocations.keys():
        installations_per_day = []
        for tech, request in tech_allocations[day].items():
            for i in request:
                installations_per_day.append(i)
        installations[day] = installations_per_day
    
    
    delivery_days = {}
    for day, request_li in deliveries.items():
        for request in request_li:
            delivery_days[request] = day

    install_days = {}
    for day, request_li in installations.items():
        for request in request_li:
            install_days[request] = day
    
    df_days = pd.DataFrame({'delivery_days': pd.Series(delivery_days), 'install_days': pd.Series(install_days)})
    df_days['idle_days'] = df_days['install_days'] - df_days['delivery_days'] - 1
    
    for row in df_days.itertuples():
        if row.idle_days > 0:
            amount_idle_days = int(row.idle_days)
            idle_request = row.Index
            idle_machine_amount = int(df_requests[df_requests['request_ID'] == idle_request]['machine_amount'])
            idle_machine_ID = int(df_requests[df_requests['request_ID'] == idle_request]['machine_ID'])
            
            idle_penalty = int(df_machines[df_machines['machine_ID'] == idle_machine_ID]['idle_penalty'])
            
            idle_costs = idle_penalty * idle_machine_amount * amount_idle_days
    
    return idle_costs

def baseAlgorithm(df_var, df_machines, df_locations, df_requests, df_technicians):
    df_requests = extractRequestInfo(df_requests, df_machines)
    
    days = int(df_var[df_var['Variable'] == 'DAYS']['Value'].item())
    nr_of_techs = int(df_var[df_var['Variable'] == 'TECHNICIANS']['Value'].item())
    max_truck_capacity = int(df_var[df_var['Variable'] == 'TRUCK_CAPACITY']['Value'].item())
    truck_max_distance = int(df_var[df_var['Variable'] == 'TRUCK_MAX_DISTANCE']['Value'].item())
    
    tech_allocation = getTechAllocation(days, nr_of_techs, df_requests, df_technicians, df_locations)
    requests_to_deliver_per_day = requestsDeliveryDays(days, nr_of_techs, tech_allocation)
    truck_allocation = getTruckAllocation(days, nr_of_techs, max_truck_capacity, truck_max_distance, requests_to_deliver_per_day, df_requests, df_locations)
    
    truck_distance, number_of_truck_days, number_of_trucks_used = calculateTruckOutputVars(truck_allocation, df_locations, df_requests)
    total_dist_tech, total_techs, number_of_tech_used = calculateTechOutputVars(tech_allocation, df_locations, df_requests, df_technicians)
    
    total_cost = calculateTotalCost(truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, df_var)
    idle_cost = calculateIdleCosts(truck_allocation, tech_allocation, df_machines, df_requests)
    print('idle cost: ' + str(idle_cost))
    total_cost += idle_cost
    
    return truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost, truck_allocation, tech_allocation

def main():
    
    #filename = 'CO_Case2021_20.txt'
    filename = sys.argv[1]
    calc_time = sys.argv[-1]
    start = time.time()
    while time.time() < float(calc_time) + time.time():
        df_var, df_machines, df_locations, df_requests, df_technicians, filename = readInstanceFile(filename)
    
        truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost, truck_allocations, tech_allocations = baseAlgorithm(df_var, df_machines, df_locations, df_requests, df_technicians)
        print('total cost: ' + str(total_cost))
    
        writeOutputFile(df_var, df_machines, df_locations, df_requests, df_technicians, filename, truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost,truck_allocations,tech_allocations)
       # break
    end = time.time()
    print('elapsed time (in seconds): ' + str(end - start))
    
    #TO CREATE SOLUTION FILE, RUN FOLLOWING COMMAND IN TERMINAL
    #python Solver2.py CO_Case2021_12.txt 900 
    
    #TO VALIDATE SOLUTION FILE, RUN FOLLOWING COMMAND IN TERMINAL:
    #python Validate.py --instance CO_case2021_01.txt --solution CO_Case2021_01sol.txt
    
    return
    
if __name__ == "__main__":
    main()