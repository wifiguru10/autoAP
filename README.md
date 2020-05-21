# AutoAP 
   A script to automatically configure and sync AP ports via API to mirror the functionality of the "Secure Connect" switch feature. The only "configuration" needed for the script is to insert your API key and tag the "inscope" devices on dashboard.

# Description: 

   AutoAP script will loop every 15 seconds watching all the organizations accessible by your API key. You can tag switches and APs with "autoAP" to have the script monitor/configure/sync that hardware (to constrain the scope of the script). Removing the TAGs will excude the hardware/APs from autoAP. This script can be run in a container perpetually if desired.
   
# Use Cases:
   1. New site deployments - only configure one switchport for the master AP(seed AP), as you plug in APs the switch ports will automatically mirror the first "seed" AP.
   2. Existing deployments - adding vlans or changing trunk ports across a network can easily miss a port if not properly managed. This script can "fix" any misconfigurations by syncing with the master port. Any future changes to that master port is syncronized across all other clone ports.
   3. Multiple profiles per network - you can have a lab network which has different switch port settings than a production wireless deployment. (roadmap)
   4. Bulk deployments - auto-assign APs into networks from provisioning network (roadmap)

# Safety
   A switch port will only be configured if the following safety gates have been met
   
      1. The network is tagged with "autoAP" (no tag means ALL hardware in that network is except regardless of tag)
      2. The switch needs to be tagged with "autoAP" (no tag means the switch is excuded from the scope)
      3. There has to be APs tagged with "autoAP" and a SINGLE master AP tagged with "AP:master"

# Instructions
   1. Enable API access on ORG and generate an API key
   2. Tag the "Network" that you want inscope with "autoAP" (Overview Page)
   3. In the MS Network, tag all the switches that you want inscope with "autoAP"
   4. In the MR Network, tag all the APs that you want inscope with "autoAP" 
   5. In the same MR Network, tag the MASTER ap with "AP:master" (this means it's configured switch port is the "golden config" for all other switchports)
       - you can tag only ONE ap per switch with "AP:master"
       - multiple "AP:master" tags will allow you to have different "profiles" per switch, not recommended in this version of script
   6. Run the command line 'export MERAKI_DASHBOARD_API_KEY="<KEY>"' on your command line before running the script
   7. Run the script and it'll loop perpetually
   8. Every loop you'll see the switches blinking their LED's when the script is checking them, that way installers can see if it's still running


# Recommendations
       1. Test it first, don't be silly and run this in production. There WILL be bugs, run it in non-WRITE mode first
            -set the variable "WRITE" to False to make it read-only
       2. This version is mainly for single network deployments, preferrably combined networks, future versions will be Complete org
       3. Only has been tested on combined networks, won't work across multiple networks at the current version
