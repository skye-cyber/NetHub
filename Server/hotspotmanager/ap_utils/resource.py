def increase_resource_limits():
    """Increase system resource limits to prevent 'Too many open files' errors"""
    try:
        import resource
        # Increase file descriptor limit
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft_limit < 4096:
            new_limit = min(hard_limit, 4096) if hard_limit > 0 else 4096
            resource.setrlimit(resource.RLIMIT_NOFILE, (new_limit, hard_limit))
            # print(f"Increased file descriptor limit to {new_limit}")

        # Increase process limit
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NPROC)
        if soft_limit < 1024:
            new_limit = min(hard_limit, 1024) if hard_limit > 0 else 1024
            resource.setrlimit(resource.RLIMIT_NPROC, (new_limit, hard_limit))

    except (ImportError, ValueError, resource.error) as e:
        print(f"Warning: Could not increase resource limits: {str(e)}")
