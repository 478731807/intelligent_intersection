#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
#
#   This module creates meta data
#
#######################################################################


import datetime
from right_turn import get_connected_links
from bicycle import key_value_check, get_bicycle_lane_location, is_shared
from lane import set_ids, get_link_from_and_to, is_opposite_lane_exist
from public_transit import get_public_transit_stop
from border import get_border_length
from path_way import get_num_of_lanes
from border import get_angle_between_bearings, get_border_curvature, great_circle_vec_check_for_nan
from log import get_logger
from guideway import get_crosswalk_to_crosswalk_distance_along_guideway, get_through_guideways

logger = get_logger()
meta_keys = ['diameter',
             'stop_sign',
             'number_of_railway_exits',
             'min_number_of_lanes_in_approach',
             'number_of_center_bicycle_approaches',
             'number_of_right_side_bicycle_exits',
             'max_number_of_lanes_in_approach',
             'signal_present',
             'number_of_approaches',
             'max_curvature',
             'min_curvature',
             'subway_station_present',
             'number_of_right_side_bicycle_approaches',
             'number_of_tram/train_stops',
             'max_number_of_lanes_in_exit',
             'timestamp',
             'number_of_exits',
             'distance_to_next_intersection',
             'max_angle',
             'number_of_railway_approaches',
             'number_of_bus/trolley_stops',
             'pedestrian_signal_present',
             'shortest_distance_to_railway_crossing',
             'min_number_of_lanes_in_exit',
             'number_of_center_bicycle_exits',
             'approach_street_types',
             'exit_street_types',
             'approach_max_speed_limit',
             'approach_min_speed_limit',
             'exit_max_speed_limit',
             'exit_min_speed_limit',
             'approach_counts',
             'exit_counts'
             ]


def set_meta_data(lanes, intersection_data, max_distance=20.0):
    """
    Set meta data for all lanes related to the intersection
    :param lanes: list of dictionaries
    :param max_distance: max distance in meters for a transit stop to belong to a lane
    :param intersection_data: intersection data dictionary
    :return: 
    """

    set_ids(lanes)
    for lane_data in lanes:
        try:
            lane_data['meta_data'] = get_lane_meta_data(lane_data, lanes, intersection_data, max_distance=max_distance)
        except Exception as e:
            lane_data['meta_data'] = 'Exception in the log'
            logger.exception('Lane meta data exception: %r' % e)
            continue

    try:
        intersection_data['meta_data'] = get_intersection_meta_data(intersection_data)
    except Exception as e:
        meta_data = {'exception': 'Exception: %r' % e}
        intersection_data['meta_data'] = meta_data
        for k in meta_keys:
            meta_data[k] = None
        meta_data['timestamp'] = str(datetime.datetime.now())
        logger.exception('Intersection meta data exception: %r' % e)


