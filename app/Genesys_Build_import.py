#!/user/bin/python

import pandas as pd
import Genesys_Build_backend as Genesys_Backend
from Genesys_Build_backend import asyncio

def zero_constansts():
    Genesys_Backend.sites = []
    Genesys_Backend.locations = []
    Genesys_Backend.groups = []
    Genesys_Backend.queues = []
    Genesys_Backend.emergency_groups = []
    Genesys_Backend.schedules = []
    Genesys_Backend.schedule_groups = []
    Genesys_Backend.users = []
    Genesys_Backend.wrapup_codes = []
    Genesys_Backend.trunks = []
    Genesys_Backend.call_routes = []
    Genesys_Backend.line_bases = []
    Genesys_Backend.phone_bases = []
    Genesys_Backend.dids = []
    Genesys_Backend.extensions = []
    Genesys_Backend.org_roles = []


def sync_backend():
    zero_constansts()
    asyncio.run(Genesys_Backend.get_init_state())

def discard_none(iterable,key):
    iter_errors = []
    for iter in iterable:
        if iter[key]:
            iter_errors.append(iter.get(key))
    return iter_errors
        

def import_excel(excel):
    excel_dict = transform_excel(excel)

    location_details = verify_locations(excel_dict['locations'])
    
    address_verified = discard_none(location_details,'addressVerified')
    location_errors = discard_none(location_details,'locationErrors')

    site_details = verify_sites(excel_dict['sites'])
    site_errors = discard_none(site_details,'siteErrors')

    queue_details = verify_queues(excel_dict['queues'])
    queue_errors = discard_none(queue_details,'queueErrors')

    wrap_code_details = verify_wrapcodes(excel_dict['wrapUpCodes'])
    wrap_code_errors = discard_none(wrap_code_details,'wrapCodeErrors')

    group_details = verify_groups(excel_dict['groups'])
    group_errors = discard_none(group_details,'groupErrors')

    schedule_details = verify_schedules(excel_dict['schedules']) 
    schedule_errors = discard_none(schedule_details,'scheduleErrors')

    sched_group_details = verify_sched_groups(excel_dict['scheduleGroups'])
    sched_group_errors = discard_none(sched_group_details,'scheduleGroupErrors')

    em_group_details = verify_em_groups(excel_dict['emergencyGroups'])
    em_group_errors = discard_none(em_group_details,'emergencyGroupErrors')

    call_route_details = verify_call_routes(excel_dict['callRoutes'])
    call_route_errors = discard_none(call_route_details,'callRouteErrors')

    agent_details = verify_agents(excel_dict['agents'])
    agent_errors = discard_none(agent_details,'agentErrors')
    
    return {'data': excel_dict,'addressVerify': address_verified,'errors':
                {'locationErrors': location_errors,'siteErrors': site_errors,
                'queuErrors': queue_errors,'wrapCodeErrors': wrap_code_errors,'groupErrors': group_errors,
                'scheduleErrors': schedule_errors,'scheduleGroupErrors': sched_group_errors,
                'emergencyGroupErrors': em_group_errors,'callRouteErrors': call_route_errors,
                'agentErrors': agent_errors}}


