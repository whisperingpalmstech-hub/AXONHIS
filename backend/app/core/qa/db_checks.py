"""Database check logic for QA module."""
import time
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.qa.schemas import DBCheckResponse
from app.database import get_db


async def check_database_connection(db: AsyncSession) -> DBCheckResponse:
    """
    Check if database connection is healthy.
    
    Args:
        db: Database session
    
    Returns:
        DBCheckResponse with connection status
    """
    start_time = time.time()
    
    try:
        result = await db.execute(text("SELECT 1"))
        connection_healthy = result.fetchone() is not None
        query_time_ms = (time.time() - start_time) * 1000
        
        return DBCheckResponse(
            status="healthy" if connection_healthy else "unhealthy",
            connection_healthy=connection_healthy,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=None if connection_healthy else "Database connection failed"
        )
    
    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        return DBCheckResponse(
            status="error",
            connection_healthy=False,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=str(e)
        )


async def check_table_access(
    table_name: str,
    db: AsyncSession,
    max_time_ms: Optional[int] = None
) -> DBCheckResponse:
    """
    Check if a table is accessible and queryable.
    
    Args:
        table_name: Name of the table to check
        db: Database session
        max_time_ms: Optional maximum query time threshold
    
    Returns:
        DBCheckResponse with table access status
    """
    start_time = time.time()
    
    try:
        # Check if table exists and is accessible
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = await db.execute(query)
        count = result.fetchone()
        
        table_accessible = count is not None
        query_time_ms = (time.time() - start_time) * 1000
        
        within_threshold = True
        if max_time_ms and query_time_ms > max_time_ms:
            within_threshold = False
        
        return DBCheckResponse(
            status="accessible" if table_accessible and within_threshold else "unaccessible",
            connection_healthy=True,
            table_accessible=table_accessible,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=None if (table_accessible and within_threshold) else f"Table access failed or query too slow ({query_time_ms:.2f}ms)"
        )
    
    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        return DBCheckResponse(
            status="error",
            connection_healthy=False,
            table_accessible=False,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=str(e)
        )


async def check_query_performance(
    query: str,
    db: AsyncSession,
    max_time_ms: Optional[int] = None
) -> DBCheckResponse:
    """
    Check if a query performs within acceptable time limits.
    
    Args:
        query: SQL query to execute
        db: Database session
        max_time_ms: Optional maximum query time threshold
    
    Returns:
        DBCheckResponse with query performance status
    """
    start_time = time.time()
    
    try:
        result = await db.execute(text(query))
        result.fetchall()
        
        query_time_ms = (time.time() - start_time) * 1000
        within_threshold = True
        
        if max_time_ms and query_time_ms > max_time_ms:
            within_threshold = False
        
        return DBCheckResponse(
            status="within_threshold" if within_threshold else "slow",
            connection_healthy=True,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=None if within_threshold else f"Query time {query_time_ms:.2f}ms exceeds threshold {max_time_ms}ms"
        )
    
    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        return DBCheckResponse(
            status="error",
            connection_healthy=False,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=str(e)
        )


async def check_data_integrity(
    table_name: str,
    rules: Dict[str, Any],
    db: AsyncSession
) -> DBCheckResponse:
    """
    Check data integrity based on provided rules.
    
    Args:
        table_name: Name of the table to check
        rules: Dictionary of integrity rules
        db: Database session
    
    Returns:
        DBCheckResponse with data integrity status
    """
    start_time = time.time()
    
    try:
        integrity_healthy = True
        error_messages = []
        
        # Check for null values in required columns
        if "required_columns" in rules:
            for column in rules["required_columns"]:
                query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {column} IS NULL")
                result = await db.execute(query)
                null_count = result.fetchone()[0]
                
                if null_count > 0:
                    integrity_healthy = False
                    error_messages.append(f"Column '{column}' has {null_count} null values")
        
        # Check for duplicate values in unique columns
        if "unique_columns" in rules:
            for column in rules["unique_columns"]:
                query = text(f"""
                    SELECT {column}, COUNT(*) as count 
                    FROM {table_name} 
                    GROUP BY {column} 
                    HAVING COUNT(*) > 1
                """)
                result = await db.execute(query)
                duplicates = result.fetchall()
                
                if duplicates:
                    integrity_healthy = False
                    error_messages.append(f"Column '{column}' has {len(duplicates)} duplicate values")
        
        # Check for foreign key constraints
        if "foreign_keys" in rules:
            for fk in rules["foreign_keys"]:
                table = fk["table"]
                column = fk["column"]
                ref_table = fk["ref_table"]
                ref_column = fk["ref_column"]
                
                query = text(f"""
                    SELECT COUNT(*) FROM {table} t
                    LEFT JOIN {ref_table} r ON t.{column} = r.{ref_column}
                    WHERE t.{column} IS NOT NULL AND r.{ref_column} IS NULL
                """)
                result = await db.execute(query)
                orphan_count = result.fetchone()[0]
                
                if orphan_count > 0:
                    integrity_healthy = False
                    error_messages.append(f"Foreign key violation: {orphan_count} orphaned records in {table}.{column}")
        
        query_time_ms = (time.time() - start_time) * 1000
        
        return DBCheckResponse(
            status="integrity_ok" if integrity_healthy else "integrity_failed",
            connection_healthy=True,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=integrity_healthy,
            error_message=None if integrity_healthy else "; ".join(error_messages)
        )
    
    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        return DBCheckResponse(
            status="error",
            connection_healthy=False,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=str(e)
        )


async def check_index_usage(
    table_name: str,
    db: AsyncSession
) -> DBCheckResponse:
    """
    Check if indexes are being used effectively.
    
    Args:
        table_name: Name of the table to check
        db: Database session
    
    Returns:
        DBCheckResponse with index usage status
    """
    start_time = time.time()
    
    try:
        # Check for missing indexes on foreign keys
        query = text(f"""
            SELECT 
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = '{table_name}'
        """)
        result = await db.execute(query)
        foreign_keys = result.fetchall()
        
        missing_indexes = []
        for fk in foreign_keys:
            table, column = fk[0], fk[1]
            # Check if index exists
            index_query = text(f"""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = '{table}' 
                AND indexdef LIKE '%{column}%'
            """)
            index_result = await db.execute(index_query)
            if not index_result.fetchone():
                missing_indexes.append(f"{table}.{column}")
        
        query_time_ms = (time.time() - start_time) * 1000
        index_healthy = len(missing_indexes) == 0
        
        return DBCheckResponse(
            status="index_ok" if index_healthy else "missing_indexes",
            connection_healthy=True,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=index_healthy,
            error_message=None if index_healthy else f"Missing indexes on: {', '.join(missing_indexes)}"
        )
    
    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        return DBCheckResponse(
            status="error",
            connection_healthy=False,
            table_accessible=None,
            query_time_ms=round(query_time_ms, 2),
            data_integrity_healthy=None,
            error_message=str(e)
        )