def get_intersection_meta_data(intersection_data):

    number_of_approaches = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                    for l in intersection_data['merged_lanes']
                                    if 'to_intersection' in l['meta_data']['identification']
                                    ]
                                   )
                               )
    number_of_exits = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                               for l in intersection_data['merged_lanes']
                               if 'from_intersection' in l['meta_data']['identification']
                               ]
                              )
                          )

    number_of_railway_approaches = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                            for l in intersection_data['merged_tracks']
                                            if 'to_intersection' in l['meta_data']['identification']
                                            ]
                                           )
                                       )
    number_of_railway_exits = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                       for l in intersection_data['merged_tracks']
                                       if 'from_intersection' in l['meta_data']['identification']
                                       ]
                                      )
                                  )

    if number_of_approaches > 0:
        max_number_of_lanes_in_approach = max([0] + [l['meta_data']['max_number_of_lanes']
                                                     for l in intersection_data['merged_lanes']
                                                     if 'to_intersection' in l['meta_data']['identification']
                                                     ]
                                              )
        min_number_of_lanes_in_approach = min([l['meta_data']['min_number_of_lanes']
                                               for l in intersection_data['merged_lanes']
                                               if 'to_intersection' in l['meta_data']['identification']
                                               ]
                                              )
    else:
        max_number_of_lanes_in_approach = 0
        min_number_of_lanes_in_approach = 0

    if number_of_exits > 0:
        max_number_of_lanes_in_exit = max([0] + [l['meta_data']['max_number_of_lanes']
                                                 for l in intersection_data['merged_lanes']
                                                 if 'from_intersection' in l['meta_data']['identification']
                                                 ]
                                          )
        min_number_of_lanes_in_exit = min([l['meta_data']['min_number_of_lanes']
                                           for l in intersection_data['merged_lanes']
                                           if 'from_intersection' in l['meta_data']['identification']
                                           ]
                                          )
    else:
        max_number_of_lanes_in_exit = 0
        min_number_of_lanes_in_exit = 0

    # Stop signs
    if any([l['meta_data']['stop_sign'] == 'yes' for l in intersection_data['merged_lanes']
       if 'stop_sign' in l['meta_data']]):
        stop_sign = 'yes'
    elif all([l['meta_data']['stop_sign'] == 'no' for l in intersection_data['merged_lanes']
             if 'stop_sign' in l['meta_data']]):
        stop_sign = 'no'
    else:
        stop_sign = None

    # Traffic signals
    if any([l['meta_data']['traffic_signals'] == 'yes' for l in intersection_data['merged_lanes']
       if 'traffic_signals' in l['meta_data']]):
        signal_present = 'yes'
    elif all([l['meta_data']['traffic_signals'] == 'no' for l in intersection_data['merged_lanes']
             if 'traffic_signals' in l['meta_data']]):
        signal_present = 'no'
    else:
        signal_present = None

    if signal_present is None and stop_sign == 'yes':
        signal_present = 'no'
    elif stop_sign is None and signal_present == 'yes':
        stop_sign = 'no'

    # Pedestrian_traffic_signals
    if any([l['meta_data']['pedestrian_traffic_signals'] == 'yes' for l in intersection_data['merged_lanes']]):
        pedestrian_traffic_signals = 'yes'
    elif all([l['meta_data']['pedestrian_traffic_signals'] == 'no' for l in intersection_data['merged_lanes']]):
        pedestrian_traffic_signals = 'no'
    else:
        pedestrian_traffic_signals = None

    if pedestrian_traffic_signals == 'yes':
        signal_present = 'yes'

    number_of_center_bicycle_approaches = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                                   for l in intersection_data['merged_lanes']
                                                   if 'to_intersection' in l['meta_data']['identification']
                                                   and l['meta_data']['bicycle_lane_on_the_left'] is not None
                                                   and 'yes' in l['meta_data']['bicycle_lane_on_the_left']
                                                   ]
                                                  )
                                              )
    number_of_right_side_bicycle_approaches = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                                       for l in intersection_data['merged_lanes']
                                                       if 'to_intersection' in l['meta_data']['identification']
                                                       and l['meta_data']['bicycle_lane_on_the_right'] is not None
                                                       and l['meta_data']['bicycle_lane_on_the_right'] != 'no'
                                                       ]
                                                      )
                                                  )
    number_of_center_bicycle_exits = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                              for l in intersection_data['merged_lanes']
                                              if 'from_intersection' in l['meta_data']['identification']
                                              and l['meta_data']['bicycle_lane_on_the_left'] is not None
                                              and 'yes' in l['meta_data']['bicycle_lane_on_the_left']
                                              ]
                                             )
                                         )
    number_of_right_side_bicycle_exits = len(set([l['meta_data']['identification'] + '_' + l['meta_data']['compass']
                                                  for l in intersection_data['merged_lanes']
                                                  if 'from_intersection' in l['meta_data']['identification']
                                                  and l['meta_data']['bicycle_lane_on_the_right'] is not None
                                                  and l['meta_data']['bicycle_lane_on_the_right'] != 'no'
                                                  ]
                                                 )
                                             )

    max_angle = 0.0
    for l1 in intersection_data['merged_lanes']:
        if 'from_intersection' in l1['direction']:
            continue
        b1 = l1['bearing']
        max_angle = max(max_angle, max([0] + [abs(get_angle_between_bearings(l2['bearing'], b1))
                                              for l2 in intersection_data['merged_lanes']
                                              if 'from_intersection' in l2['direction'] and l1['name'] != l2['name']]))

    if [n for n in intersection_data['nodes'] if 'subway' in intersection_data['nodes'][n]
       and intersection_data['nodes'][n]['subway'] == 'yes']:
        subway_station_present = 'yes'
    else:
        subway_station_present = 'no'

    rail_stations = [1 for n in intersection_data['nodes'] if 'light_rail' in intersection_data['nodes'][n]
                     and intersection_data['nodes'][n]['light_rail'] == 'yes'] + \
                    [1 for n in intersection_data['nodes'] if 'station' in intersection_data['nodes'][n]
                     and intersection_data['nodes'][n]['station'] == 'light_rail'] + \
                    [1 for n in intersection_data['nodes'] if 'railway' in intersection_data['nodes'][n]
                     and intersection_data['nodes'][n]['railway'] == 'station']

    bus_stops = [1 for n in intersection_data['nodes'] if 'highway' in intersection_data['nodes'][n]
                 and intersection_data['nodes'][n]['highway'] == 'bus_stop'] + \
                [1 for n in intersection_data['nodes'] if 'highway' in intersection_data['nodes'][n]
                 and 'trolley' in intersection_data['nodes'][n]['highway']]

    intersection_diameter = get_intersection_diameter(intersection_data)
    distance_to_next_intersection = get_distance_to_next_intersection(intersection_data, intersection_diameter)

    approach_street_types = get_list_of_highway_types(intersection_data, "to_intersection")
    exit_street_types = get_list_of_highway_types(intersection_data, "from_intersection")

    try:
        approach_list = [int(l['meta_data']['maxspeed'].split(' ')[0]) for l in intersection_data['merged_lanes']
                         if 'to_intersection' in l['meta_data']['identification']
                         ]
        if approach_list:
            approach_max_speed = str(max(approach_list)) + ' ' + 'mph'
            approach_min_speed = str(min(approach_list)) + ' ' + 'mph'
        else:
            approach_max_speed = '25 mph'
            approach_min_speed = '25 mph'

        exit_list = [int(l['meta_data']['maxspeed'].split(' ')[0]) for l in intersection_data['merged_lanes']
                     if 'from_intersection' in l['meta_data']['identification']
                     ]
        if exit_list:
            exit_max_speed = str(max(exit_list)) + ' ' + 'mph'
            exit_min_speed = str(min(exit_list)) + ' ' + 'mph'
        else:
            exit_max_speed = '25 mph'
            exit_min_speed = '25 mph'
    except:
        approach_max_speed = '25 mph'
        approach_min_speed = '25 mph'
        exit_max_speed = '25 mph'
        exit_min_speed = '25 mph'

    meta_data = {
                'number_of_approaches': number_of_approaches,
                'number_of_exits': number_of_exits,
                'max_number_of_lanes_in_approach': max_number_of_lanes_in_approach,
                'min_number_of_lanes_in_approach': min_number_of_lanes_in_approach,
                'number_of_railway_approaches': number_of_railway_approaches,
                'number_of_railway_exits': number_of_railway_exits,
                'max_number_of_lanes_in_exit': max_number_of_lanes_in_exit,
                'min_number_of_lanes_in_exit': min_number_of_lanes_in_exit,
                'number_of_center_bicycle_approaches': number_of_center_bicycle_approaches,
                'number_of_right_side_bicycle_approaches': number_of_right_side_bicycle_approaches,
                'number_of_center_bicycle_exits': number_of_center_bicycle_exits,
                'number_of_right_side_bicycle_exits': number_of_right_side_bicycle_exits,
                'signal_present': signal_present,
                'pedestrian_signal_present': pedestrian_traffic_signals,
                'diameter': intersection_diameter,
                'max_angle': max_angle,
                'max_curvature': max([0] + [l['meta_data']['curvature'] for l in intersection_data['merged_lanes']]),
                'min_curvature': min([l['meta_data']['curvature'] for l in intersection_data['merged_lanes']]),
                'distance_to_next_intersection': distance_to_next_intersection,
                'shortest_distance_to_railway_crossing': get_distance_to_railway_crossing(intersection_data),
                'subway_station_present': subway_station_present,
                'number_of_tram/train_stops': sum(rail_stations),
                'number_of_bus/trolley_stops': sum(bus_stops),
                'stop_sign': stop_sign,
                'approach_street_types': approach_street_types,
                'exit_street_types': exit_street_types,
                'approach_max_speed_limit' : approach_max_speed,
                'approach_min_speed_limit': approach_min_speed,
                'exit_max_speed_limit': exit_max_speed,
                'exit_min_speed_limit': exit_min_speed,
                'approach_counts': count_oneways(intersection_data, 'to_intersection'),
                'exit_counts': count_oneways(intersection_data, 'from_intersection'),
                }

    meta_data['timestamp'] = str(datetime.datetime.now())
    return meta_data


