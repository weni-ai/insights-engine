class ConversationsMetricsError(Exception):
    """
    Exception raised when conversations metrics encounters an error.
    """


class GetProjectAiCsatMetricsError(Exception):
    """
    Raised when the GetProjectAiCsatMetricsUseCase fails after handling
    ConversationsMetricsError (logging, Sentry). Carries event_id for the response.
    """

    def __init__(self, message: str, event_id: str):
        super().__init__(message)
        self.event_id = event_id
