#!/user/bin/python

import json
import requests
import PureCloudPlatformClientV2 as v2
import numpy as np
from datetime import datetime
import os, re
import time
import asyncio
from aiohttp import ClientSession


#Contansts to capture json data for state.

sites = []
created_sites = []
site_routes = []

locations = []
created_locations = []

groups = []
created_groups = []
updated_group = []

queues = []
created_queues = []
queue_wrap_codes = []

emergency_groups = []
created_emergency_groups = []

schedules = []
created_schedules = []

schedule_groups = []
created_schedule_groups = []

users = []
created_users = []
updated_users = []

wrapup_codes = []
created_wrapup_codes = []

trunks = []
call_routes = []

line_bases = []
phone_bases = []
created_phones = []

dids = []
extensions = []

org_roles = []
prompts_created = []

user_ids = []
users_roles = []

#environment variables for OAuth keys
GENESYS_CLOUD_CLIENT_ID = os.getenv('GENESYS_CLOUD_CLIENT_ID_CE')
GENESYS_CLOUD_CLIENT_SECRET = os.getenv('GENESYS_CLOUD_CLIENT_SECRET_CE')

def get_api_token():
    #Setting the Region
    region = v2.PureCloudRegionHosts.us_west_2
    v2.configuration.host = region.get_api_host()
    #with Client Credntials Create a token object
    apiclient = v2.api_client.ApiClient().get_client_credentials_token(GENESYS_CLOUD_CLIENT_ID, GENESYS_CLOUD_CLIENT_SECRET)
    global apitoken
    #collect token from token object
    apitoken = apiclient.access_token
    global headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'authorization': f'Bearer {apitoken}'
        }
        

api_url = "https://api.usw2.pure.cloud/api/v2/"


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'to_json'):
            return obj.to_json()
        if isinstance(obj, np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)
'''
#if Windows OS 
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
'''

async def get_template(url):
    async with ClientSession(headers=headers) as session:
        dump_list = []
        async with session.get(url) as resp:
            response = await resp.json()
            dump_list.append(response)
            page_number = response.get('pageNumber')
            page_count = response.get('pageCount')
            if page_count == None:
                page_count = 1

            while page_count != page_number:
                page_number += 1
                resp = session.get(f'{url}&pageNumber={page_number}')
                response = await resp.json()
                dump_list.append(response)
    return dump_list


#    ****************************          SITES GROUPING       ***********************

async def get_sites():
    url = f"{api_url}telephony/providers/edges/sites?pageSize=100"
    site_list = await get_template(url)

    for list in site_list:
        for site in list['entities']:
            id = site.get('id')
            name = site.get('name')
            location = site['location'].get('name')
            caller_name = site.get('callerName')
            caller_id = str(site.get('callerId'))
            sites.append({'name': name, 'id': id, 'linkedLocation': location, 'callerName': caller_name, 'callerId': caller_id})


#create a site
def create_site(site_name, div_id, address, caller_id, caller_number, location_name, location_id):
    url = f"{api_url}telephony/providers/edges/sites"
    site_payload = json.dumps({
        "name": site_name,
        "division": {
            "id": div_id
        },
        "version": 1,
        "state": "active",
        "description": address,
        "callerId": caller_number,
        "callerName": caller_id,
        "mediaModel": "Cloud",
        "location": {
            "name": location_name,
            "state": "active",
            "version": 1,
            "id": location_id
        }
    },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=site_payload)
    created_sites.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_sites[0]['message']] 




async def get_trunks():
    url = f"{api_url}telephony/providers/edges/trunks?pageSize=100"
    trunk_list = await get_template(url)

    for list in trunk_list:
        for trunk in list['entities']:
            trunk_name = trunk.get('name')
            trunk_id = trunk.get('id')
            trunk_base_id = trunk['trunkBase'].get('id')
            if trunk['trunkType'] == 'EXTERNAL':
                trunks.append({"name": trunk_name, "id": trunk_id, "trunkBaseId": trunk_base_id})




