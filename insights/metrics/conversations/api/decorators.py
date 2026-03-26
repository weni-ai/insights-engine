def force_use_real_service(func):
    """
    Decorator to prevent the use of the mock service
    """
    func.force_use_real_service = True

    return func
