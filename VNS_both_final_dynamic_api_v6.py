﻿# -*- coding: utf-8 -*-
"""
@author: yanglan

插入法+VNS
"""
"""
先出机场后去机场的模式：

曼哈顿距离
速度设为30公里每小时, 8.33米每秒
使用总行驶距离作为成本，使用行驶时间矩阵计算时间窗等

入机场者：
"xx-xx时间段内上车出发"，取出租车上车时间的前5分钟，后10分钟
行驶时间不超过单人单车直达的1.5倍

出机场者：
出发时间窗设定为出租车出发时间的前5分钟，后10分钟
到达时间窗设为行驶距离不超过单人单车直达的行驶距离的1.5倍

每个顾客点的服务时间为半分钟
输出：车辆数，每个路线的顾客点编号顺序，在每个点的时间范围（出发时间范围，回机场时间范围，到达每个顾客点的时间范围）, 总路程的平均乘客数
"""
"""
删掉了之前的程序中所有用于debug的注释
"""

import time
import math
import numpy as np
import copy

# import pylab
from matplotlib import pylab
import matplotlib.transforms as mtransforms

import urllib2
import json
import logging

import read_file_py
import someclass
# import check2distance

car_capacity = 7
service_time = 30
# 最大时间窗空余量
max_timeWindow_interval = 60
# 最大等待时间
max_waiting_time = 3600
# 假设固定速度
velocity = 8.33

maxIteration = 7

# 选取时间段
time_point_in_1 = "2015-08-03 18:00:00"
time_point_in_2 = "2015-08-03 18:30:00"

time_point_out_1 = "2015-08-03 16:00:00"
time_point_out_2 = "2015-08-03 16:30:00"


def getUrl_multiTry( url ):
    # user_agent ='"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36"'
    user_agent = '"Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"'
    headers = {'User-Agent': user_agent}
    maxTryNum = 10
    for tries in range( maxTryNum ):
        try:
            req = urllib2.Request( url, headers = headers )
            html = urllib2.urlopen( req ).read()
            break
        except:
            if tries < (maxTryNum - 1):
                continue
            else:
                logging.error( "Has tried %d times to access url %s, all failed!", maxTryNum, url )
                break

    return html

def check2distance(a, distance_dictionary):
    airport=someclass.Demand('airport',np.array([113.814, 22.623]),None,None)
    can_insert = 1
    check_complete=0
    # expected_return_time=0
    time_list = []
    # if a.route_list[0].service_type==True:
    if 'airport' + '_' + a.route_list[0].id not in distance_dictionary.keys():
        distance_dictionary=airport.update_distance_dictionary(a.route_list[0],distance_dictionary)
    whole_distance = distance_dictionary['airport' + '_' + a.route_list[0].id]
    time_list.append(whole_distance)
    if len(a.route_list) == 1:
        whole_distance = whole_distance + distance_dictionary[a.route_list[0].id + '_' + 'airport']
        time_list.append(whole_distance)
    else:
        # while can_insert == 1 and check_complete==0:
        if len(a.route_list)<10:
            for k in range(0, len(a.route_list) - 1):
                if a.route_list[k].id + '_' + a.route_list[k + 1].id not in distance_dictionary.keys():
                    distance_dictionary=a.route_list[k].update_distance_dictionary(a.route_list[k+1],distance_dictionary)
                whole_distance = whole_distance + distance_dictionary[
                    a.route_list[k].id + '_' + a.route_list[k + 1].id]
                time_list.append( whole_distance )

                if 'airport' + '_' + a.route_list[k+1].id not in distance_dictionary.keys():
                    distance_dictionary=airport.update_distance_dictionary(a.route_list[k+1],distance_dictionary)
                if a.route_list[k+1].service_type==True:
                    if whole_distance > 2 * distance_dictionary['airport' + '_' + a.route_list[k+1].id]:
                        time_list = []
                        can_insert = 0
                        break
                    # else:
                    #     check_complete=1

                if k == len( a.route_list ) - 2:
                    if a.route_list[k + 1].id + '_' + 'airport' not in distance_dictionary.keys():
                        distance_dictionary = a.route_list[k + 1].update_distance_dictionary( airport,
                                                                                              distance_dictionary )
                    whole_distance = whole_distance + distance_dictionary[a.route_list[k + 1].id + '_' + 'airport']
                    time_list.append( whole_distance )
                    for j in range( len( a.route_list ) - 1, -1, -1 ):
                        if a.route_list[j].service_type == False:
                            to_airport_distance = time_list[-1] - time_list[j]
                            # 对第k个乘客 从他上车至回到机场所需时间
                            if to_airport_distance > 2 * distance_dictionary[a.route_list[j].id + '_' + 'airport']:
                                can_insert = 0
                                time_list = 0
                                break
        else:
            can_insert=0
            time_list=0

        # check_inv_complete=0
        # if check_complete==1:
        #     while can_insert==1 and check_inv_complete==0:
        

                    # if k==0:
                    #     check_inv_complete=1


    return can_insert, time_list,distance_dictionary

def check_capacity(a, distance_dictionary):#没超过为０，超过为１
    capacity=10
    inbound=0
    outbound=0
    exceed_capacity=0
    num_whole_customer=len(a.route_list)
    if num_whole_customer<capacity:
        for i in a.route_list:
            if i.service_type==True:
                outbuound=outbound+1
            else:
                inbound=inbound+1
            test=num_whole_customer-outbound+inbound
            if test>capacity:
                exceed_capacity=1
                break

    else:
        exceed_capacity=1

    return exceed_capacity,distance_dictionary



