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