def get_lane_meta_data(lane_data, all_lanes, intersection_data, max_distance=20.0):
    """
    Create meta data dictionary for a lane (i.e. approach or exit)
    :param lane_data: dictionary of all lanes related to the intersection
    :param all_lanes: list of all lanes related to the intersection
    :param max_distance: max distance in meters for a transit stop to belong to a lane
    :param intersection_data: intersection data dictionary
    :return: dictionary
    """

    meta_data = {'city': intersection_data['city']}
    stops = intersection_data['public_transit_nodes']
    lane_data['city'] = intersection_data['city']

    if 'num_of_trunk_lanes' in lane_data:
        meta_data['total_number_of_vehicle_lanes'] = lane_data['num_of_left_lanes'] \
                                                     + lane_data['num_of_right_lanes'] \
                                                     + lane_data['num_of_trunk_lanes']
        meta_data['number_of_left-turning_lanes'] = lane_data['num_of_left_lanes']
        meta_data['number_of_right-turning_lanes'] = lane_data['num_of_right_lanes']

    if lane_data['lane_type'] == 'crosswalk':
        meta_data['identification'] = get_crosswalk_name(lane_data)
    else:
        if 'name' in lane_data:
            if 'no_name' in lane_data['name']:
                from_name, to_name = get_link_from_and_to(lane_data, all_lanes)
                if from_name is None or to_name is None:
                    meta_data['identification'] = lane_data['name'] + ' ' + lane_data['direction']
                else:
                    meta_data['identification'] = from_name + ' - ' + to_name + ' Link ' + lane_data['direction']
            else:
                meta_data['identification'] = lane_data['name'] + ' ' + lane_data['direction']
        else:
            meta_data['identification'] = 'undefined_name' + ' ' + lane_data['direction']

    if 'id' in lane_data:
        meta_data['id'] = lane_data['id']
    else:
        meta_data['id'] = None

    if len(get_connected_links(lane_data, all_lanes)) > 0:
        meta_data['right_turn_dedicated_link'] = 'yes'
    else:
        meta_data['right_turn_dedicated_link'] = 'no'

    meta_data['bicycle_lane_on_the_right'] = None
    meta_data['bicycle_lane_on_the_left'] = None

    if 'path' not in lane_data:
        meta_data['bicycle_lane_on_the_right'] = 'no'
        meta_data['bicycle_lane_on_the_left'] = 'no'
    else:
        for p in lane_data['path']:
            if key_value_check([('bicycle', 'no')], p):
                meta_data['bicycle_lane_on_the_right'] = 'no'
                meta_data['bicycle_lane_on_the_left'] = 'no'
                break
            elif is_shared(p):
                meta_data['bicycle_lane_on_the_right'] = 'shared'
                meta_data['bicycle_lane_on_the_left'] = 'no'
                break

            right, left = where_is_bicycle_lane(p)
            if meta_data['bicycle_lane_on_the_right'] is None:
                meta_data['bicycle_lane_on_the_right'] = right
            if meta_data['bicycle_lane_on_the_left'] is None:
                meta_data['bicycle_lane_on_the_left'] = left

    if 'rail' in lane_data['lane_type']:
        meta_data['rail_track'] = 'yes'
    else:
        meta_data['rail_track'] = 'no'
        node_set = set(lane_data['nodes'])
        for l in all_lanes:
            if 'rail' not in l['lane_type']:
                continue
            if len(node_set & set(l['nodes'])) > 0:
                meta_data['rail_track'] = 'yes'
                break

    if 'lane_type' in lane_data:
        meta_data['lane_type'] = lane_data['lane_type']

    stop_sign = None
    if 'nodes_dict' in lane_data:
        for n in lane_data['nodes_dict']:
            if 'highway' in lane_data['nodes_dict'][n] and lane_data['nodes_dict'][n]['highway'] == 'stop':
                stop_sign = 'yes'
                break

    traffic_signals = None
    if 'traffic_signals' in lane_data:
        meta_data['traffic_signals'] = lane_data['traffic_signals']
    else:
        if 'nodes_dict' in lane_data:
            for n in lane_data['nodes_dict']:
                if 'highway' in lane_data['nodes_dict'][n] \
                        and "traffic_signals" in lane_data['nodes_dict'][n]['highway']:
                    traffic_signals = 'yes'
                    break

    if traffic_signals is None and stop_sign == 'yes':
        traffic_signals = 'no'
    elif stop_sign is None and traffic_signals == 'yes':
        stop_sign = 'no'

    meta_data['traffic_signals'] = traffic_signals
    meta_data['stop_sign'] = stop_sign

    meta_data['number_of_crosswalks'] = None
    if 'footway' in lane_data and lane_data['footway'] == 'crossing':
        meta_data['number_of_crosswalks'] = 1
    if 'crossing' in lane_data:
        meta_data['number_of_crosswalks'] = 1
        if 'traffic_signal' in lane_data['crossing']:
            meta_data['pedestrian_traffic_signals'] = 'yes'
        else:
            meta_data['pedestrian_traffic_signals'] = 'no'
    else:
        meta_data['pedestrian_traffic_signals'] = None

    meta_data['compass'] = lane_data['compass']
    meta_data['length'] = get_border_length(lane_data['median'])

    if get_public_transit_stop(lane_data, stops, max_distance=max_distance):
        meta_data['public_transit_stop'] = 'yes'
    else:
        meta_data['public_transit_stop'] = None

    if 'railway' in lane_data and lane_data['railway'] == 'level_crossing':
        meta_data['crossing_railway'] = 'yes'
    else:
        meta_data['crossing_railway'] = None

    if 'median' in lane_data:
        curvature = get_border_curvature(lane_data['median'])
    else:
        curvature = get_border_curvature(lane_data['left_border'])

    meta_data['curvature'] = curvature
    num_of_lanes_list = [get_num_of_lanes(p) for p in lane_data['path']]
    if num_of_lanes_list:
        meta_data['max_number_of_lanes'] = max(num_of_lanes_list)
        meta_data['min_number_of_lanes'] = min(num_of_lanes_list)
    else:
        meta_data['max_number_of_lanes'] = 0
        meta_data['min_number_of_lanes'] = 0

    street_type = "undefined"
    if 'highway' in lane_data:
        street_type = lane_data['highway']
    meta_data['street_type'] = street_type

    maxspeed = '25 mph'
    if 'maxspeed' in lane_data:
        maxspeed = lane_data['maxspeed']
    meta_data['maxspeed'] = maxspeed

    meta_data['timestamp'] = str(datetime.datetime.now())

    return meta_data