def plot_a_simple_map( ready_route, filename ):
    airport_position = [113.814, 22.623]
    multiplier = math.cos( math.radians( airport_position[1] ) )
    x = [113.814 * multiplier]
    y = [22.623]
    # trans_offset = mtransforms.offset_copy( x = 0.05, y = 0.10, units = 'inches' )
    for j in range( 0, len( ready_route.route_list ) ):
        x.append( ready_route.route_list[j].position[0] * multiplier )
        y.append( ready_route.route_list[j].position[1] )
        if ready_route.route_list[j].service_type == True:
            label = 'r*'
        else:
            label = 'g*'

        pylab.plot( ready_route.route_list[j].position[0] * multiplier, ready_route.route_list[j].position[1], label )
        pylab.text( ready_route.route_list[j].position[0] * multiplier, ready_route.route_list[j].position[1],str(j+1))
        # plot.text( x, y, '%d, %d' % (int( x ), int( y )), transform = trans_offset )
    x.append( 113.814 * multiplier )
    y.append( 22.623 )

    # pylab.plot( x, y, label )
    pylab.plot( x, y, '--' )
    pylab.plot( 113.814 * multiplier, 22.623, 'ko' )

    pylab.title( filename )
    pylab.axis( 'off' )
    pylab.savefig(filename)
    pylab.show()
    # plt.savefig( 'fig_cat.png' )



def inner_change(route,distance_dictionary):
    opt_index = [0, 0, 0, 0]
    route_tmp = someclass.Route(None,[],[])
    new_route = route
    t_max=route.drop_time_list[-1]

    for i in range(0, len( route.route_list ) - 1 ):  # 最大len-3
        for j in range( i+1, len( route.route_list )  ):  # 最大len-step-2
            for m in range( j , len( route.route_list )  ):
                for n in range( m+1, len( route.route_list )+1):

                    # if m > j + 1:
                    #     route_tmp.route_list = route.route_list[0:i] + route.route_list[m:n + 1] + route.route_list[j + 1:m] + route.route_list[i:j + 1] + route.route_list[
                    #                                                                                 n + 1:len( route.route_list )]
                    # else:
                    #     route_tmp.route_list = route.route_list[0:i] + route.route_list[m:n + 1] + route.route_list[i:j + 1] + route.route_list[n + 1:len( route.route_list )]


                    if i>0:
                        if m>j:
                            if n<len(route.route_list):
                                route_tmp.route_list=route.route_list[0:i]+route.route_list[m:n]+route.route_list[j:m]+route.route_list[i:j]+route.route_list[n:len(route.route_list)]
                            else:
                                route_tmp.route_list=route.route_list[0:i]+route.route_list[m:n]+route.route_list[j:m]+route.route_list[i:j]
                        else:
                            if n<len(route.route_list):
                                route_tmp.route_list=route.route_list[0:i]+route.route_list[m:n]+route.route_list[i:j]+route.route_list[n:len(route.route_list)]
                            else:
                                route_tmp.route_list=route.route_list[0:i]+route.route_list[m:n]+route.route_list[i:j]
                    else:
                        if m>j:
                            if n<len(route.route_list):
                                route_tmp.route_list=route.route_list[m:n]+route.route_list[j:m]+route.route_list[i:j]+route.route_list[n:len(route.route_list)]
                            else:
                                route_tmp.route_list=route.route_list[m:n]+route.route_list[j:m]+route.route_list[i:j]
                        else:
                            if n<len(route.route_list):
                                route_tmp.route_list=route.route_list[m:n]+route.route_list[i:j]+route.route_list[n:len(route.route_list)]
                            else:
                                route_tmp.route_list=route.route_list[m:n]+route.route_list[i:j]

                    can_insert, time_list, distance_dictionary = check2distance( route_tmp, distance_dictionary )

                    if can_insert == 1:
                        t_value = time_list[-1]

                        if t_value < t_max:
                            # current_travel_cost = t_value
                            opt_index = [i, j, m, n]
                            t_max=t_value

    if opt_index[0]!=0 or opt_index[1]!=0 or opt_index[2]!=0 or opt_index[3]!=0:

        i = opt_index[0]
        j = opt_index[1]
        m = opt_index[2]
        n = opt_index[3]

        if i > 0:
            if m > j:
                if n < len( route.route_list ):
                    new_route.route_list = route.route_list[0:i] + route.route_list[m:n] + route.route_list[
                                                                                           j:m] + route.route_list[
                                                                                                  i:j] + route.route_list[
                                                                                                         n:len(
                                                                                                             route.route_list )]
                else:
                    new_route.route_list = route.route_list[0:i] + route.route_list[m:n] + route.route_list[
                                                                                           j:m] + route.route_list[i:j]
            else:
                if n < len( route.route_list ):
                    new_route.route_list = route.route_list[0:i] + route.route_list[m:n] + route.route_list[
                                                                                           i:j] + route.route_list[
                                                                                                  n:len( route.route_list )]
                else:
                    new_route.route_list = route.route_list[0:i] + route.route_list[m:n] + route.route_list[i:j]
        else:
            if m > j:
                if n < len( route.route_list ):
                    new_route.route_list = route.route_list[m:n] + route.route_list[j:m] + route.route_list[
                                                                                           i:j] + route.route_list[
                                                                                                  n:len( route.route_list )]
                else:
                    new_route.route_list = route.route_list[m:n] + route.route_list[j:m] + route.route_list[i:j]
            else:
                if n < len( route.route_list ):
                    new_route.route_list = route.route_list[m:n] + route.route_list[i:j] + route.route_list[
                                                                                           n:len( route.route_list )]
                else:
                    new_route.route_list = route.route_list[m:n] + route.route_list[i:j]

        can_insert, time_list, distance_dictionary = check2distance( new_route, distance_dictionary )
        if time_list[-1]==t_max:
            new_route.drop_time_list=time_list

    return new_route, distance_dictionary