def set_outbound_route(site_id,div_id,source_trunk_base,site_trunk_base):
    url = f"{api_url}telephony/providers/edges/sites/{site_id}/outboundroutes?"
    payload={}
    get_response = requests.request("GET", url, headers=headers, data=payload)
    route = json.loads(get_response.text)
    time.sleep(0.5)
    
    route_name = route['entities'][0].get('name')
    route_id = route['entities'][0].get('id')

    time.sleep(0.5)

    url = f"{api_url}telephony/providers/edges/sites/{site_id}/outboundroutes/{route_id}"
    payload = json.dumps({
        "name": route_name,
        "division": {
            "id": div_id
        },
        "classificationTypes": [
            "Emergency",
            "National",
            "International",
            "Network"
        ],
        "enabled": True,
        "distribution": "SEQUENTIAL",
        "externalTrunkBases": [
            {
            "id": source_trunk_base
            },
            {
            "id": site_trunk_base
            }
        ]
        })
    response = requests.request("PUT", url, headers=headers, data=payload)
    site_routes.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,site_routes[0]['message']]


def check_site(check_name:str):
    results = regex_search(sites,check_name,'name')
    if results:
        return results



# *************************************     LOCATION GROUPING            ******************************

def validate_address(city,state,street,house_num,zip_code):
    url = f"{api_url}telephony/providers/edges/addressvalidation"
    verified_payload = json.dumps({
        "address": {
            "A3": city,
            "A1": state,
            "RD": street,
            "PC": zip_code,
            "country": "US",
            "HNO": house_num
            }
        })
    response = requests.request("POST", url, headers=headers, data=verified_payload)
    verified = json.loads(response.text)
    if response.status_code <= 300:
        if verified['valid'] == True:
            return {f'{city}, {state} {zip_code}. {house_num} {street}': 'Address Verified'}
        else:
            return {f'{city}, {state} {zip_code}. {house_num} {street}': 'NOT Verified'}
    else:
        return {'error': 'Bad Request'}

#create a location
def create_location(location_name,elin,phone_number,city,state,address1,address2,zipcode):
    url = f"{api_url}locations"
    #collecting data from excel through pandas df. storing in payload
    location_payload = json.dumps({
        "name": location_name,
        "version": 1,
        "state": "active",
        "emergencyNumber": {
            "e164": elin,
            "number": phone_number,
            "type": "elin"
        },
        "address": {
            "city": city,
            "country": "US",
            "countryName": "United States",
            "state": state,
            "street1": address1,
            "street2": address2,
            "zipcode": zipcode
            },
        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=location_payload)
    created_locations.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_locations[0]['message']]
        


async def get_locations():
    url = f"{api_url}locations?pageSize=100"
    location_list = await get_template(url)

    for list in location_list: 
        for location in list['entities']:
            id = location.get('id')
            name = location.get('name')
            verified = location.get('addressVerified')
            try:
                city = location['address'].get('city')
                state = location['address'].get('state')
                street1 = location['address'].get('street1')
                if location['address'].get('street2') != None:
                    street2 = location['address'].get('street2')
                else:
                    street2 = ""
                zipcode = str(location['address'].get('zipcode'))
                try:
                    elin = str(location['emergencyNumber'].get('e164'))
                except KeyError:
                    elin = "*No Emergency Number for location*"
                locations.append({'name': name, 'id': id, 'city': city,'state': state,'street1': street1,'street2': street2,'zipcode':zipcode, 'elin': elin, 'addressVerified': verified})
            except KeyError:
                locations.append({'name': name, 'id': id, 'addressVerified': verified})



def check_location(check_name:str,check_street1:str, check_number:str):
    results = []
    check_elin = re.sub(r'[+-]','', check_number).strip()
    result_name = regex_search(locations,check_name,'name')
    result_steet1 = regex_search(locations,check_street1,'street1')
    result_elin = regex_search(locations,check_elin,'elin')
    result_did = regex_search(dids,check_elin,'phoneNumber')
    
    check_results = [result_name,result_steet1,result_elin,result_did]
    
    for check in check_results:
        if check:
            results.append(check)
    if results:
        return results

#************************************               GROUP GROUPING            ******************************************