def where_is_bicycle_lane(p):
    """
    Define bicycle lane location for meta_data
    :param p: dictionary
    :return: tuple of two strings.  Each element is either yes or no
    """
    location = get_bicycle_lane_location(p)
    right = 'no'
    left = 'no'
    if location['bicycle_forward_location'] is None and location['bicycle_backward_location'] is None:
        return 'no', 'no'
    if location['bicycle_forward_location'] == 'right' or location['bicycle_backward_location'] == 'right':
        right = 'yes'
    if location['bicycle_forward_location'] == 'left' or location['bicycle_backward_location'] == 'left':
        left = 'yes'

    return right, left


def get_crosswalk_name(crosswalk_data):
    """
    Construct a name for a crosswalk from the streets it is crossing
    :param crosswalk_data: dictionary
    :return: string
    """

    if crosswalk_data['lane_type'] != 'crosswalk':
        return None

    streets = [crosswalk_data['nodes_dict'][n]['street_name'] for n in crosswalk_data['nodes']
               if 'street_name' in crosswalk_data['nodes_dict'][n]
               and len(crosswalk_data['nodes_dict'][n]['street_name']) > 0
               and 'no_name' not in crosswalk_data['nodes_dict'][n]['street_name']
               and 'railway' not in crosswalk_data['nodes_dict'][n]
               ]

    if len(streets) == 0:
        crosswalk_name = 'no_name'
        end_street = ''
    else:
        crosswalk_name = ' '.join(sorted(list(streets[0])))
        end_street = ' '.join(sorted(list(streets[-1])))

    if crosswalk_name != end_street:
        crosswalk_name = crosswalk_name + ' - ' + end_street

    crosswalk_name += ' crosswalk'
    return crosswalk_name


