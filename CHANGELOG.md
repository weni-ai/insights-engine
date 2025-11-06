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
