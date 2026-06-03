class CommerceIntegrationError(Exception):
    """Base exception for errors when integrating with external commerce services."""


class RetailSetupRequestError(CommerceIntegrationError):
    """Raised when the request to the retail setup service fails."""


class BillingRequestError(CommerceIntegrationError):
    """Raised when the request to the billing service fails."""