def get_intersection_diameter(x_data):
    """
    Get the diameter of the intersection, which is defined as the max distance to the crosswalk border times 2.
    :param x_data: intersection dictionary
    :return: float distance in meters
    """

    guideways = get_through_guideways(x_data['merged_lanes'])
    if guideways:
        diameter = max([get_crosswalk_to_crosswalk_distance_along_guideway(g, x_data['crosswalks']) for g in guideways])
    else:
        logger.warning('No through guideways found %r' % '(' + ', '.join(list(x_data['streets']))+')')
        diameter = -2

    if diameter > 0:
        logger.debug('Intersection %s c2c diameter: %r' % ('(' + ', '.join(list(x_data['streets']))+')', diameter))
        return diameter
    else:
        logger.warning('Unable to find crosswalk to crosswalk distance for intersection %s'
                       % '(' + ', '.join(list(x_data['streets']))+')'
                       )

    x0 = x_data['center_x']
    y0 = x_data['center_y']
    all_lanes = x_data['merged_lanes']
    edge_points = [l['left_border'][-1] for l in all_lanes if 'to_intersection' in l['direction']]
    edge_points.extend([l['right_border'][-1] for l in all_lanes if 'to_intersection' in l['direction']])
    edge_points.extend([l['right_border'][0] for l in all_lanes if 'from_intersection' in l['direction']])
    edge_points.extend([l['left_border'][0] for l in all_lanes if 'from_intersection' in l['direction']])
    if x_data['crosswalks']:
        edge_points.extend([l['left_border'][0] for l in x_data['crosswalks']])
        edge_points.extend([l['right_border'][0] for l in x_data['crosswalks']])
        edge_points.extend([l['left_border'][-1] for l in x_data['crosswalks']])
        edge_points.extend([l['right_border'][-1] for l in x_data['crosswalks']])
        crosswalk_width = 0.0
    else:
        crosswalk_width = 2.538  # 1.8*sqrt(2)

    dist = [great_circle_vec_check_for_nan(y0, x0, p[1], p[0]) for p in edge_points]
    if len(dist) > 0:
        return (max(dist) + crosswalk_width)*2.0
    else:
        return None


