# 1.23.3
# Fix
  - SQL join conditions for removed queues and sectors in room filters

# 1.23.2
# Fix
  - List operation results handling in QueryExecutor

# 1.23.1
# Add
  - Finished rooms V2 with restructured query execution
# Fix
  - CI complexity configuration

# 1.23.0
# Add
  - Detailed monitoring endpoints for agent status
  - Deletion status tracking for queues, sectors, and tags in room query results
# Fix
  - Date formatting in human support dashboard service

# 1.22.0
# Add
  - Data source service integration with feature flag support

# 1.21.1
# Fix
  - Update query to exclude deleted tags in TagSQLQueryBuilder

# 1.21.0
# Add
  - Inline agent switch functionality on project creation

# 1.20.0
# Add
  - Agent invocations metrics to report export
  - Tool result metrics to report export
  - Internal errors response middleware
# Remove
  - ConversationsMetricsError in favor of simplified error handling
  - Sales funnel parallel processing feature flag

# 1.19.4
# Add
  - Parallel processing for sales funnel data retrieval

# 1.19.3
# Add
  - New template for export
  
# 1.19.2
# Add
  - Adding name filter support to endpoint that list projects (#368)

# 1.19.1
# Fix
  - Total of agents and tools 
  
# 1.19.0
# Add
  - Add tools for result metrics 

# 1.18.2
# Fix
  - Sales funnel event count type conversion to integers

# 1.18.1
# Add
  - Absolute numbers operations support in sales funnel metrics
  - UTM source metrics endpoint for VTEX orders

# 1.18.0
# Add
  - Crosstab widgets in human support exports and report worksheets
  - Validation for crosstab widgets when building reports
  - Spanish and Portuguese locale updates for export-related messages
  - Tests for crosstab worksheet export

# 1.17.7
# Fix
  - Only send operation key when not null in datalake conversations metrics

# 1.17.6
# Fix
  - Rename field_name to operation_key in datalake conversations metrics service

# 1.17.5
# Fix
  - Handle empty field name in conversations metrics service

# 1.17.4
# Add
  - Reference field support for crosstab

# 1.17.3
# Fix
  - Absolute numbers config field name in conversations metrics service

# 1.17.2
# Add
  - VTEX Orders API cache TTL configuration
# Fix
  - VTEX orders cache key generation

# 1.17.1
# Fix
  - Crosstab field name for crosstable

# 1.17.0
# Add
  - Absolute numbers endpoint and metrics service integration
  - Subwidgets support
  - User email to finished rooms endpoint

# 1.16.0
# Add
  - Update projects consumer

# 1.15.0
# Add
  - Increase the number of templates used in abandoned cart analytics
  - Conversations metrics service class
  - Update datalake SDK version to 0.7.0
# Fix
  - Crosstab empty data handling

# 1.14.4
# Add
  - Endpoint to list projects to be used in mcp

# 1.14.3
# Fix
  - Search agents
  
# 1.14.2
# Add
  - Vtex orders pagination
  
# 1.14.1
# Add
  - Conversations metric service

# 1.14.0
# Add
  - Use vtex account on jwt auth
  
# 1.13.0
# Add
  - NPS metrics V2 endpoint
# Remove
  - Cached property from Nexus Conversations API client

# 1.12.2
# Add
  - Enhance response_content handling in ConversationsMetricsService to return lists for both dict and list types

# 1.12.1
# Fix
  - ensure response_content from topics and subtopics returns a list for non-dict types in ConversationsMetricsService

# 1.12.0
# Add
  - Nexus Conversations API client

# 1.11.2
# Add
  - Agent email to detailed monitoring

# 1.11.1
# Fix
  - ensure project_uuid is always a string in InternalVTEXOrdersViewSet
  - authentication classes orders when using JWTAuthentication alongside OIDC

# 1.11.0
# Add
  - Internal project CSAT endpoint
  - Adding internal authentication to conversation totals and VTEX orders

# 1.10.1
# Add
  - restrict delete permission for SurveyAdmin

# 1.10.0
# Add
  - admin SSO functionality with Keycloak login/logout views.
  - settings to include OIDC parameters and session cookie configurations.
  - URL patterns to support OIDC routes for admin.
  - custom admin login template to include Keycloak login option.

# 1.9.0
# Add
  - data volume for queue and tags
  - WhiteNoise middleware for static file serving
  - unit tests for HumanSupportDashboardService to ensure functionality and reliability

# 1.8.3
# Fix
  - Handle empty answers in feedback service and update serializer to allow blank answers

# 1.8.2
# Add
  - Chips and filters

# 1.8.1
# Add
  - is_staff field to User model and create migration

# 1.8.0
# Add
  - User feedback for the conversational dashboard

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
