def flag_as_internal_jwt_enabled(func):
    func._flag_as_internal_jwt_enabled = True
    return func