def get_distance_to_railway_crossing(x_data):
    """
    Get the shortest distance to a railway crossing if applicable, -1 if no railway present.
    :param x_data: intersection dictionary
    :return: float distance in meters
    """
    x0 = x_data['center_x']
    y0 = x_data['center_y']

    if len(x_data['merged_tracks']) == 0:
        return -1

    edge_points = [l['left_border'][-1] for l in x_data['merged_tracks'] if 'to_intersection' in l['direction']]
    edge_points.extend([l['right_border'][-1] for l in x_data['merged_tracks'] if 'to_intersection' in l['direction']])
    edge_points.extend([l['right_border'][0] for l in x_data['merged_tracks'] if 'from_intersection' in l['direction']])
    edge_points.extend([l['left_border'][0] for l in x_data['merged_tracks'] if 'from_intersection' in l['direction']])
    dist_list = [great_circle_vec_check_for_nan(y0, x0, p[1], p[0]) for p in edge_points]
    if dist_list:
        return min([great_circle_vec_check_for_nan(y0, x0, p[1], p[0]) for p in edge_points])
    return -1


def get_distance_to_next_intersection(x_data, intersection_diameter):
    """
    Get minimum distance to another intersection.  
    It should be at least 20 m (or the intersection diameter) away to be considered as a separate intersection.
    :param x_data: intersection dictionary
    :param intersection_diameter: float
    :return: float distance in meters
    """
    other_intersection_nodes = set()
    dist_threshold = max(20.0, intersection_diameter)
    x0 = x_data['center_x']
    y0 = x_data['center_y']

    for n in x_data['nodes']:
        if 'street_name' not in x_data['nodes'][n]:
            continue
        if len(x_data['nodes'][n]['street_name']) < 2:
            continue
        if great_circle_vec_check_for_nan(y0, x0, x_data['nodes'][n]['y'], x_data['nodes'][n]['x']) < dist_threshold:
            continue
        for s in x_data['nodes'][n]['street_name']:
            if '_link' in s:
                continue
            if s not in x_data['streets']:
                other_intersection_nodes.add(n)

    if len(other_intersection_nodes) == 0:
        return -1
    else:
        return min([great_circle_vec_check_for_nan(y0, x0, x_data['nodes'][n]['y'], x_data['nodes'][n]['x'])
                    for n in other_intersection_nodes]
                   )