def inter_change(route1, route2,distance_dictionary):
    opt_index = [0, 0, 0, 0]

    new_route_tmp_1 = someclass.Route(None,[],[])
    new_route_tmp_2 = someclass.Route(None,[],[])
    new_route_1 = someclass.Route(None,[],[])
    new_route_2 = someclass.Route(None,[],[])
    t_max1=route1.drop_time_list[-1]
    t_max2=route2.drop_time_list[-1]

    A_route_has_been_deleted = False

    for i in range( 0, len( route1.route_list )  ):
        # for i in random.sample(range(1, len(route1)-1),int(random_rate*(len(route1)-2))):
        for j in range( i, len( route1.route_list )+1 ):
            # for j in random.sample(range(i-1, len(route1)-1),int(random_rate*(len(route1)-i-1))):
            for m in range( 0, len( route2.route_list )  ):
                # for m in random.sample(range(1, len(route2)-1),int(random_rate*(len(route2)-2))):
                for n in range( m , len( route2.route_list ) + 1 ):
                    # for n in random.sample(range(m-1, len(route2)-1),int(random_rate*(len(route2)-m-1))):
                    if i>0:
                        if j<len(route1.route_list):
                            if m>0:
                                if n<len(route2.route_list):
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[j :len(route1.route_list )]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[n :len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] +route1.route_list[j :len(route1.route_list )]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                            else:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route1.route_list[i:j] + route2.route_list[n:len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route1.route_list[i:j]
                        else:
                            if m > 0:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[n:len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                            else:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route1.route_list[i:j]
                    else:
                        if j < len( route1.route_list ):
                            if m > 0:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[n:len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                            else:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route1.route_list[i:j] + route2.route_list[n:len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route2.route_list[m:n] + route1.route_list[j:len(route1.route_list )]
                                    new_route_tmp_2.route_list = route1.route_list[i:j]
                        else:
                            if m > 0:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[n:len(route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                            else:
                                if n < len( route2.route_list ):
                                    new_route_tmp_1.route_list = route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                                else:
                                    new_route_tmp_1.route_list = route2.route_list[m:n]
                                    new_route_tmp_2.route_list = route1.route_list[i:j]

                    # if len(new_route_tmp_1.route_list)!=0:
                    #     can_insert1, time_list1, distance_dictionary = check2distance( new_route_tmp_1, distance_dictionary )
                    #     if can_insert1==1:
                    #         t_value_1 = time_list1[-1]
                    # if len(new_route_tmp_2.route_list)!=0:
                    #     can_insert2, time_list2, distance_dictionary = check2distance( new_route_tmp_2, distance_dictionary )
                    #     if can_insert2==1:
                    #         t_value_2 = time_list2[-1]
                    # judge_tmp_1 = judge_feasibility( new_route_tmp_1, customer, distance_matrix, distance_airport,
                    #                                  time_matrix, time_airport, number_out )
                    # judge_tmp_2 = judge_feasibility( new_route_tmp_2, customer, distance_matrix, distance_airport,
                    #                                  time_matrix, time_airport, number_out )

                    # if (can_insert1==1) and (can_insert2==1):




                    # 车数是第一目标，如果一个route被删了，则不管行驶时间，一定认为最优
                    if A_route_has_been_deleted == True:
                        if (len( new_route_tmp_1.route_list ) == 0) or (len( new_route_tmp_2.route_list ) == 0):
                            # opt_index = [i, j, m, n]
                            if len( new_route_tmp_1.route_list ) == 0:
                                t_value_1=0
                                can_insert2, time_list2, distance_dictionary = check2distance( new_route_tmp_2, distance_dictionary )
                                if can_insert2==1:
                                    t_value_2=time_list2[-1]
                                    if (t_value_1 + t_value_2) < (t_max1 + t_max2):
                                        # travel_cost_1 = t_value_1
                                        # travel_cost_2 = t_value_2
                                        opt_index = [i, j, m, n]
                                        t_max1 = t_value_1
                                        t_max2 = t_value_2
                            else:
                                can_insert1,time_list1, distance_dictionary= check2distance(new_route_tmp_1, distance_dictionary)
                                if can_insert1==1:
                                    t_value_1=time_list1[-1]
                                    if len(new_route_tmp_2.route_list)==0:
                                        t_value_2=0
                                        if (t_value_1 + t_value_2) < (t_max1 + t_max2):
                                            # travel_cost_1 = t_value_1
                                            # travel_cost_2 = t_value_2
                                            opt_index = [i, j, m, n]
                                            t_max1 = t_value_1
                                            t_max2 = t_value_2
                    else:
                        if (len( new_route_tmp_1.route_list ) == 0) or (len( new_route_tmp_2.route_list ) == 0):
                            if len( new_route_tmp_1.route_list ) == 0:
                                t_value_1=0
                                can_insert2, time_list2, distance_dictionary = check2distance( new_route_tmp_2, distance_dictionary )
                                if can_insert2==1:
                                    A_route_has_been_deleted = True
                                    t_value_2=time_list2[-1]
                                    opt_index = [i, j, m, n]
                                    t_max1 = t_value_1
                                    t_max2 = t_value_2
                            else:
                                can_insert1,time_list1, distance_dictionary= check2distance(new_route_tmp_1, distance_dictionary)
                                if can_insert1==1:
                                    t_value_1=time_list1[-1]
                                    if len(new_route_tmp_2.route_list)==0:
                                        t_value_2=0
                                        A_route_has_been_deleted = True
                                        opt_index = [i, j, m, n]
                                        t_max1 = t_value_1
                                        t_max2 = t_value_2
                        else:
                            can_insert1, time_list1, distance_dictionary = check2distance( new_route_tmp_1,distance_dictionary )
                            can_insert2, time_list2, distance_dictionary = check2distance( new_route_tmp_2, distance_dictionary )
                            if can_insert1==1 and can_insert2==1:
                                t_value_1=time_list1[-1]
                                t_value_2=time_list2[-1]
                                if t_value_1+t_value_2<t_max1+t_max2:
                                    t_max1=t_value_1
                                    t_max2=t_value_2
                                    A_route_has_been_deleted =True
                                    opt_index=[i,j,m,n]



    if opt_index[0] != 0 or opt_index[1]!=0 or opt_index[2]!=0 or opt_index[3]!=0:
        i = opt_index[0]
        j = opt_index[1]
        m = opt_index[2]
        n = opt_index[3]

        if i > 0:
            if j < len( route1.route_list ):
                if m > 0:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[
                                                                                                       j:len(
                                                                                                           route1.route_list )]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[
                                                                                                       n:len(
                                                                                                           route2.route_list )]
                    else:
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[
                                                                                                       j:len(
                                                                                                           route1.route_list )]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                else:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[
                                                                                                       j:len(
                                                                                                           route1.route_list )]
                        new_route_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                    else:
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n] + route1.route_list[
                                                                                                       j:len(
                                                                                                           route1.route_list )]
                        new_route_2.route_list = route1.route_list[i:j]
            else:
                if m > 0:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[
                                                                                                       n:len(
                                                                                                           route2.route_list )]
                    else:
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                else:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                        new_route_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                    else:
                        new_route_1.route_list = route1.route_list[0:i] + route2.route_list[m:n]
                        new_route_2.route_list = route1.route_list[i:j]
        else:
            if j < len( route1.route_list ):
                if m > 0:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route2.route_list[m:n] + route1.route_list[j:len( route1.route_list )]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[
                                                                                                       n:len(
                                                                                                           route2.route_list )]
                    else:
                        new_route_1.route_list = route2.route_list[m:n] + route1.route_list[j:len( route1.route_list )]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                else:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route2.route_list[m:n] + route1.route_list[j:len( route1.route_list )]
                        new_route_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                    else:
                        new_route_1.route_list = route2.route_list[m:n] + route1.route_list[j:len( route1.route_list )]
                        new_route_2.route_list = route1.route_list[i:j]
            else:
                if m > 0:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route2.route_list[m:n]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j] + route2.route_list[
                                                                                                       n:len(
                                                                                                           route2.route_list )]
                    else:
                        new_route_1.route_list = route2.route_list[m:n]
                        new_route_2.route_list = route2.route_list[0:m] + route1.route_list[i:j]
                else:
                    if n < len( route2.route_list ):
                        new_route_1.route_list = route2.route_list[m:n]
                        new_route_2.route_list = route1.route_list[i:j] + route2.route_list[n:len( route2.route_list )]
                    else:
                        new_route_1.route_list = route2.route_list[m:n]
                        new_route_2.route_list = route1.route_list[i:j]


        if len(new_route_1.route_list)!=0:
            can_insert1, time_list1, distance_dictionary = check2distance( new_route_1, distance_dictionary )
            new_route_1.drop_time_list = time_list1
        else:
            new_route_1.drop_time_list=[]
        if len(new_route_2.route_list)!=0:
            can_insert2, time_list2, distance_dictionary = check2distance( new_route_2, distance_dictionary )
            new_route_2.drop_time_list = time_list2
        else:
            new_route_2.drop_time_list=[]


    else:
        new_route_1=route1
        new_route_2=route2


    return new_route_1, new_route_2, distance_dictionary



def calculate_cutomer_out( customer_out_calculating, whole_route, distance_dictionary):
    airport=someclass.Demand('airport',np.array([113.814, 22.623]),None,None)
    for i in range(0, len(customer_out_calculating)):  # 表示现有需要计算的订单
        flag2=0
        distance_test = float( "inf" )
        available_positions=[]
        if (len( whole_route ) == 0) or whole_route[0]==None:
            # key = 'airport' + '_' + customer_out_calculating[i].id
            route_list_tmp = []
            route_list_tmp.append( customer_out_calculating[0] )
            time_list = []
            if 'airport' + '_' + customer_out_calculating[0].id not in distance_dictionary.keys():
                distance_dictionary = customer_out_calculating[0].update_distance_dictionary(airport,distance_dictionary)

            # distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
            expected_drop_time0 = distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
            time_list.append( expected_drop_time0 )
            expected_drop_time0=expected_drop_time0+distance_dictionary[customer_out_calculating[0].id+'_'+'airport']
            time_list.append(expected_drop_time0)

            route_tmp = someclass.Route( None, route_list_tmp, time_list )
            route_tmp0 = []
            route_tmp0.append( route_tmp )
            whole_route[0] = route_tmp0
            # customer_out_calculated_route_id = customer_out_calculated_route_id + 1
            # customer_out_calculated.append( customer_out_calculated_route_id, route )
        else:
            for a in whole_route[0]:  # 不同的线路
                if len(a.route_list)<10:
                    for j in range( 0, len( a.route_list ) + 1 ):
                        if j == 0:
                            if 'airport' + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                                distance_dictionary = customer_out_calculating[i].update_distance_dictionary( airport,
                                                                                          distance_dictionary )
                            if customer_out_calculating[i].id + '_' + a.route_list[0].id not in distance_dictionary.keys():
                                distance_dictionary=customer_out_calculating[i].update_distance_dictionary(a.route_list[0],distance_dictionary)
                            if 'airport' + '_' + a.route_list[0].id not in distance_dictionary.keys():
                                distance_dictionary = airport.update_distance_dictionary(a.route_list[0],distance_dictionary)

                            distance_increase = distance_dictionary['airport' + '_' + customer_out_calculating[i].id] + \
                                                distance_dictionary[customer_out_calculating[i].id + '_' + a.route_list[0].id] - \
                                                distance_dictionary['airport' + '_' + a.route_list[0].id]
                        if j == len( a.route_list ):
                            if a.route_list[-1].id + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                                distance_dictionary = a.route_list[-1].update_distance_dictionary(
                                    customer_out_calculating[i], distance_dictionary )
                            if customer_out_calculating[i].id + '_' + 'airport' not in distance_dictionary.keys():
                                distance_dictionary = customer_out_calculating[i].update_distance_dictionary( airport,
                                                                                                              distance_dictionary )
                            if a.route_list[-1].id + '_' + 'airport' not in distance_dictionary.keys():
                                distance_dictionary = a.route_list[-1].update_distance_dictionary( airport,
                                                                                                   distance_dictionary )
                            distance_increase = distance_dictionary[
                                                    a.route_list[-1].id + '_' + customer_out_calculating[i].id] + \
                                                distance_dictionary[
                                                    customer_out_calculating[i].id + '_' + 'airport'] - distance_dictionary[
                                                    a.route_list[-1].id + '_' + 'airport']
                        if (j != 0) and (j != len( a.route_list )):
                            if a.route_list[j - 1].id + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                                distance_dictionary= a.route_list[j-1].update_distance_dictionary(customer_out_calculating[i],distance_dictionary)
                            if customer_out_calculating[i].id + '_' + a.route_list[j].id not in distance_dictionary.keys():
                                distance_dictionary=customer_out_calculating[i].update_distance_dictionary(a.route_list[j],distance_dictionary)
                            if a.route_list[j - 1].id + '_' + a.route_list[j].id not in distance_dictionary.keys():
                                distance_dictionary=a.route_list[j-1].update_distance_dictionary(a.route_list[j],distance_dictionary)

                                distance_increase = distance_dictionary[
                                                    a.route_list[j - 1].id + '_' + customer_out_calculating[
                                                        i].id] + distance_dictionary[
                                                    customer_out_calculating[i].id + '_' + a.route_list[j].id] - \
                                                distance_dictionary[
                                                    a.route_list[j - 1].id + '_' + a.route_list[j].id]



                        if distance_increase < distance_test:
                            distance_test = distance_increase
                            insert_position = j
                            # insert_route = a
                            # insert_route_index = whole_route[0].index( insert_route )
                            insert_route_index = whole_route[0].index( a )
                            position_tmp=someclass.Position(distance_test,insert_position,insert_route_index)
                            available_positions.append(position_tmp)
                else:
                    flag2=flag2+1
            if flag2==len(whole_route[0]):#所有的线路都超过10个人
                route_list_tmp = []
                route_list_tmp.append(customer_out_calculating[i])
                time_list = []
                if 'airport' + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                    distance_dictionary = customer_out_calculating[i].update_distance_dictionary(airport,
                                                                                                 distance_dictionary)

                # distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
                expected_drop_time0 = distance_dictionary['airport' + '_' + customer_out_calculating[i].id]
                time_list.append(expected_drop_time0)
                expected_drop_time0 = expected_drop_time0 + distance_dictionary[
                    customer_out_calculating[i].id + '_' + 'airport']
                time_list.append(expected_drop_time0)

                route_tmp = someclass.Route(None, route_list_tmp, time_list)
                # route_tmp0 = []
                # route_tmp0.append(route_tmp)
                whole_route[0].append(route_tmp)
            else:
                # insert_route.route_list.insert(insert_position, customer_out_calculating[i])
                flag3=1
                for p in range(len(available_positions)-1,-1,-1):
                    insert_route_index=available_positions[p].insert_route_index
                    insert_position=available_positions[p].insert_position
                    whole_route[0][insert_route_index].route_list.insert(insert_position, customer_out_calculating[i])
                    # customer_out_calculated[a].insert( j, customer_out_calculating[i] )
                    # can_insert, time_list, distance_dictionary= check2distance(insert_route, distance_dictionary)
                    can_insert, time_list, distance_dictionary= check2distance(whole_route[0][insert_route_index], distance_dictionary)

                    if can_insert==1:
                        whole_route[0][insert_route_index].drop_time_list = time_list
                        flag3=0
                        break
                if p==0 and flag3!=0:#所有的位置都不行
                    # 重新分配一辆车
                    # a.route_list.pop(insert_position)
                    # customer_out_cannot_service.append(customer_out_calculating[i])
                    whole_route[0][insert_route_index].route_list.remove(customer_out_calculating[i])

                    route_list_tmp = []
                    route_list_tmp.append(customer_out_calculating[i])
                    time_list = []
                    if 'airport' + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                        distance_dictionary = airport.update_distance_dictionary(customer_out_calculating[i],
                                                                                 distance_dictionary)

                    expected_drop_time0 = distance_dictionary['airport' + '_' + customer_out_calculating[i].id]
                    time_list.append(expected_drop_time0)
                    expected_drop_time0 = expected_drop_time0 + distance_dictionary[
                        customer_out_calculating[i].id + '_' + 'airport']
                    time_list.append(expected_drop_time0)

                    route_tmp = someclass.Route(None, route_list_tmp, time_list)
                    # customer_out_calculated_route_id = customer_out_calculated_route_id + 1
                    whole_route[0].append(route_tmp)

                    # if can_insert == 0:

                    # else:
                        # a.route_drop_time_list=time_list
                        # whole_route[0][insert_route_index].route_list.insert(insert_position, customer_out_calculating[i])
    whole_route[1] = whole_route[0]
    whole_route[0] = None

    return whole_route, customer_out_cannot_service,distance_dictionary


def calculate_cutomer_in(customer_in_calculating, whole_route, distance_dictionary,timestamp_1):
    airport=someclass.Demand('airport',np.array([113.814, 22.623]),None,None)
    customer_in_completed=[]

    for i in range( 0, len( customer_in_calculating ) ):  # 表示现有需要计算的订单
        if i==10:
            pass
        distance_test = float( "inf" )
        available_positions=[]
        for a in whole_route[1]:
            if customer_in_calculating[i].on_time < timestamp_1+a.drop_time_list[-1]:
                if customer_in_calculating[i].on_time < timestamp_1+a.drop_time_list[0]:

                    if 'airport' + '_' + customer_in_calculating[i].id not in distance_dictionary.keys():
                        distance_dictionary=airport.update_distance_dictionary(customer_in_calculating[i],distance_dictionary)
                    if customer_in_calculating[i].id + '_' + a.route_list[0].id not in distance_dictionary.keys():
                        distance_dictionary=customer_in_calculating[i].update_distance_dictionary(a.route_list[0],distance_dictionary)
                    if 'airport' + '_' + a.route_list[0].id not in distance_dictionary.keys():
                        airport.update_distance_dictionary(a.route_list[0],distance_dictionary)
                    distance_increase = distance_dictionary['airport' + '_' + customer_in_calculating[i].id] + \
                                        distance_dictionary[customer_in_calculating[i].id + '_' + a.route_list[0].id] - \
                                        distance_dictionary['airport' + '_' + a.route_list[0].id]
                    p = 0
                    if distance_increase < distance_test:
                        distance_test = distance_increase
                        # insert_route = a
                        insert_position = p
                        # insert_route_index = whole_route[1].index( insert_route )
                        insert_route_index = whole_route[1].index( a )
                        position_tmp=someclass.Position(distance_test, insert_position, insert_route_index)
                        available_positions.append(position_tmp)
                else:
                    for j in range( 0, len( a.drop_time_list ) - 1 ):
                        if (customer_in_calculating[i].on_time > timestamp_1+a.drop_time_list[j]) and \
                                (customer_in_calculating[i].on_time < timestamp_1+a.drop_time_list[j + 1]):
                            if j == len( a.drop_time_list ) - 2:
                                if a.route_list[-1].id + '_' + customer_in_calculating[i].id not in distance_dictionary.keys():
                                    distance_dictionary = a.route_list[-1].update_distance_dictionary(customer_in_calculating[i],distance_dictionary)
                                if customer_in_calculating[i].id + '_' + 'airport' not in distance_dictionary.keys():
                                    distance_dictionary = customer_in_calculating[i].update_distance_dictionary(airport,distance_dictionary)
                                if a.route_list[-1].id + '_' + 'airport' not in distance_dictionary.keys():
                                    distance_dictionary = a.route_list[-1].update_distance_dictionary(airport,distance_dictionary)

                                distance_increase = distance_dictionary[
                                                        a.route_list[-1].id + '_' + customer_in_calculating[i].id] + \
                                                    distance_dictionary[customer_in_calculating[i].id + '_' + 'airport'] - \
                                                    distance_dictionary[a.route_list[-1].id + '_' + 'airport']
                            else:
                                if a.route_list[j].id + '_' + customer_in_calculating[i].id not in distance_dictionary.keys():
                                    distance_dictionary=a.route_list[j].update_distance_dictionary(customer_in_calculating[i],distance_dictionary)
                                if customer_in_calculating[i].id + '_' + a.route_list[j + 1].id not in distance_dictionary.keys():
                                    distance_dictionary = customer_in_calculating[i].update_distance_dictionary(a.route_list[j+1],distance_dictionary)
                                if a.route_list[j].id + '_' + a.route_list[j + 1].id not in distance_dictionary.keys():
                                    distance_dictionary = a.route_list[j].update_distance_dictionary(a.route_list[j+1],distance_dictionary)

                                distance_increase = distance_dictionary[
                                                        a.route_list[j].id + '_' + customer_in_calculating[i].id] + \
                                                    distance_dictionary[
                                                        customer_in_calculating[i].id + '_' + a.route_list[j + 1].id] - \
                                                    distance_dictionary[
                                                        a.route_list[j].id + '_' + a.route_list[j + 1].id]

                            p = j + 1
                            if distance_increase < distance_test:
                                distance_test = distance_increase
                                # insert_route = a
                                insert_position = p
                                # insert_route_index = whole_route[1].index( insert_route )
                                insert_route_index = whole_route[1].index(a)
                                position_tmp = someclass.Position(distance_test, insert_position, insert_route_index)
                                available_positions.append(position_tmp)

        # insert_route.route_list.insert( insert_position, customer_in_calculating[i] )
        # can_insert, time_list, distance_dictionary = check2distance(  insert_route, distance_dictionary )

        flag3=1
        for p in range(len(available_positions) - 1, -1, -1):
            insert_route_index = available_positions[p].insert_route_index
            insert_position = available_positions[p].insert_position
            whole_route[1][insert_route_index].route_list.insert(insert_position, customer_in_calculating[i])
            # customer_out_calculated[a].insert( j, customer_out_calculating[i] )
            # can_insert, time_list, distance_dictionary= check2distance(insert_route, distance_dictionary)
            can_insert, time_list, distance_dictionary = check2distance(whole_route[1][insert_route_index],
                                                                        distance_dictionary)
            exceed_capacity,distance_dictionary=check_capacity(whole_route[1][insert_route_index], distance_dictionary)

            if can_insert == 1 and exceed_capacity==0:
                whole_route[1][insert_route_index].drop_time_list = time_list
                customer_in_completed.append(customer_in_calculating[i])
                flag3=0
                break
        if p == 0 and flag3!=0:  # 所有的位置都不行
            # 重新分配一辆车
            # a.route_list.pop(insert_position)
            # customer_out_cannot_service.append(customer_out_calculating[i])
            whole_route[1][insert_route_index].route_list.remove(customer_in_calculating[i])
            route_list_tmp = []
            route_list_tmp.append(customer_in_calculating[i])
            time_list = []
            if 'airport' + '_' + customer_in_calculating[i].id not in distance_dictionary.keys():
                distance_dictionary = airport.update_distance_dictionary(customer_in_calculating[i],
                                                                         distance_dictionary)

            expected_drop_time0 = distance_dictionary['airport' + '_' + customer_in_calculating[i].id]
            time_list.append(expected_drop_time0)
            expected_drop_time0 = expected_drop_time0 + distance_dictionary[
                customer_in_calculating[i].id + '_' + 'airport']
            time_list.append(expected_drop_time0)

            route_tmp = someclass.Route(None, route_list_tmp, time_list)
            # customer_out_calculated_route_id = customer_out_calculated_route_id + 1
            whole_route[1].append(route_tmp)
    if 2 not in whole_route.keys():
        whole_route[2]=[whole_route[1]]
    else:
        whole_route[2].append(whole_route[1])
    # whole_route[1]
    whole_route[1] = None

    # return whole_route, customer_in_cannot_service,distance_dictionary
    return whole_route, customer_in_completed,distance_dictionary



distance_dictionary = dict()

"""
========================== 读取所有出入机场数据 ======================================
"""
start = time.clock()
customer = []

f = open( 'both mode_1123.txt', 'w' )
f.write( "2015-08-03" + '\n' )



filename_out = '20150803_gaode_offboard.txt'  # 出机场的数据
filename_in = '20150803_gaode_onboard.txt'  # 入机场的数据

# customer_out, distance_dictionary = read_file_py.read_file( filename_out, True, distance_dictionary )
# customer_in, distance_dictionary = read_file_py.read_file( filename_in, False, distance_dictionary )

customer_out = read_file_py.read_file1( filename_out, True, distance_dictionary )
customer_in= read_file_py.read_file1( filename_in, False, distance_dictionary )
customer = customer_out + customer_in

# g=open('distance_dictionary.txt','w')
# for key in distance_dictionary.keys():
#     g.write(str(key)+', ' + str(distance_dictionary[key]) + '\n')
# g.close()

#read from distance_dictionary
# filename= 'distance_dictionary_euclidean.txt'
# distance_dictionary=dict()
# with open( filename, 'r' ) as file_to_read:
#     # j = 1  # 用于添加用户ID
#     while True:
#         lines = file_to_read.readline()  # 整行读取数据
#         if not lines:
#             break
#             pass
#
#         # 将整行数据分割处理，如果分割符是空格，括号里就不用传入参数，如果是逗号， 则传入‘，'字符。
#         key, value = [ i for i in lines.split( ', ' )]
#         distance_dictionary[key]=float(value[:-1])



f.write( "出机场总点数：" + str( len( customer_out ) ) + '\n' )
f.write( "入机场总点数：" + str( len( customer_in ) ) + '\n' )

end = time.clock()
f.write( "读取数据耗时：" + str( end - start ) + '\n' + '\n' )

"""
========================== 读取数据结束，开始大循环 ======================================
"""
"""
"2015-08-03 00:00:00" 对应时间戳 1438531200.0 
"2015-08-04 00:00:00" 对应时间戳 1438617600.0 

数据更新间隔5分钟，300秒

假设出机场的提前半小时下订单
假设入机场的提前2小时下单

假定入机场的上车点平均单程为1小时
晚10点半以后(10点以后预约)的出机场数据不要

距出发时间还有5分钟时，车辆固定，准备出发

"""

#    customer_out_calculated=dict()#有顺序的各种不同线路
customer_out_calculated_route_id = 0
customer_out_cannot_service = []
customer_in_cannot_service = []
route = []
customer_in_cannot_service = []
customer_out_calculated_route_id = 0
whole_route=dict()
flag=-1
for timestamp_1 in range( 1438531200, 1438617600, 900 ):
    flag=flag+1
    customer_out_calculating = []  # 无顺序
    customer_in_calculating = []
    if timestamp_1==1438597800:
        pass
    # 每隔15min算一次

    start = time.clock()
    """时间戳表示实际时间，现实时间"""
    timestamp_2 = timestamp_1 + 900
    timestr_1 = time.strftime( "%H:%M:%S", time.localtime( timestamp_1 ) )
    timestr_2 = time.strftime( "%H:%M:%S", time.localtime( timestamp_2 ) )
    f.write( "当前时间：" + timestr_1 + "--" + timestr_2 + '\n' )
    print("当前时间：" + timestr_1 + "--" + timestr_2)

    # whole_route = dict()
    for r in customer_out:
        if timestamp_1 < r.on_time < timestamp_2:
            customer_out_calculating.append( r )
    f.write( "此时段的出机场订单有：" + str( len( customer_out_calculating ) ) + '个\n' )

    whole_route, customer_out_cannot_service, distance_dictionary= calculate_cutomer_out( customer_out_calculating, whole_route,
                                                                      distance_dictionary)
    # inner_exchange
    for k in range(len(whole_route[1])):
        # plot_a_simple_map( whole_route[1][k], 'test_before'+str(k) )
        new_route, distance_dictionary=inner_change( whole_route[1][k], distance_dictionary )
        # plot_a_simple_map( new_route, 'test_after'+str(k) )
        whole_route[1][k]=new_route


    #     inter_exchange
    for k in range(len(whole_route[1])-1):
        for l in range(k+1,len(whole_route[1])):
            # plot_a_simple_map( whole_route[1][k], 'test_before' + str( k ) )
            # plot_a_simple_map( whole_route[1][l], 'test_before' + str( l ) )
            if len(whole_route[1][k].route_list)!=0 and len(whole_route[1][l].route_list)!=0:
                new_route1, new_route2,distance_dictionary= inter_change(whole_route[1][k], whole_route[1][l],distance_dictionary)
                whole_route[1][k]=new_route1
                whole_route[1][l]=new_route2

    for k in range(len(whole_route[1])-1,-1,-1):
        if len(whole_route[1][k].route_list)==0:
            whole_route[1].remove(whole_route[1][k])

    # for k in range(len(whole_route[1])):
    #     whole_route[1][k].route_id=customer_out_calculated_route_id
    #     customer_out_calculated_route_id=customer_out_calculated_route_id+1


            # else:
            #     if len( whole_route[1][k].route_list ) == 0:
            #         whole_route[1].remove( whole_route[1][k] )
            #     if len( whole_route[1][l].route_list ) == 0:
            #         whole_route[1].remove( whole_route[1][l] )
            # plot_a_simple_map( new_route1, 'test_after' + str( k ) )
            # plot_a_simple_map( new_route2, 'test_after' + str( l ) )

            # if len(new_route1.route_list)!=0:
            #     whole_route[1][k]=new_route2
            # if len( new_route2.route_list ) != 0:
            #     whole_route[1][l] = new_route2

            # if len(new_route1.route_list)==0:
            #     whole_route[1].remove(whole_route[1][k])
            # if len(new_route2.route_list)==0:
            #     whole_route[1].remove(whole_route[1][l])






    if len(customer_out_cannot_service)!=0:
        f.write( "在此时间间隔内不能服务的出机场乘客是：" )
        for i in range( len( customer_out_cannot_service ) ):
            f.write( customer_out_cannot_service[i].id + ', ' )

    if len(customer_out_cannot_service)!=0:
        print("在此时间间隔内不能服务的出机场乘客是：")
        for i in range( len( customer_out_cannot_service ) ):
            print(customer_out_cannot_service[i].id + ', ')

    # this is not fully true! #we should select customer_in based on each route in whole_route[1]. Selecting customer from all customer_in
    # without aiming at specific route will introduce much inefficient action.
    latest_return_time = 0
    for a in whole_route[1]:
        if a.drop_time_list[-1] > latest_return_time:
            latest_return_time = a.drop_time_list[-1]

    for r in customer_in:
        if timestamp_1 < r.on_time < latest_return_time+timestamp_1:
            customer_in_calculating.append( r )
    # for r in customer_in_cannot_service:
    #     if timestamp_1 < r.on_time < latest_return_time+timestamp_1:
    #         customer_in_calculating.append( r )

    f.write( "此时段的入机场订单可能有：" + str( len( customer_in_calculating ) ) + '个\n' )

    # whole_route, customer_in_completed, distance_dictionary, customer_out_calculated_route_id= calculate_cutomer_in( customer_in_calculating, whole_route,
    #                                                                 distance_dictionary,timestamp_1,customer_out_calculated_route_id )
    whole_route, customer_in_completed, distance_dictionary = calculate_cutomer_in(customer_in_calculating, whole_route,
        distance_dictionary, timestamp_1)


    # inner_exchange
    for k in range(len(whole_route[2][flag])):
        # plot_a_simple_map( whole_route[1][k], 'test_before'+str(k) )
        new_route, distance_dictionary=inner_change( whole_route[2][flag][k], distance_dictionary )
        # plot_a_simple_map( new_route, 'test_after'+str(k) )
        whole_route[2][flag][k]=new_route


    #     inter_exchange
    for k in range(len(whole_route[2][flag])-1):
        for l in range(k+1,len(whole_route[2][flag])):
            # plot_a_simple_map( whole_route[1][k], 'test_before' + str( k ) )
            # plot_a_simple_map( whole_route[1][l], 'test_before' + str( l ) )
            if len(whole_route[2][flag][k].route_list)!=0 and len(whole_route[2][flag][l].route_list)!=0:
                new_route1, new_route2,distance_dictionary= inter_change(whole_route[2][flag][k], whole_route[2][flag][l],distance_dictionary)
                whole_route[2][flag][k]=new_route1
                whole_route[2][flag][l]=new_route2

    for k in range(len(whole_route[2][flag])-1,-1,-1):
        if len(whole_route[2][flag][k].route_list)==0:
            whole_route[2][flag].remove(whole_route[2][flag][k])

    for k in range(len(whole_route[2][flag])):
        whole_route[2][flag][k].route_id=customer_out_calculated_route_id
        customer_out_calculated_route_id=customer_out_calculated_route_id+1


    print("在此时间段完成的入机场订单有："+str(len(customer_in_completed))+'个\n他们是：')
    for i in customer_in_completed:
        print(i.id+', ')


    print("在此时间段完成的出入机场订单线路有：\n")
    for i in whole_route[2][flag]:
        print(str(i.route_id)+': ')
        for j in i.route_list:
           print(str(j.id)+', ')

    customer_in = [v for v in customer_in if v not in customer_in_completed]
    # customer_in=customer_in-customer_in_completed
    for ready_route in whole_route[2][flag]:
        image_name = timestr_1 + "--" + timestr_2 + " final: "+str(ready_route.route_id)
        plot_a_simple_map( ready_route, image_name )

print("在整个模拟中，一直达不到进机场条件的订单有：")
for i in range( len( customer_in ) ):
    print(customer_in[i].id + ", ")

f.write( "在整个模拟中，一直达不到进机场条件的订单有：" )
for i in range( len( customer_in) ):
    f.write( customer_in[i].id + ", " )
