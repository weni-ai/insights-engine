from django.db import models
from django.utils.translation import gettext_lazy as _


class WhatsAppMessageTemplatesCategories(models.TextChoices):
    ACCOUNT_UPDATE = "ACCOUNT_UPDATE", _("Account Update")
    ALERT_UPDATE = "ALERT_UPDATE", _("Alert Update")
    APPOINTMENT_UPDATE = "APPOINTMENT_UPDATE", _("Appointment Update")
    AUTHENTICATION = "AUTHENTICATION", _("Authentication")
    AUTO_REPLY = "AUTO_REPLY", _("Auto Reply")
    ISSUE_RESOLUTION = "ISSUE_RESOLUTION", _("Issue Resolution")
    MARKETING = "MARKETING", _("Marketing")
    OTP = "OTP", _("OTP")
    PAYMENT_UPDATE = "PAYMENT_UPDATE", _("Payment Update")
    PERSONAL_FINANCE_UPDATE = "PERSONAL_FINANCE_UPDATE", _("Personal Finance Update")
    RESERVATION_UPDATE = "RESERVATION_UPDATE", _("Reservation Update")
    SHIPPING_UPDATE = "SHIPPING_UPDATE", _("Shipping Update")
    TICKET_UPDATE = "TICKET_UPDATE", _("Ticket Update")
    TRANSACTIONAL = "TRANSACTIONAL", _("Transactional")
    TRANSPORTATION_UPDATE = "TRANSPORTATION_UPDATE", _("Transportation Update")
    UTILITY = "UTILITY", _("Utility")
