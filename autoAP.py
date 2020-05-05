#!/usr/bin/python3

### AutoAP by Nico Darrow

### Description: 
#
#   AutoAP script will watch all the organizations that your API key is active in and look for the following to activate
#
#   1. Enable API access on ORG and generate an API key
#   2. Tag the "Network" that you want inscope with "autoAP" (Overview Page)
#   3. In the MS Network, tag all the switches that you want inscope with "autoAP"
#   4. In the MR Network, tag all the APs that you want inscope with "autoAP" 
#       - if you don't want the AP's port to be configured, don't tag the AP or switch to excempt
#   5. In the MR Network, tag the MASTER ap with "AP:master"
#       - you can tag only ONE ap per switch with "AP:master"
#       - multiple "AP:master" tags will allow you to have different "profiles" per switch, not recommended in this version of script
#   6. Run the command line 'export MERAKI_DASHBOARD_API_KEY="<KEY>"' on your command line before running the script
#   7. Run the script and it'll loop perpetually
#   8. Every loop you'll see the switches blinking their LED's when the script is checking them, that way installers can see if it's still running
#
#
#   CAVEATS/Recommendations
#       1. Test it first, don't be silly and run this in production. There WILL be bugs, run it in non-WRITE mode first
#       2. This version is mainly for single network deployments, preferrably combined networks, future versions will be Complete org
#       3. Only has been tested on combined networks, won't work across multiple networks
#   


import csv
import meraki
from datetime import datetime
import os, sys
import time

from tagHelper import *

tag_network_TARGET = "autoAP"
tag_device_TARGET = "autoAP"
tag_ap_master   = "AP:master"
tag_port_master = "AP:master"
tag_port_clone  = "AP:clone"
tag_port_AUTO = "AP:auto"


WRITE = True
AUTO_TAG = True #Should the script auto-bind the master AP to a switch port if it isn't specified with 'AP:master' tag?


# converts 981888fc1e17 to '98:18:88:fc:1e:17'
def convert_mac(mac):
    if len(mac) != 12:
        print("Error: can't convert mac, not the right length")
        return 

    nm = mac[0:2] + ':' + mac[2:4] + ':' + mac[4:6] + ':' + mac[6:8] + ':' + mac[8:10] + ':' + mac[10:12]
    return nm

#clones a port, {p} is a port object (dict)
def clone_port(dashboard, masterP, serial, p):
    name = p['name']
    port = int(p['number'])
    if not p['tags'] is None and tag_port_clone in p['tags']:
        tags = p['tags']
    else:
        if p['tags'] is None:
            tags = tag_port_clone
        else:
            tags = p['tags'] + " " + tag_port_clone
    if not 'enabled' in masterP:
        return
    enabled = masterP['enabled']
    ptype = masterP['type']
    vlan = masterP['vlan']
    if ptype == "trunk":
        allowedVlans = masterP['allowedVlans']
    else:
        voiceVlan = masterP['voiceVlan']
    poeEnabled = masterP['poeEnabled']
    isolationEnabled = masterP['isolationEnabled']
    rstpEnabled = masterP['rstpEnabled']
    stpGuard = masterP['stpGuard']
    linkNegotiation = masterP['linkNegotiation']
    udld = masterP['udld']

    delta = False
    
    if not p['tags'] is None and not tag_port_clone in p['tags']:       delta = True #use case if you already have the port configured correctly, doesn't get TAG
    if enabled != p['enabled']: delta = True
    if ptype != p['type']:      delta = True
    if vlan != p['vlan']:       delta = True
    if ptype == "trunk":
        if allowedVlans != p['allowedVlans']:   delta = True
    else:
        if voiceVlan != p['voiceVlan']:         delta = True
    if poeEnabled != p['poeEnabled']:           delta = True
    if isolationEnabled != p['isolationEnabled']:   delta = True
    if rstpEnabled != p['rstpEnabled']:         delta = True
    if stpGuard != p['stpGuard']:               delta = True
    if linkNegotiation != p['linkNegotiation']: delta = True
    if udld != p['udld']:                       delta = True

    if not delta:
        return



    print(f'WRITE:  programming port[{port}] on switch[{serial}]')
#    print(f'{masterP}')
#    print()
#    print(f'{p}')
    if WRITE:
        if ptype == "trunk":
            result=dashboard.switch_ports.updateDeviceSwitchPort(serial=serial,number=port,tags=tags,type=ptype,enabled=enabled,vlan=vlan,allowedVlans=allowedVlans,poeEnabled=poeEnabled,isolationEnabled=isolationEnabled,rstpEnabled=rstpEnabled,stpGuard=stpGuard,linkNegotiation=linkNegotiation,udld=udld)
        else:
            result=dashboard.switch_ports.updateDeviceSwitchPort(serial=serial,number=port,tags=tags,type=ptype,enabled=enabled,vlan=vlan,voiceVlan=voiceVlan,poeEnabled=poeEnabled,isolationEnabled=isolationEnabled,rstpEnabled=rstpEnabled,stpGuard=stpGuard,linkNegotiation=linkNegotiation,udld=udld)
        print()
    return