async def get_groups():
    url = f"{api_url}groups?pageSize=100"
    group_list = await get_template(url)

    for list in group_list:
        for group in list['entities']:
            owners = []
            id = group.get('id')
            name = group.get('name')
            addresses = group.get('addresses')
            if addresses != None:
                for address in addresses:
                    try:
                        did = str(address.get('address'))
                    except KeyError:
                        did = str(address.get('extension'))
            else: 
                did = "*No DID or Extension"
            member_count = group.get('memberCount')
            owner_ids = group.get('owners')
            if owner_ids != None:
                for owner in owner_ids:           
                    owners.append(owner.get('id'))
            groups.append({'name': name, 'id': id, 'phoneNumber': did, 'memberCount': member_count, 'owners': owners})
    

#create a group
def create_group(group_name,elin):
    url = f"{api_url}groups"
    group_payload = json.dumps({
        "name": group_name,
        "state": "active",
        "version": 1,
        "type": "official",
        "addresses": [
            {
            "type": "GROUPRING",
            "mediaType": "PHONE",
            "address": elin,
            }
        ],
        "rulesVisible": "true",
        "visibility": "public",
        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=group_payload)
    created_groups.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_groups[0]['message']]


def set_group_membership(group_id,group_member_ids):
    url = f"{api_url}groups/{group_id}/members"
    group_membership_payload = json.dumps({
        "memberIds": group_member_ids,
        "version": 2
        })
    response = requests.request("POST", url, headers=headers, data=group_membership_payload)
    return response.status_code


def update_group(group_id,owner_ids):
    url = f"{api_url}groups/{group_id}"
    payload = json.dumps({
        "state": "active",
        "version": 1,
        "rulesVisible": "true",
        "visibility": "Public",
        "ownerIds": 
            owner_ids
        })
    response = requests.request("PUT", url, headers=headers, data=payload)
    updated_group.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,updated_group[0]['message']]

def check_group(check_name:str,check_number:str):
    results = []
    check_phone_number = re.sub(r'[+-]','', check_number).strip()
    result_name = regex_search(groups,check_name,'name')
    result_phone_number = regex_search(groups,check_phone_number,'phoneNumber')
    result_did = regex_search(dids,check_phone_number,'phoneNumber')
    result_extension = regex_search(extensions,check_phone_number,'phoneNumber')
    
    check_results = [result_name,result_phone_number,result_did,result_extension]
    
    for check in check_results:
        if check:
            results.append(check)
    if results:
        return results


# ********************************************          QUEUE GROUPING                 **************************************************


async def get_queues():
    url = f"{api_url}routing/queues?pageSize=100"
    queue_list = await get_template(url)

    for list in queue_list:
        for queue in list['entities']:
            id = queue.get('id')
            name = queue.get('name')
            member_count = queue.get('memberCount')
            division = queue['division'].get('name')
            caller_name = queue.get('callingPartyName')
            caller_id = queue.get('callingPartyNumber')
            try:
                queue_flow = queue['queueFlow'].get('name')
            except KeyError:
                queue_flow = "*No Queue Flow associated*"
            acw_settings = queue.get('acwSettings')
            call = queue['mediaSettings'].get('call')
            queues.append({'name': name, 'id': id,'division': division,'memberCount': member_count, 'callingPartyName': caller_name, 'callingPartyNumber': caller_id, 'queueFlow': queue_flow, 'acwSettings': acw_settings, 'call': call})



#create 2 queues | Main & Priority
def create_queue(queue_name,div_id,caller_id,caller_number):
    url = f"{api_url}routing/queues"
    queue_payload = json.dumps({
        "name": queue_name,
        "division": {
            "id": div_id
        },
        "routingRules": [],
        "mediaSettings": {
            "call": {
                    "alertingTimeoutSeconds": 15,
                    "serviceLevel": {
                        "percentage": 0.8,
                        "durationMs": 20000
                    }
                },
                "callback": {
                    "alertingTimeoutSeconds": 30,
                    "serviceLevel": {
                        "percentage": 0.8,
                        "durationMs": 20000
                    }
                },
            },
        
        "acwSettings": {
            "wrapupPrompt": "MANDATORY_TIMEOUT",
            "timeoutMs": 90000
        },
        "skillEvaluationMethod": "ALL",
        "autoAnswerOnly": "false",
        "enableTranscription": "false",
        "enableManualAssignment": "false",
        "callingPartyName": caller_id,
        "callingPartyNumber": caller_number

        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=queue_payload)
    created_queues.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_queues[0]['message']]



