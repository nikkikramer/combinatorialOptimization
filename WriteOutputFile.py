#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 16:40:22 2021

@author: Case Team 18
"""

#from ReadInputFile import readInstanceFile
#from Solver import baseAlgorithm
#import Solver

def writeOutputFile(df_var, df_machines, df_locations, df_requests, df_technicians, filename, truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost, truck_allocations,tech_allocations):
    name = df_var[df_var['Variable'] == 'NAME']['Value'].item()
    dataset_name = df_var[df_var['Variable'] == 'DATASET']['Value'].item()
    
    file = open(filename[:-4] + 'sol.txt', 'w+') 
    file.write('DATASET = ' + str(dataset_name) + '\n')
    file.write('NAME = '+ str(name) + '\n') 
    file.write('\n')
    
    file.write('TRUCK_DISTANCE = '+ str(truck_distance) + ' \n')
    file.write('NUMBER_OF_TRUCK_DAYS = '+ str(number_of_truck_days) + ' \n')
    file.write('NUMBER_OF_TRUCKS_USED = '+ str(number_of_trucks_used) + ' \n')
    file.write('TECHNICIAN_DISTANCE = '+ str(total_dist_tech) + '\n')
    file.write('NUMBER_OF_TECHNICIAN_DAYS = '+ str(total_techs) + '\n')
    file.write('NUMBER_OF_TECHNICIANS_USED = ' + str(number_of_tech_used)+ '\n')
    file.write('IDLE_MACHINE_COSTS = ' + str(idle_cost) + '\n')
    file.write('TOTAL_COST = '+ str(total_cost)+ '\n')
    
    for k in tech_allocations.keys():
        file.write('\n')
        #print(k) #prints days
        file.write('DAY = ' + str(k) + '\n')
        number_of_trucks = 0
        for key1, value1 in truck_allocations[k].items():
            if value1:
                number_of_trucks += 1
        #print(number_of_trucks)
        file.write('NUMBER_OF_TRUCKS = ' + str(number_of_trucks))
        if number_of_trucks == 0:
            file.write('\n')
        else:
            file.write('\n')
            for key1, value1 in truck_allocations[k].items():
                file.write(str(key1) + ' ')
                for item in value1:
                    file.write(str(item) + ' ')
                file.write('\n')
                        
        number_of_technicians = 0
        for key, value in tech_allocations[k].items():
            if value:
                number_of_technicians += 1
        #print(number_of_technicians)
        file.write('NUMBER_OF_TECHNICIANS = ' + str(number_of_technicians))
        if number_of_technicians == 0:
            file.write('\n')
        else:
            file.write('\n')
            for key, value in tech_allocations[k].items():
                if value:
                    file.write(str(key) + ' ')
                    for item in value:
                        file.write(str(item) + ' ')
                file.write('\n')
 
    file.close()
    
    return 
    
def main():
    #df_var, df_machines, df_locations, df_requests, df_technicians, filename = readInstanceFile('CO_Case2021_14.txt')
    
    #truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost, truck_allocations, tech_allocations = Solver.baseAlgorithm(df_var, df_machines, df_locations, df_requests, df_technicians)
    #number_of_tech_used, total_techs, total_dist_tech = Solver.baseAlgorithm(df_var, df_machines, df_locations, df_requests, df_technicians)
    
    #writeOutputFile(df_var, df_machines, df_locations, df_requests, df_technicians, filename, truck_distance, number_of_truck_days, number_of_trucks_used, number_of_tech_used, total_techs, total_dist_tech, idle_cost, total_cost,truck_allocations,tech_allocations)
    
    return
    
if __name__ == "__main__":
    main()