#returns clients
def getNetClients(dashboard, networkId):
    result = dashboard.clients.getNetworkClients(networkId)
    return result

def inscope_info(devices_inscope):
    print("[NETWORKS INSCOPE]")
    for orgid in devices_inscope:
        MS = 0
        MR = 0
        devs = devices_inscope[orgid]
        for d in devs:
            if d['model'][:2] == "MS":
                MS += 1
            if d['model'][:2] == "MR":
                MR += 1
#                print(d)
        print(f'\tOrg[{orgid}]')
        print(f'\t\tSwitches[{MS}]\tAccessPoints[{MR}]')
    print()
    return



def main():

    # client_query() # this queries current org and all client information and builds database
    # exit()

    # Fire up Meraki API and build DB's
    TH = tagHelper() #new SDK for device querying 
    dashboard = TH.getDashboard()
    orgs = TH.getOrgs() 
    orgs_inscope = TH.getOrgNets_inscope()

        
    loop = True

    last_changes = []
    count = 5
    while loop:
        print()
        print("**************START LOOP***************")
        print()
        if count <= 0:
            TH.updAll() #updates all and updates INSCOPE devices/networks
            orgs = TH.getOrgNets()
            orgs_inscope = TH.getOrgNets_inscope()
            count = 5
        else:
            TH.update() #updates INSCOPE devices/tags only
            count -= 1

       
        #check clients, find APs and make sure their ports are configured
        print()
        devices_inscope = TH.getOrgDev_inscope() # { 'orgid' : [{device}] }
        master_ports = TH.getMasterPorts() # { 'serial' : [{port}] }
        if len(master_ports) == 0:
            print(f'WARNING: No Master ports detected')
            mAP = TH.getMasterAp() #this returns {}
            masterAPmacs = []
            for tmp_netid in mAP:
                for net in mAP[tmp_netid]:
                    if 'mac' in net and not net['mac'] is None:
                        masterAPmacs.append(net['mac'])
            print(f'All Master AP MACs found {masterAPmacs}')
                

            if len(masterAPmacs) == 0:
                print(f'WARNING: No Master AP detected either, cannot rebind master port')
                continue
            else:
                #found MasterAP
                #NOW TO FIND THE PORT AND SET ITS TAG
                change = False #boolean flag
                for orgId in devices_inscope:
                    devs = devices_inscope[orgId]
                    for d in devs:
                        if d['model'][:2] == "MS":
                            serial=d['serial']
                            ports = dashboard.switch_ports.getDeviceSwitchPortStatuses(serial)
                            ports_cfg = dashboard.switch_ports.getDeviceSwitchPorts(serial)
                            for p in ports:
                                if p['status'] == "Connected":
                                    mac = ""
                                    if 'lldp' in p and 'chassisId' in p['lldp']:
                                        mac = p['lldp']['chassisId']
                                    if not mac in masterAPmacs:
                                        continue
                                    if 'cdp' in p and 'platform' in p['cdp'] and p['cdp']['platform'][:6] == "Meraki":
                                        # THIS PORT HAS A MERAKI MR
                                        #{'portId': '18', 'enabled': True, 'status': 'Connected', 'errors': [], 'warnings': [], 'speed': '1 Gbps', 'duplex': 'full', 'usageInKb': {'total': 385, 'sent': 209, 'recv': 176}, 'cdp': {'platform': 'Meraki MR46 Cloud Managed Indoor AP', 'deviceId': '981888fc1e17', 'portId': 'Port 0', 'address': '10.99.8.17', 'version': '1', 'capabilities': 'Router, Switch'}, 'lldp': {'systemName': 'Meraki MR46 - 2.11', 'systemDescription': 'Meraki MR46 Cloud Managed Indoor AP', 'portId': '0', 'chassisId': '98:18:88:fc:1e:17', 'portDescription': 'eth0', 'systemCapabilities': 'Two-port MAC Relay'}, 'clientCount': 1, 'powerUsageInWh': 2.3, 'trafficInKbps': {'total': 0.0, 'sent': 0.0, 'recv': 0.0}}
                                        pId = int(p['portId'])
                                        for port_cfg in ports_cfg:
                                            if 'number' in port_cfg and port_cfg['number'] == pId:
                                                newTags = "" 
                                                if not port_cfg['tags'] is None:
                                                    newTags = tag_port_master + " " + port_cfg['tags'] #need the space in here to seperate tags
                                                else:
                                                    newTags = tag_port_master
                                                #clone_port(dashboard,master_port,sw_serial,port_tmp)
                                                if(WRITE):
                                                    dashboard.switch_ports.updateDeviceSwitchPort(serial=serial, number=pId, tags=newTags)
                                                print(f'Setting Master AP TAG for port {pId} on switch {serial}')
                                                change = True

                            
                if change: #if the masterAP port changed, re-loop to better approach this
                    print("BREAKING")
                    count = 0 #force an update
                    TH.updAll()
                    continue #need to reset here, if there is no masterAP it'll error


        #START PORT CLONE AND CONFIG

        inscope_info(devices_inscope)
        for org_id in devices_inscope:
            devices = devices_inscope[org_id]
            for d in devices:
                if d['model'][:2] == "MS":
                    sw_serial = d['serial']

                    master_port = TH.getMasterPort(sw_serial)
                    if not 'number' in master_port: #if you couldn't find the serial, use the networkID
                        master_port = TH.getMasterPort(d['networkId'])
                    
                    print(f'Blinking {sw_serial}')
                    dashboard.devices.blinkNetworkDeviceLeds(d['networkId'], serial=sw_serial, duration=5, duty=10, period=100 )
                    ports = dashboard.switch_ports.getDeviceSwitchPortStatuses(sw_serial)
                    ports_cfg = dashboard.switch_ports.getDeviceSwitchPorts(sw_serial)
                    masterMACS = TH.getMasterAp_macs()
                    for p in ports:
                        if p['status'] == "Connected":
                            mac = ""
                            if 'lldp' in p and 'chassisId' in p['lldp']:
                                mac = p['lldp']['chassisId']
                            if not mac in masterMACS:
                                continue
                            if 'cdp' in p and 'platform' in p['cdp'] and p['cdp']['platform'][:6] == "Meraki":
                                # THIS PORT HAS A MERAKI MR
                                #{'portId': '18', 'enabled': True, 'status': 'Connected', 'errors': [], 'warnings': [], 'speed': '1 Gbps', 'duplex': 'full', 'usageInKb': {'total': 385, 'sent': 209, 'recv': 176}, 'cdp': {'platform': 'Meraki MR46 Cloud Managed Indoor AP', 'deviceId': '981888fc1e17', 'portId': 'Port 0', 'address': '10.99.8.17', 'version': '1', 'capabilities': 'Router, Switch'}, 'lldp': {'systemName': 'Meraki MR46 - 2.11', 'systemDescription': 'Meraki MR46 Cloud Managed Indoor AP', 'portId': '0', 'chassisId': '98:18:88:fc:1e:17', 'portDescription': 'eth0', 'systemCapabilities': 'Two-port MAC Relay'}, 'clientCount': 1, 'powerUsageInWh': 2.3, 'trafficInKbps': {'total': 0.0, 'sent': 0.0, 'recv': 0.0}}
                                #CHECK TO SEE IF THE CONFIG MATCHES MASTER
                                port_tmp = {}
                                for port_cfg in ports_cfg:
                                    if 'number' in port_cfg and port_cfg['number'] == int(p['portId']):
                                        port_tmp = port_cfg
                                        clone_port(dashboard,master_port,sw_serial,port_tmp)

                                
                                               
                                



        for orgId in devices_inscope:
            devs = devices_inscope[orgId]
            for d in devs:
                if d['model'][:2] == "MS":
                    serial=d['serial']
                    ports = dashboard.switch_ports.getDeviceSwitchPorts(serial=serial)
                    stats = dashboard.switch_ports.getDeviceSwitchPortStatuses(serial=serial)
    #                print(len(ports))
     #               print(len(stats))
                    for p in ports:
                        if not 'tags' in p:
                            continue 
                        tags = p['tags']
                        if tags is None:
                            continue
      #                  print(f'Tags: {tags}')
                        if not tag_port_clone in tags and not tag_port_master in tags: 
                            continue
                        pId = p['number']
                        for s in stats:
                            sId = int(s['portId'])
                            if pId == sId:
                                if s['status'] == "Disconnected":
                                    print(f'Old switchport detected: Clearing flag on switch[{serial}] port[{pId}]')
                                    newTags = p['tags'].replace(tag_port_clone,'')
                                    newTags = newTags.replace(tag_port_master,'')

                                    if(WRITE):
                                        dashboard.switch_ports.updateDeviceSwitchPort(serial=serial, number=pId, tags=newTags)



        #dashboard.devices.getNetworkDeviceUplink("N_577586652210338281",serial="Q2MW-MW3X-LG3U") 
        # 'publicIp' - public ip
        # 'gateway' - gateway ip

        #

        print()
        print("**************END LOOP***************")
        print()

        time.sleep(15)
        print()
        print()
        # while loop


if __name__ == '__main__':
    start_time = datetime.now()

    print()
    main()
    end_time = datetime.now()
    print(f'\nScript complete, total runtime {end_time - start_time}')