def set_queue_membership(queue_id,queue_member_ids):
    url = f"{api_url}routing/queues/{queue_id}/members?delete=false"
    queue_membership_payload = json.dumps(queue_member_ids)
    response = requests.request("POST", url, headers=headers, data=queue_membership_payload)
    return response.status_code
    


async def get_wrap_codes():
    url = f"{api_url}routing/wrapupcodes?pageSize=100"
    wrap_code_list = await get_template(url)

    for list in wrap_code_list:
        for wrap_code in list['entities']:
            name = wrap_code.get('name')
            id = wrap_code.get('id')
            wrapup_codes.append({'name': name, 'id': id})


def set_queue_wrap_codes(queue_id,wrap_code_ids):
    url = f"{api_url}routing/queues/{queue_id}/wrapupcodes"
    queue_wrap_payload = json.dumps(wrap_code_ids)
    response = requests.request("POST", url, headers=headers, data=queue_wrap_payload)
    queue_wrap_codes.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,queue_wrap_codes[0]['message']]


def check_queue(check_name:str):
    results = regex_search(queues,check_name,'name')
    if results:
        return results

def check_wrapcode(check_name:str):
    results = regex_search(wrapup_codes,check_name,'name')
    if not results:
        return check_name


#********************************************              SCHEDULE GROUPING                     **************************************************


async def get_schedules():
    url = f"{api_url}architect/schedules?pageSize=100"
    schedule_list = await get_template(url)

    for list in schedule_list:
        for schedule in list['entities']:
            id = schedule.get('id')
            name = schedule.get('name')
            division = schedule['division'].get('name')
            start = schedule.get('start')
            start = change_datetime(start)
            end = schedule.get('end')
            end = change_datetime(end)
            frequency = schedule.get('rrule')
            schedules.append({'name': name, 'id': id, 'division': division, 'start': start, 'end': end, 'frequency': frequency})

        
def change_datetime(time):
    date_time = datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%f')
    sched_date = date_time.date().strftime('%m/%d/%Y')
    sched_time = date_time.time().strftime('%I:%M %p')
    time = f'{sched_date} @ {sched_time}' 
    return time
        

async def get_schedule_groups():
    url = f"{api_url}architect/schedulegroups?pageSize=100"
    schedule_group_list = await get_template(url)

    for list in schedule_group_list:
        for schedule_group in list['entities']:
            open_schedule_ids = []
            closed_schedule_ids = []
            holiday_schedule_ids = []
            id = schedule_group.get('id')
            name = schedule_group.get('name')
            division = schedule_group['division'].get('name')
            time_zone = schedule_group.get('timeZone')
            open_schedules = schedule_group.get('openSchedules')
            if open_schedules != None:
                for open_schedule in open_schedules:
                    open_schedule_ids.append(open_schedule.get('id'))

            closed_schedules = schedule_group.get('closedSchedules')
            if closed_schedules != None:
                for closed_schedule in closed_schedules:
                    closed_schedule_ids.append(closed_schedule.get('id'))

            holiday_schedules = schedule_group.get('holidaySchedules')
            if holiday_schedules != None:
                for holiday_schedule in holiday_schedules:
                    holiday_schedule_ids.append(holiday_schedule.get('id'))

            schedule_groups.append({'name': name, 'id': id,'division': division, 'timeZone': time_zone, 'openSchedules': open_schedule_ids, 'closedSchedules': closed_schedule_ids, 'holidaySchedules': holiday_schedule_ids})


