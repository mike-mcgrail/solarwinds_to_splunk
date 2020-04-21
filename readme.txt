Background:
SolarWinds custom alert properties are not easily retrieved via API queries (several tables need to be joined and the primary/foreign keys are not well implemented).  As such, we are using the Splunk Add-On for Solarwinds to retrieve asset inventory while sending alerts to HEC.  Subsequently, ITSI can create episodes then alert to third-party tools such as Remedy ITSM or PagerDuty.  Additinally, the SolarWinds Reset action can be used in ITSI as logic to break episodes.

Details:
1. SolarWinds calls a .bat file as a wrapper, which passes arguments (SolarWinds cannot execute Python directly)
2. alert.bat passes arguments to alert.py to parse and format JSON payload
3. send_to_splunk.py sends payload to HEC

Prerequisites:
1. Install Python 3 on SolarWinds server
2. Install Python requests module (including any dependencies if necessary)
3. Splunk index solarwinds is created on indexers
4. Splunk HTTP event collector token is ready on HEC servers for SolarWinds to use

Configuration:
SolarWinds:
1. Install files on the SolarWinds server (default is D:\solarwinds_to_splunk)
2. Update alert.bat line 18 to match the Python and solarwinds_to_splunk installation directories
3. Add the HEC destination & token to send_to_splunk.py line 27 and save the updated file
4. Modify alert.py to match your environment and needs
5. Set SolarWinds Alerts actions to call alert.bat. In our environment, 5 variables are required:
    <alert name>
    <node name>
    <node IP address>
    <alert detailed message body>
    <link to SolarWinds>
    Example: D:\solarwinds_to_splunk\alert.bat "${AlertName}" "${NodeName}" "${N=SwisEntity;M=Node.IP_Address}" "${N=Alerting;M=AlertMessage}" "${N=Alerting;M=AlertDetailsUrl}" "alert"
6. [optional] Set SolarWinds Reset actions to call alert.bat with "Reset"
    Example: D:\solarwinds_to_splunk\alert.bat "${AlertName}" "${NodeName}" "${N=SwisEntity;M=Node.IP_Address}" "${N=Alerting;M=AlertMessage}" "${N=Alerting;M=AlertDetailsUrl}" "reset"
7. Add optional parameters as needed, ensuring alert.py and SolarWinds alert actions are updated to correspond. In our environment, 3 variables are used:
    -t <yes or no> (to create an ITSM incident)
    -g <ITSM support group name>
    -k kba#
8. test_alert.bat is also provided which will simply log the JSON payload without sending it to HEC. This is useful to test first to ensure SolarWinds variables are producing the desired results.

Splunk/ITSI:
8. Configure lookups as needed.  This may include alert destinations or enrichment of ITSM group details (e.g. Remedy Company & Organization to match the Support Group)
9. Configure ITSI Correlation Search to create episodes on index=solarwinds sourcetype="solarwinds:hec:alert". The link to the SolarWinds alert can be used as the drilldown website link.
10. Configure ITSI Notable Event Aggregation Policy to take action

Example of a standard alert with no ITSM ticketing information:
D:\solarwinds_to_splunk\alert.bat "${AlertName}" "${NodeName}" "${N=SwisEntity;M=Node.IP_Address}" "${N=Alerting;M=AlertMessage}" "${N=Alerting;M=AlertDetailsUrl}" "alert"

Example of an alert set to create an incident to Network and include a KBA number:
D:\solarwinds_to_splunk\alert.bat "${AlertName}" "${NodeName}" "${IP}" "<alert message>" "${AlertDetailsUrl}" -t yes -g "Network" -k "KBA12345"

Example Basic Correlation Search
index=solarwinds sourcetype="solarwinds:hec:alert" 
| eval sw_status=status 
| eval itsi_alert=alert 
| eval itsi_node=node 
| eval itsi_url=url 
| eval itsi_severity=case(severity == "LOW", 3, severity == "MEDIUM", 4, severity == "HIGH", 5, severity == "CRITICAL", 6) 
| eval itsi_status=case(sw_status == "alert", 1, sw_status == "reset", 5) 
| `apply_entity_lookup(itsi_node)`

Example Correlation Search enriching additional details with lookups:
index=solarwinds sourcetype="solarwinds:hec:alert" 
| eval sw_status=status 
| eval itsi_alert=alert 
| eval itsi_node=node 
| eval itsi_url=url 
| eval itsi_severity=case(severity == "LOW", 3, severity == "MEDIUM", 4, severity == "HIGH", 5, severity == "CRITICAL", 6) 
| eval itsi_status=case(sw_status == "alert", 1, sw_status == "reset", 5) 
| eval itsi_action_ticket=if(ticket == "yes", 1, 0) 
| eval remedy_group=group 
| eval remedy_kba=if(isnotnull(kba), kba, "(no kba)")
| lookup remedy_groups.csv Support_Group_Name AS remedy_group OUTPUTNEW Company AS remedy_company Support_Organization AS remedy_organization
| eval remedy_impact=case(severity == "LOW", "4-Minor/Localized", severity == "MEDIUM", "3-Moderate/Limited", severity == "HIGH", "2-Significant/Large", severity == "CRITICAL", "2-Significant/Large")
| eval remedy_urgency=case(severity == "LOW", "4-Low", severity == "MEDIUM", "3-Medium", severity == "HIGH", "2-High", severity == "CRITICAL", "1-Critical")
| lookup alert_solarwinds.csv instance AS alert OUTPUTNEW action_pagerduty pagerduty_service 
| eval itsi_action_pagerduty=if(action_pagerduty == "1", 1, 0) 
| lookup pageduty_keys service_name AS pagerduty_service OUTPUTNEW integration_key AS pagerduty_integration_key 
| `apply_entity_lookup(itsi_node)`

Example NEAP details
Filtering:
Include the events if: search_name matches Solarwinds Alert Search
Split events into multiple episodes by: msg

Action Rules:
If itsi_action_ticket matches 1 and sw_status matches alert: Remedy Incident Integration
If itsi_action_pagerduty matches 1 and sw_status matches alert: PagerDuty Incident Integration
If sw_status matches reset: Add a comment and close the episode