import logging
import functools
import traceback
from typing import Callable, Any, Optional, Type, List, Dict
from enum import Enum, auto
from ap_utils.colors import fg

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EH')


class ErrorSeverity(Enum):
    """Enum for error severity levels"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorHandler:
    """Robust error handling class with multiple strategies"""

    def __init__(self, name: str = "ErrorHandler"):
        self.name = name
        self.error_count = 0
        self.error_history: List[Dict[str, Any]] = []
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
        self.max_errors = 100
        self._is_recoverable = True

    def log_error(self, error: Exception, severity: ErrorSeverity = ErrorSeverity.ERROR,
                  context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context"""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'severity': severity.name,
            'context': context or {},
            'timestamp': self._get_current_timestamp()
        }

        self.error_history.append(error_info)
        self.error_count += 1

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"{fg.BWHITE}{self.name}{fg.RESET}: {fg.RED}{error_info['message']}{fg.RESET}")
        elif severity == ErrorSeverity.ERROR:
            logger.error(f"{fg.BWHITE}{self.name}{fg.RESET}: {fg.RED}{error_info['message']}{fg.RESET}")
        elif severity == ErrorSeverity.WARNING:
            logger.warning(f"{fg.BWHITE}{self.name}{fg.RESET}: {fg.YELLOW}{error_info['message']}{fg.RESET}")
        else:
            logger.info(f"{fg.BWHITE}{self.name}{fg.RESET}: {fg.BLUE}{error_info['message']}{fg.RESET}")

        if self.error_count > self.max_errors:
            logger.critical(f"{self.name}: Maximum error count ({self.max_errors}) reached. Stopping.")
            self._is_recoverable = False

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _should_retry(self, attempt: int) -> bool:
        """Determine if a retry should be attempted"""
        return attempt < self.retry_attempts and self._is_recoverable

    def _retry_delay(self, attempt: int) -> float:
        """Calculate delay before retry"""
        return self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff

    def handle_error(self, error: Exception, func: Callable, *args, **kwargs) -> Any:
        """Handle an error and optionally retry the function"""
        attempt = 0

        while self._should_retry(attempt):
            attempt += 1
            if attempt > 1:
                logger.warning(f"Retrying {func.__name__} (attempt {attempt})")

            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.log_error(e, context={
                    'function': func.__name__,
                    'attempt': attempt,
                    'args': args,
                    'kwargs': kwargs
                })

                if not self._should_retry(attempt + 1):
                    raise  # Re-raise the last exception if no more retries

                import time
                time.sleep(self._retry_delay(attempt))

        raise Exception(f"All retry attempts failed for {func.__name__}")

    def decorator(self, func: Callable) -> Callable:
        """Decorator for error handling with retry logic"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.handle_error(func, *args, **kwargs)
        return wrapper

    def decorator_with_args(self, *decorator_args, **decorator_kwargs) -> Callable:
        """Decorator factory that accepts arguments"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Merge decorator args with function args
                merged_kwargs = {**decorator_kwargs, **kwargs}
                return self.handle_error(func, *args, **merged_kwargs)
            return wrapper
        return decorator

    def context(self, func: Callable, *args, **kwargs) -> Any:
        """Context manager for error handling"""
        log_error = self.log_error

        class ErrorHandlerContext:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    log_error(exc_val, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    return True  # Suppress the exception
        return ErrorHandlerContext()

    def context_factory(self, *context_args, **context_kwargs) -> Callable:
        """Context manager factory that accepts arguments"""
        def context_manager(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.context(func, *args, **kwargs) as ctx:
                    return func(*args, **kwargs)
            return wrapper
        return context_manager

    def exception(self, exception_type: Type[Exception]) -> Callable:
        """Decorator that handles specific exception types"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exception_type as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def exception_factory(self, *exception_types: Type[Exception]) -> Callable:
        """Decorator factory that handles multiple exception types"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except tuple(exception_types) as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_fallback(self, fallback_func: Callable) -> Callable:
        """Decorator that provides a fallback function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    return fallback_func(*args, **kwargs)
            return wrapper
        return decorator

    def with_fallback_factory(self, fallback_func: Callable) -> Callable:
        """Decorator factory that provides a fallback function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    return fallback_func(*args, **kwargs)
            return wrapper
        return decorator

    def with_recovery(self, recovery_func: Callable) -> Callable:
        """Decorator that provides a recovery function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    recovery_func(*args, **kwargs)
                    return wrapper(*args, **kwargs)  # Retry the function
            return wrapper
        return decorator

    def with_recovery_factory(self, recovery_func: Callable) -> Callable:
        """Decorator factory that provides a recovery function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    recovery_func(*args, **kwargs)
                    return wrapper(*args, **kwargs)  # Retry the function
            return wrapper
        return decorator

    def with_cleanup(self, cleanup_func: Callable) -> Callable:
        """Decorator that provides a cleanup function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    cleanup_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_cleanup_factory(self, cleanup_func: Callable) -> Callable:
        """Decorator factory that provides a cleanup function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    cleanup_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_rollback(self, rollback_func: Callable) -> Callable:
        """Decorator that provides a rollback function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    rollback_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_rollback_factory(self, rollback_func: Callable) -> Callable:
        """Decorator factory that provides a rollback function if the main function fails"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    rollback_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_transaction(self, commit_func: Callable, rollback_func: Callable) -> Callable:
        """Decorator that provides transactional behavior"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    commit_func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    rollback_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def with_transaction_factory(self, commit_func: Callable, rollback_func: Callable) -> Callable:
        """Decorator factory that provides transactional behavior"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    commit_func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.log_error(e, context={
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs
                    })
                    rollback_func(*args, **kwargs)
                    raise  # Re-raise the exception
            return wrapper
        return decorator

    def get_error_report(self) -> str:
        """Generate a report of all errors"""
        report = f"Error Report for {self.name}\n"
        report += f"Total Errors: {self.error_count}\n\n"

        for i, error in enumerate(self.error_history, 1):
            report += f"Error {i}:\n"
            report += f"  Type: {error['type']}\n"
            report += f"  Message: {error['message']}\n"
            report += f"  Severity: {error['severity']}\n"
            report += f"  Timestamp: {error['timestamp']}\n"
            report += f"  Context: {error['context']}\n\n"

        return report

    def clear_errors(self) -> None:
        """Clear all recorded errors"""
        self.error_count = 0
        self.error_history = []