#create a list of schedules
def create_schedules(schedule_name,div_id,start,end,rrules):
    url = f"{api_url}architect/schedules"
    schedule_payload = json.dumps({
        "name": schedule_name,
        "division": {
            "id": div_id
        },
        "version": 1,
        "state": "active",
        "start": start,
        "end": end,
        "rrule": rrules
        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=schedule_payload)
    created_schedules.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_schedules[0]['message']]
   

#create a schedule group, pass in all schedule made to either holiday, open or closed.
def create_schedule_group(schedule_group_name,div_id,timezone,open_schedules,holidays):
    url = f"{api_url}architect/schedulegroups"
    schedule_group_payload = json.dumps({
        "name": schedule_group_name,
        "division": {
            "id": div_id
        },
        "version": 1,
        "state": "active",
        "timeZone": timezone,
        "openSchedules": open_schedules,
        "holidaySchedules": holidays
        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=schedule_group_payload)
    created_schedule_groups.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_schedule_groups[0]['message']]


def check_schedule(check_name:str):
    results = regex_search(schedules,check_name,'name')
    if results:
        return results    

def check_sched_group(check_name:str):
    results = regex_search(schedule_groups,check_name,'name')
    if results:
        return results
        

# ********************************************             ETC GROUPING              **************************************************

def regex_search(iterable:list,query,key:str): 
    results = []
    regex_string = re.escape(query)
    for iter in iterable:
        try:
            if re.search(regex_string,iter[key],re.IGNORECASE):
                results.append(iter)
        except KeyError:
            pass
    return results


async def get_emergency_groups():
    url = f"{api_url}architect/emergencygroups?pageSize=100"
    emergency_group_list = await get_template(url)

    for list in emergency_group_list:
        for emergency_group in list['entities']:
            name = emergency_group.get('name')
            division = emergency_group['division'].get('name')
            emergency_groups.append({'name': name, 'division': division})  


def create_emergency_groups(group_name,div_id):
    url = f"{api_url}architect/emergencygroups"
    emergency_group_payload = json.dumps({
        "name": group_name,
        "division": {
            "id": div_id
        },
        "version": 1,
        "state": "active"
        })
    response = requests.request("POST", url, headers=headers, data=emergency_group_payload)
    created_emergency_groups.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_emergency_groups[0]['message']]


async def get_call_routes():
    url = f"{api_url}architect/ivrs?pageNumber=1&pageSize=100"
    call_route_list = await get_template(url)

    for list in call_route_list:
        for call_route in list['entities']:
            did = call_route.get('dnis')
            name = call_route.get('name')
            call_routes.append({'name': name, 'did': did})


async def get_dids():
    url = f"{api_url}telephony/providers/edges/dids?pageSize=100"
    did_list = await get_template(url)

    for list in did_list:
        for did in list['entities']:
            number = did.get('phoneNumber')
            owner = did['owner'].get('name')
            owner_type = did.get('ownerType')
            dids.append({'phoneNumber': number, 'name': owner, 'ownerType': owner_type})


async def get_extensions():
    url = f"{api_url}telephony/providers/edges/extensions?pageSize=100"
    extension_list = await get_template(url)

    for list in extension_list:
        for extension in list['entities']:
            number = extension.get('number')
            owner = extension['owner'].get('name')
            owner_type = extension.get('ownerType')
           
            extensions.append({'phoneNumber': number, 'name': owner, 'ownerType': owner_type})
 

async def get_org_roles():
    url = f"{api_url}authorization/roles?pageSize=100"
    org_roles_list = await get_template(url)

    for page in org_roles_list:
        for role in page['entities']:
            role_name = role.get('name')
            role_id = role.get('id')
            org_roles.append({'id': role_id, 'name': role_name})


def check_em_group(check_name:str):
    results = regex_search(emergency_groups,check_name,'name')
    if results:
        return results

def check_call_route(check_name:str,numbers):
    results = []
    numbers = re.sub(r'[+-]','',numbers)
    if len(numbers) > 18:
        result_dids = []
        numbers = numbers.split(',')
        for num in numbers:
            num = num.strip()
            num_search = regex_search(dids,num,'phoneNumber')
            if num_search:
                result_dids.append(num_search)
    else:
        result_dids = regex_search(dids,numbers,'phoneNumber')

    result_name = regex_search(call_routes,check_name,'name')
    check_results = [result_name,result_dids]

    for check in check_results:
        if check:
            results.append(check)
    if results:
        return results


