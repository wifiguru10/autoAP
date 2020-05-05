# autoAP


# AutoAP by Nico Darrow

# Description: 

   AutoAP script will watch all the organizations that your API key is active in and look for the following to activate

   1. Enable API access on ORG and generate an API key
   2. Tag the "Network" that you want inscope with "autoAP" (Overview Page)
   3. In the MS Network, tag all the switches that you want inscope with "autoAP"
   4. In the MR Network, tag all the APs that you want inscope with "autoAP" 
       - if you don't want the AP's port to be configured, don't tag the AP or switch to excempt
   5. In the MR Network, tag the MASTER ap with "AP:master"
       - you can tag only ONE ap per switch with "AP:master"
       - multiple "AP:master" tags will allow you to have different "profiles" per switch, not recommended in this version of script
   6. Run the command line 'export MERAKI_DASHBOARD_API_KEY="<KEY>"' on your command line before running the script
   7. Run the script and it'll loop perpetually
   8. Every loop you'll see the switches blinking their LED's when the script is checking them, that way installers can see if it's still running


   CAVEATS/Recommendations
       1. Test it first, don't be silly and run this in production. There WILL be bugs, run it in non-WRITE mode first
       2. This version is mainly for single network deployments, preferrably combined networks, future versions will be Complete org
       3. Only has been tested on combined networks, won't work across multiple networks
