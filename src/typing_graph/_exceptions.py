class TypingGraphError(Exception):
    """Base exception for all typing-graph errors.

    This is the root of the typing-graph exception hierarchy. All
    library-specific exceptions inherit from this class.
    """


class TraversalError(TypingGraphError):
    """Error during graph traversal.

    Raised when traversal encounters an unrecoverable error condition:
    - max_depth is negative (invalid parameter)
    - Implementation errors detected during traversal
    """
