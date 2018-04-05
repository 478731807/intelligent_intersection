#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
#
#   This module provides functions for turns
#
#######################################################################

import copy
import math
import shapely.geometry as geom
import osmnx as ox
from lane import add_space_for_crosswalk
from border import cut_border_by_polygon, get_turn_angle, to_rad, shift_list_of_nodes, extend_vector, get_compass, shift_by_bearing_and_distance


def shorten_border_for_crosswalk(input_border,
                                 street_name,
                                 lanes, crosswalk_width=1.82,
                                 destination='from_intersection'):
    """
    Remove the portion of the input border overlapping with any crosswalk crossing the input border.
    Scan all lanes with street names other than the street the input border belongs to,
    and identify crosswalks related to each lane.
    :param input_border: list of coordinates
    :param street_name: string
    :param lanes: list of dictionaries
    :param crosswalk_width: float
    :param destination: string
    :return: list of coordinates
    """
    border = copy.deepcopy(input_border)
    if destination == 'from_intersection':
        multi_string_index = -1
    else:
        multi_string_index = 0

    for l in lanes:
        if l['name'] == 'no_name' or l['name'] == street_name:
            continue

        #if l['lane_id'] == '1' or l['lane_id'] == '1R' or 'B' in l['lane_id']:
        lb, rb = add_space_for_crosswalk(l, crosswalk_width=crosswalk_width)
        coord = lb + rb[::-1]
        polygon = geom.Polygon(coord)
        temp = cut_border_by_polygon(border, polygon, multi_string_index)
        if temp is not None:
            border = temp

    return border


def construct_turn_arc(origin_border, destination_border, number_of_points=12, turn_direction=-1.0):
    """
    Construct a turn arc
    :param origin_border: list of coordinates
    :param destination_border: list of coordinates
    :param number_of_points: integer
    :param turn_direction: -1 if left turn otherwise 1
    :return: list of coordinates
    """
    intersection_point, vector1, vector2 = get_turn_angle(origin_border, destination_border)

    if intersection_point is None:
        return None

    from_origin_to_intersection = ox.great_circle_vec(intersection_point[1], intersection_point[0],
                                                      vector1[1][1], vector1[1][0])
    from_destination_to_intersection = ox.great_circle_vec(intersection_point[1], intersection_point[0],
                                                           vector2[1][1], vector2[1][0])

    bearing1 = get_compass(vector1[1], vector1[0])
    bearing2 = get_compass(vector2[0], vector2[1])
    angle = ((turn_direction*(bearing2 - bearing1) + 360) % 360)

    if from_origin_to_intersection < from_destination_to_intersection:
        distance_to_starting_point = from_origin_to_intersection
        dist_delta = 0.0
    else:
        distance_to_starting_point = from_destination_to_intersection
        dist_delta = from_origin_to_intersection - from_destination_to_intersection

    radius = distance_to_starting_point / math.tan(to_rad(angle / 2.0))
    shift = [turn_direction * 2.0 * radius * (math.sin(to_rad(angle / 2.0 * i / float(number_of_points)))) ** 2
             for i in range(0, number_of_points + 1)
             ]

    vec = [origin_border[-1], intersection_point]
    vector = [
        extend_vector(vec, length=dist_delta + radius * (math.sin(to_rad(angle * i / float(number_of_points)))), backward=False)[
            1]
        for i in range(0, number_of_points + 1)
        ]

    temp = shift_list_of_nodes(vector, shift, direction_reference=vec)

    for i in range(0, number_of_points + 1):
        res = shift_by_bearing_and_distance(vector[i], shift[i], vec, bearing_delta=turn_direction*90.0)
        temp[i] = res

    return temp # shift_list_of_nodes(vector, shift, direction_reference=vec)
