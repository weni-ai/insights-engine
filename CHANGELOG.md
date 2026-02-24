# 1.7.1
# Add
  - Getting user request for analysis 
  
# 1.7.0
# Add
  - Endpoint for template message
  
# 1.6.4
# Fix
 - Query source on elasticsearch flowrun results

# 1.6.3
# Fix
 - Simplify query construction in ConversationsElasticsearchService by integrating search_after directly into the query and removing redundant params
 - Update pagination handling in ConversationsElasticsearchService to use search_after instead of page_number

# 1.6.2
# Add
 - Add validation for product_type in TemplatesMetricsAnalyticsBodySerializer to ensure only valid options are accepted
# Fix
 - Change product_type field in TemplatesMetricsAnalyticsBodySerializer from ChoiceField to CharField for improved flexibility

# 1.6.1
# Fix
 - Orders API endpoint path in VtexOrdersRestClient

# 1.6.0
# Add
 - Internal jwt authentication

# 1.5.1
# Fix
 - Add unclassified and unknown labels to the conversations resolutions report worksheet

# 1.5.0
# Fix
 - CSAT/NPS Elasticsearch date filters

# 1.4.14
# Add
 - Contact and urn filter in detailed monitoring

# 1.4.13
# Refactor
 - Remove redundant test for empty data in get_transferred_to_human_worksheet

# 1.4.12
# Add
 - Combine conversations resolutions and transfer to human in export

# 1.4.11
# Fix
 - Return parameters in HumanSupportDashboardService's _get_analysis_detailed_monitoring_status_filters

# 1.4.10
# Refactor
 - Reduce cyclomatic complexity in the human support dashboard V2 and the conversations dashboard service

# 1.4.9
# Add
 - Analysis CSAT ratings filters

# 1.4.8
# Add
 - Crosstab's full value
 - Increase test coverage

# 1.4.7
# Remove
 - Remove human support dashboard V1 feature flag

# 1.4.6
# Remove
 - Remove Insights pagination for detailed monitoring status (to use only Chat's pagination)

# 1.4.5
# Add
 - Limit and offset to Chats internal call in the human support dashboard's monitoring status

# 1.4.4
# Add
 - CSAT ratings to finished rooms

# 1.4.3
# Remove
 - Conversations report feature flag

# 1.4.2
# Fix
 - Conversations report range date

# 1.4.1
# Add
 - Resolutions events translations for conversations report export

# 1.4.0
# Add
 - Create human support dashboard V2 when creating a project

# 1.3.4
# Add
 - Available widgets endpoint

# 1.3.3
# Add
 - New status label in agents list route
 - Feature flag to hide human support V1 (old) dashboards from list

# 1.3.2
# Fix
 - Sales funnel calculation when source field value is not an integer

# 1.3.1
# Fix
 - Initialize crosstab data serializer with default field name

# 1.3.0
# Refactor
 - Reduce human support dashboard complexity
# Add
 - Crosstab serialization classes and source validation

# 1.2.10
# Fix
 - Get analysis status filters

# 1.2.9
# Refactor
 - Reduce conversations report complexity

# 1.2.8
# Add
 - Update Weni Feature Flags' version and use Weni Commons

# 1.2.7
# Add
 - Filter human support dashboard rooms by contact external id

# 1.2.6
# Fix
 - change analysis peak human timeseries query to use hour instead of date

# 1.2.5
# Refactor
  - reduce topics distribution method complexity

# 1.2.4
# Add
  - v2 version of new human dashboard

# 1.2.3
# Fix
  - subtopics unclassified count

# 1.2.2
# Fix
  - conversations elasticsearch flowruns response

# 1.2.1
# Fix
  - fetch elasticsearch with serializable project UUID and convert datetime

# 1.2.0
# Add
  - sending conversations dashboard report link instead of attaching files to the email

# 1.1.6
# Fix
  - conversations dashboard report service date conversion to ISO format
  when fetching events from the datalake

# 1.1.5
# Fix
  - add conversations dashboards report page limit environment variables

# 1.1.4
# Add
  - conversations dashboard report email's template

# 1.1.3
# Remove
  - formatting date logs and sentry exceptions

# 1.1.2
# Add
  - new logic for calculating the total number of conversations
  in the conversations dashboard
  - new logic for building the human support data export
  from the conversations dashboard
  - fallback for formatting dates in conversations dashboard
  reports worksheets
# Fix
  - conversations report check if ready permission

# 1.1.1
# Fix
  - check if event has metadata before trying to convert to dict
    in the sales funnel feature

# 1.1.0
# Add
  - replace feature flags logic with new Weni Feature Flags library

# 1.0.0
## Fix
  - removing mock from get widget data