#********************************************     USERS GROUPING         **************************************************


async def get_all_users():
    url = f"{api_url}users?expand=locations,groups&pageSize=100"
    user_list = await get_template(url)

    for list in user_list:
        for user in list['entities']:
            location_ids = []
            group_ids = []
            extensions = []
            id = user.get('id')
            name = user.get('name')
            division = user['division'].get('name')
            email = user.get('email')
            title = user.get('title')
            usr_locations = user.get('locations')
            for location in usr_locations:
                location_ids.append(location['locationDefinition'].get('id'))
            usr_groups = user.get('groups')
            for group in usr_groups:
                group_ids.append(group.get('id'))
            try:
                addresses = user.get('addresses')
                for address in addresses:
                    try:
                        extensions.append(address.get('extension'))
                    except:
                        extensions.append("No Extension")
            except KeyError:
               extensions.append("No Extension")
            users.append({'name': name, 'id': id, 'division': division, 'email': email, 'extension': extensions, 'title': title, 'locations': location_ids, 'groups': group_ids})
            

#create a user
def create_user(div_id,user_name,user_email,user_extension,user_title,user_department,location_id):
    url = f"{api_url}users"
    user_payload = json.dumps({
        "name": user_name,
        "department": user_department,
        "email": user_email,
        "locations": [{"id": location_id}],
        "title": user_title,
        "password": "Password123!",
        "divisionId": div_id,
        "primaryContactInfo": [
            {
            "address": user_email,
            "mediaType": "EMAIL",
            "type": "PRIMARY"
            },
            {
            "address": "",
            "mediaType": "PHONE",
            "type": "PRIMARY",
            "extension": user_extension
            }
        ]
        },cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=user_payload)
    data = json.loads(response.text)
    created_users.append(data)
    if response.status_code < 300:
        return response.status_code
    else:
        try:
            return [response.status_code,data['message']]
        except KeyError:
            return response.status_code


#for each user, REPLACE ALL roles with those supplied
def set_user_roles(usr_roles,user_id,div_id):
    user_roles = list(usr_roles.split(', '))
    final_roles = []
    for user_role in user_roles:
        for role in org_roles:
            if user_role == role['name']:
                final_roles.append({"roleId": role.get('id'), "divisionId": div_id})
    url = f"{api_url}authorization/subjects/{user_id}/bulkreplace?subjectType=PC_USER"
    user_roles_payload = json.dumps({
        "grants": 
            final_roles
        })
    response = requests.request("POST", url, headers=headers, data=user_roles_payload)
    try:
        updated_users.append(json.loads(response.text))
    except:
        pass
    
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,updated_users[0]['message']]



def set_user_location(user_id,location_id):
    url = f"{api_url}users/{user_id}"
    payload = json.dumps({
        "version": 2,
        "locations": [
            {
            "id": location_id
            }
        ]
        })
    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.status_code


def check_user(check_name:str,check_email:str,check_number:str):
    results = []
    check_phone_number = re.sub(r'[+-]','', check_number).strip()
    result_name = regex_search(users,check_name,'name')
    result_email = regex_search(users,check_email,'email')
    result_extension = regex_search(extensions,check_phone_number,'phoneNumber')
    
    check_results = [result_name,result_email,result_extension]
    
    for check in check_results:
        if check:
            results.append(check)
    if results:
        return results

#********************************************     PHONE GROUPING         **************************************************


async def get_phone_bases():
    url = f"{api_url}telephony/providers/edges/phonebasesettings?pageSize=100"
    phone_base_list = await get_template(url)

    for list in phone_base_list:
        for phone in list['entities']:
            name = phone.get('name')
            id = phone.get('id')
            phone_bases.append({'id': id, 'name': name})
        


async def get_line_bases():
    url = f"{api_url}telephony/providers/edges/linebasesettings?pageSize=100"
    line_base_list = await get_template(url)

    for list in line_base_list:
        for line in list['entities']:
            name = line.get('name')
            id = line.get('id')
            line_bases.append({'id': id, 'name': name})