# Example usage:


# Create an error handler instance
error_handler = ErrorHandler("SystemSetup")

# Example functions to be protected


def setup_network():
    # Simulate a network setup operation
    import random
    if random.random() < 0.7:  # 70% chance of success
        print("Network setup successful")
        return True
    else:
        raise Exception("Network setup failed")


def setup_firewall():
    # Simulate a firewall setup operation
    import random
    if random.random() < 0.6:  # 60% chance of success
        print("Firewall setup successful")
        return True
    else:
        raise Exception("Firewall setup failed")


def cleanup_network():
    print("Cleaning up network resources")


def rollback_network():
    print("Rolling back network changes")

# Using the decorators


@error_handler.decorator
def setup_system():
    """Main system setup function"""
    if not setup_network():
        raise Exception("Network setup failed")
    if not setup_firewall():
        raise Exception("Firewall setup failed")
    print("System setup complete")
    return True

# Using the context manager


def setup_system_with_context():
    """Main system setup function with context manager"""
    with error_handler.context(setup_network):
        setup_network()

    with error_handler.context(setup_firewall):
        setup_firewall()

    print("System setup complete")
    return True

# Using the fallback decorator


@error_handler.with_fallback(lambda: print("Using fallback network setup"))
def setup_system_with_fallback():
    """Main system setup function with fallback"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True

# Using the recovery decorator


@error_handler.with_recovery(cleanup_network)
def setup_system_with_recovery():
    """Main system setup function with recovery"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True

# Using the rollback decorator


@error_handler.with_rollback(rollback_network)
def setup_system_with_rollback():
    """Main system setup function with rollback"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True

# Using the transaction decorator


@error_handler.with_transaction(
    commit_func=lambda: print("Committing changes"),
    rollback_func=rollback_network
)
def setup_system_with_transaction():
    """Main system setup function with transaction"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True

# Example of using the error handler directly


def setup_system_with_direct_handler():
    """Main system setup function with direct error handler"""
    try:
        setup_network()
        setup_firewall()
        print("System setup complete")
        return True
    except Exception as e:
        error_handler.log_error(e, context={
            'function': 'setup_system_with_direct_handler',
            'step': 'network and firewall setup'
        })
        return False

# Example of using the exception-specific decorator


@error_handler.exception(ConnectionError)
def setup_system_with_exception_handler():
    """Main system setup function with exception-specific handler"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True

# Example of using the multiple exception types decorator


@error_handler.exception_factory(ConnectionError, TimeoutError)
def setup_system_with_multiple_exception_handler():
    """Main system setup function with multiple exception types handler"""
    setup_network()
    setup_firewall()
    print("System setup complete")
    return True
