class ResumeProcessingError(Exception):
    """Raised when resume parsing or analysis fails."""


class ValidationError(Exception):
    """Raised when the user submits invalid or unsupported content."""