def get_list_of_highway_types(x_data, direction):
    """
    Get a dictionary of street types for all approaches or all exits.  
    Each key is a type, each value is a number of occurrences per direction.
    Multiple lanes of the same street are counted as one occurrence.
    :param x_data: intersection dictionary
    :param direction: string either "to_intersection" or "from_intersection"
    :return: dictionary of street types.
    """
    types = {}
    street_names = set([l['name'] for l in x_data['merged_lanes']])
    for st in street_names:
        street_types = set([l['highway'] for l in x_data['merged_lanes'] if st in l['meta_data']['identification']
                            and direction in l['meta_data']['identification']
                            ]
                           )
        for street_type in street_types:
            if street_type in types:
                types[street_type] += 1
            else:
                types[street_type] = 1

    number_of_cycleways = len([l['id'] for l in x_data['merged_cycleways'] if direction in l['direction']])
    if number_of_cycleways:
        types['cycleway'] = number_of_cycleways
    number_of_tracks = len([l['id'] for l in x_data['merged_tracks'] if direction in l['direction']])
    if number_of_tracks:
        types['track'] = number_of_tracks
    return types


def count_oneways(intersection_data, direction):
    """
    Count numbers of oneway, twoway or singleway for approaches or exits
    oneway is an approach or exit if the opposite traffic exists over a distance or divider
    singleway is an approach or exit if no opposite traffic
    twoway is an approach or exit adjacent to the opposite traffic without divider
    :param intersection_data: intersection dictionary
    :param direction: string
    :return: dictionary of counts
    """
    counts = {'oneway': 0, 'twoway': 0, 'singleway': 0}
    street_names = set([l['name'] for l in intersection_data['merged_lanes']])
    for st in street_names:
        two_way_count = len(set(
            [l['compass'] for l in intersection_data['merged_lanes'] if st in l['meta_data']['identification']
             and direction in l['meta_data']['identification']
             and 'split' in l
             and l['split']
             and l['split'][-1] == 'yes'
             ]
            )
        )

        one_way_count = len(set(
            [l['compass'] for l in intersection_data['merged_lanes'] if st in l['meta_data']['identification']
             and direction in l['meta_data']['identification']
             and 'split' in l
             and l['split']
             and l['split'][-1] == 'no'
             and is_opposite_lane_exist(l, intersection_data['merged_lanes'])
             ]
            )
        )

        single_way_count = len(set(
            [l['compass'] for l in intersection_data['merged_lanes'] if st in l['meta_data']['identification']
             and direction in l['meta_data']['identification']
             and 'split' in l
             and l['split']
             and l['split'][-1] == 'no'
             and not is_opposite_lane_exist(l, intersection_data['merged_lanes'])
             ]
            )
        )

        counts['oneway'] += one_way_count
        counts['twoway'] += two_way_count
        counts['singleway'] += single_way_count

    return counts