#create a WebRTC phone for each user
def create_phone(div_id,site_id,phone_name,user_id,phone_base_id,line_base_id):
    url = f"{api_url}telephony/providers/edges/phones"
    #attribute lineBaseSettings is hard coded for to grab Demo Web RTC
    phone_payload = json.dumps({
        "name": phone_name,
        "division": {
            "id": div_id
        },
        "description": "Web RTC phone",
        "version": 1,
        "state": "active",
        "site": {
            "id": site_id
        },
        "lines": [{
            "lineBaseSettings": {
            "id": line_base_id
            }
        }],
        "phoneBaseSettings": {
            "id": phone_base_id
        },
        "webRtcUser": {
            "id": user_id
        }},cls=JSONEncoder)
    response = requests.request("POST", url, headers=headers, data=phone_payload)
    created_phones.append(json.loads(response.text))
    if response.status_code < 300:
        return response.status_code
    else:
        return [response.status_code,created_phones[0]['message']]
        


#set each phone to default for user profile phone was created for
def set_phone_default():
    for phone in created_phones:
        line_id = phone['lines'][0].get('id')
        user_id = phone['webRtcUser'].get('id')
        url = f"{api_url}users/{user_id}/station/defaultstation/{line_id}"
        default_phone_payload={}
        response = requests.request("PUT", url, headers=headers, data=default_phone_payload)
        return response.status_code



#creating custom prompt, creating custom prompt resource. nesting resource in prompt with return to prompts_data.
def create_custom_prompts(prompt_name,prompt_script,resources):
    prompt_resources = []
    prompt_url = f"{api_url}architect/prompts"
    prompt_payload = json.dumps({
        "name": prompt_name,
        "description": prompt_script,
        "resources": []
        })
    prompt_response = requests.request("POST", prompt_url, headers=headers, data=prompt_payload)
    prompt_text = json.loads(prompt_response.text)
    pprint(prompt_text)
    prompt_id = prompt_text.get('id')
    time.sleep(0.5)


    for resource in resources:
        resource_url = f"{api_url}architect/prompts/{prompt_id}/resources"
        resource_payload = json.dumps({
            "name": resource,
            "language": resource,
            "ttsString": prompt_script,
            "text": prompt_script
            })
        resource_response = requests.request("POST", resource_url, headers=headers, data=resource_payload)
        resource_text = json.loads(resource_response.text)
        prompt_resources.append(resource_text)
        time.sleep(0.3)
    prompt_text['resources'] = prompt_resources
    full_response = prompt_text
    prompts_created.append(full_response)
    if prompt_response.status_code < 300:
        return [prompt_response.status_code]
    else:
        return [prompt_response.status_code,prompts_created[0]['message']]
    

    


async def get_init_state():
    await get_sites()
    await get_trunks()
    await get_locations()
    await get_groups()
    await get_queues()
    await get_wrap_codes()
    await get_schedules()
    await get_schedule_groups()
    await get_emergency_groups()
    await get_dids()
    await get_extensions()
    await get_call_routes()
    await get_org_roles()
    await get_all_users()
    await get_phone_bases()
    await get_line_bases()
    


'''
def get_prompts():
    prompt_list = []
    url = f"{api_url}architect/prompts?pageSize=100&sortOrder=asc"
    payload={}  
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    prompt_list.append(data)
    page_number = data.get('pageNumber')
    page_count = data.get('pageCount')
    

    while page_count != page_number:
        page_number += 1
        page_url = f"{api_url}architect/prompts?pageSize=100&pageNumber={page_number}&sortOrder=asc"
        get_user_payload={}
        response = requests.request("GET", page_url, headers=headers, data=get_user_payload)
        prompt_list.append(json.loads(response.text))

    
    for list in prompt_list:
        for prompt in list['entities']:
            prompt_name = prompt.get('name')
            prompt_description = prompt.get('description')
            prompts.append({'name': prompt_name, 'description': prompt_description})






'''