import os
import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer(checkpointer_instance=None):
    """
    Returns a persistent PostgreSQL checkpointer for production execution,
    or falls back cleanly to MemorySaver for unit tests and local isolation.
    """
    if checkpointer_instance is not None:
        return checkpointer_instance

    # When testing or forced by env
    use_memory = os.getenv("LANGGRAPH_USE_MEMORY_CHECKPOINTER", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if use_memory:
        return MemorySaver()

    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        db_name = os.getenv("POSTGRES_DB", "hireflow")
        db_user = os.getenv("POSTGRES_USER", "hireflow")
        db_password = os.getenv("POSTGRES_PASSWORD", "local-db-password-change-me")
        db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        db_port = os.getenv("POSTGRES_PORT", "5432")

        conn_str = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        return PostgresSaver.from_conn_string(conn_str)
    except Exception as e:
        logger.warning(
            "Could not connect to PostgreSQL checkpointer (%s); falling back to in-memory MemorySaver.",
            e,
        )
        return MemorySaver()
