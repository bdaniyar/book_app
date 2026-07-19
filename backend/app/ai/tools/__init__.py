"""Allow-listed assistant tools.

The LLM never receives a database session and cannot execute arbitrary SQL. Only
these application-owned tools may read or propose changes to user data.
"""