def transform_excel(build_excel):
    location_df = build_excel['Location']
    location_sheet = location_df.iloc[:6].dropna(thresh=3).fillna('')
    locations = location_sheet.to_dict('records')
        
    site_df = location_df.iloc[7:, :-2].rename(columns=location_df.iloc[6]).loc[1:]
    site_sheet = site_df.reset_index(drop=True).fillna('')
    sites = site_sheet.to_dict('records')

    queue_df = build_excel['Queues']
    queue_sheet = queue_df.iloc[:14, :-4].dropna(thresh=3).fillna('')
    queues = queue_sheet.to_dict('records')

    wrap_code_sheet = queue_df.iloc[:, 9:10].dropna()
    wrap_codes = wrap_code_sheet.to_dict('records')
        
    group_df = queue_df.iloc[15:, :-6].rename(columns=queue_df.iloc[14]).loc[1:]
    group_sheet = group_df.reset_index(drop=True).fillna('')
    groups = group_sheet.to_dict('records')

    schedule_df = build_excel['Schedules']
    schedule_sheet = schedule_df.iloc[:14, :-2].dropna(thresh=3).fillna('')
    schedules = schedule_sheet.to_dict('records')
        
    sched_group_df = schedule_df.iloc[15:].rename(columns=schedule_df.iloc[14]).loc[1:]
    sched_group_sheet = sched_group_df.reset_index(drop=True).fillna('')
    sched_groups = sched_group_sheet.to_dict('records')

    em_group_df = build_excel['Emergency Groups']
    em_group_sheet = em_group_df.iloc[:, :2].dropna(thresh=2)
    em_groups = em_group_sheet.to_dict('records')

    call_route_sheet = em_group_df.iloc[:, 4:9].dropna(thresh=3)
    call_routes = call_route_sheet.to_dict('records')

    agent_df = build_excel['Agents']
    agent_sheet = agent_df.iloc[:, :13].dropna(thresh=9).fillna('')
    agents = agent_sheet.to_dict('records')
    
    return {'locations': locations,'sites': sites,'queues': queues,'wrapUpCodes': wrap_codes,
    'groups': groups,'schedules': schedules,'scheduleGroups': sched_groups,
    'emergencyGroups': em_groups,'callRoutes': call_routes,'agents': agents}


def verify_locations(locations):
    location_checklist = []
    for location in locations:
        elin = str(location['e164'])[1:]
        street = location['Street 1'].split(" ",1)
        check_locations = Genesys_Backend.check_location(location['Location Name'],location['Street 1'],elin)
        verified = Genesys_Backend.validate_address(location['City'], location['State'],street[1],street[0],str(int(location['Zip Code'])))
        location_checklist.append({'addressVerified': verified, 'locationErrors': check_locations})
    return location_checklist
    

def verify_sites(sites): 
    site_checklist = []      
    for site in sites:
        check_site = Genesys_Backend.check_site(site['Site Name'])
        site_checklist.append({'siteErrors': check_site})
    return site_checklist

def verify_groups(groups):
    group_checklist = []    
    for group in groups:
        if group['e164'] != '':
            group_number = str(group['e164'])[1:]
        else:
            group_number = str(group['Extension'])
        check_group = Genesys_Backend.check_group(group['Group Name'],group_number)    
        group_checklist.append({'groupErrors': check_group})
    return group_checklist
    
def verify_queues(queues):
    queue_checklist = []
    for queue in queues:
        check_queue = Genesys_Backend.check_queue(queue['Queue Name'])
        queue_checklist.append({'queueErrors': check_queue})
    return queue_checklist

def verify_wrapcodes(wrapcodes):
    wrapcodes_checklist = []
    for wrapcode in wrapcodes:
        check_wrapcode = Genesys_Backend.check_wrapcode(wrapcode['Standard'])
        wrapcodes_checklist.append({'wrapCodeErrors': check_wrapcode})
    return wrapcodes_checklist

def verify_schedules(schedules):
    schedule_checklist = []
    for schedule in schedules:
        check_schedule = Genesys_Backend.check_schedule(schedule['Schedule Name'])
        schedule_checklist.append({'scheduleErrors': check_schedule})
    return schedule_checklist

def verify_sched_groups(sched_groups):
    sched_group_checklist = []
    for sched_group in sched_groups:
        check_sched_group = Genesys_Backend.check_sched_group(sched_group['Schedule Group Name'])
        sched_group_checklist.append({'scheduleGroupErrors': check_sched_group})
    return sched_group_checklist

def verify_em_groups(em_groups):
    em_group_checklist = []
    for em_group in em_groups:
        check_em_group = Genesys_Backend.check_em_group(em_group['Emergency Group Name'])
        em_group_checklist.append({'emergencyGroupErrors': check_em_group})
    return em_group_checklist

def verify_call_routes(call_routes):
    call_route_checklist = []
    for call_route in call_routes:
        check_call_route = Genesys_Backend.check_call_route(call_route['Call Route Name'],call_route['DIDs'])
        call_route_checklist.append({'callRouteErrors': check_call_route})
    return call_route_checklist

def verify_agents(agents):
    agent_checklist = []
    for agent in agents:
        check_agent = Genesys_Backend.check_user(agent['Name'],agent['Email'],str(agent['Extension']))
        agent_checklist.append({'agentErrors': check_agent})
    return agent_checklist

        
