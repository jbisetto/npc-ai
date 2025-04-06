"""
SQLite Storage

This module provides a SQLite implementation of the conversation storage.
"""

import os
import json
import logging
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.ai.npc.core.storage.base import ConversationStorage

logger = logging.getLogger(__name__)


class SQLiteConversationStorage(ConversationStorage):
    """
    SQLite implementation of the conversation storage.
    
    This class stores conversation contexts in a SQLite database, which persists
    them across application restarts.
    """
    
    def __init__(self, database_path: str = None):
        """
        Initialize the SQLite storage.
        
        Args:
            database_path: Path to the SQLite database file. If None, uses a default path.
        """
        self.database_path = database_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', '..', '..',
            'data', 'conversations.db'
        )
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        logger.debug(f"Initialized SQLiteConversationStorage with database at {self.database_path}")
    
    async def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        async with aiosqlite.connect(self.database_path) as db:
            # Create the conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Create the entries table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                        ON DELETE CASCADE
                )
            """)
            
            # Create indices for faster queries
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversations (timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_entries_conversation_id ON entries (conversation_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_entries_timestamp ON entries (timestamp)")
            
            await db.commit()
    
    async def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation context, or None if not found
        """
        await self._init_db()
        
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get the conversation
            async with db.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                # Parse the conversation metadata
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except json.JSONDecodeError:
                    metadata = {}
                
                # Initialize the context with empty entries
                context = {
                    "conversation_id": row['conversation_id'],
                    "timestamp": row['timestamp'],
                    "entries": [],
                    **metadata
                }
                
                # Get the conversation entries
                async with db.execute(
                    """
                    SELECT * FROM entries 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp ASC
                    """,
                    (conversation_id,)
                ) as entries_cursor:
                    entries = await entries_cursor.fetchall()
                    
                    for entry in entries:
                        try:
                            metadata = json.loads(entry['metadata']) if entry['metadata'] else {}
                        except json.JSONDecodeError:
                            metadata = {}
                        
                        # Create the entry dictionary with common fields
                        entry_dict = {
                            "timestamp": entry['timestamp'],
                            "type": entry['type'],
                            **metadata
                        }
                        
                        # Handle different entry types
                        if entry['type'] == 'user_message' or entry['type'] == 'assistant_message':
                            entry_dict['text'] = entry['content']
                        else:
                            # For other types, store the content as is
                            entry_dict['content'] = entry['content']
                        
                        # Add the entry to the context
                        context['entries'].append(entry_dict)
                
                return context
    
    async def save_context(self, conversation_id: str, context: Dict[str, Any]) -> None:
        """
        Save a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
            context: The conversation context to save
        """
        await self._init_db()
        
        # Ensure the context has a timestamp
        if 'timestamp' not in context:
            context['timestamp'] = datetime.now().isoformat()
        
        # Make a copy of the context to avoid modifying the original
        context_copy = context.copy()
        
        # Extract entries for separate storage
        entries = context_copy.pop('entries', [])
        
        # Separate metadata from core fields
        metadata = {k: v for k, v in context_copy.items() if k not in ('conversation_id', 'timestamp')}
        
        logger.debug(f"Saving context for {conversation_id} with {len(entries)} entries")
        
        # Start transaction
        async with aiosqlite.connect(self.database_path) as db:
            try:
                # Start an explicit transaction
                await db.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Insert or update the conversation
                await db.execute(
                    """
                    INSERT OR REPLACE INTO conversations (conversation_id, timestamp, metadata)
                    VALUES (?, ?, ?)
                    """,
                    (
                        conversation_id,
                        context_copy.get('timestamp'),
                        json.dumps(metadata) if metadata else None
                    )
                )
                
                # Only insert new entries, don't delete existing ones
                for entry in entries:
                    entry_type = entry.get('type', 'unknown')
                    timestamp = entry.get('timestamp', datetime.now().isoformat())
                    
                    # Handle different entry types
                    if entry_type in ('user_message', 'assistant_message'):
                        content = entry.get('text', '')
                    else:
                        content = entry.get('content', '')
                    
                    # Separate metadata from core fields
                    metadata = {k: v for k, v in entry.items() 
                               if k not in ('type', 'timestamp', 'text', 'content')}
                    
                    # Check if this entry already exists to avoid duplicates
                    async with db.execute(
                        """
                        SELECT id FROM entries 
                        WHERE conversation_id = ? AND timestamp = ? AND type = ? AND content = ?
                        """,
                        (conversation_id, timestamp, entry_type, content)
                    ) as cursor:
                        existing = await cursor.fetchone()
                    
                    # Only insert if the entry doesn't exist
                    if not existing:
                        logger.debug(f"Adding new entry for {conversation_id} of type {entry_type}")
                        await db.execute(
                            """
                            INSERT INTO entries (conversation_id, timestamp, type, content, metadata)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                conversation_id,
                                timestamp,
                                entry_type,
                                content,
                                json.dumps(metadata) if metadata else None
                            )
                        )
                
                # Commit the transaction to save all changes
                await db.commit()
                logger.debug(f"Successfully saved context for {conversation_id}")
                
            except Exception as e:
                # If any error occurs, roll back the transaction
                await db.execute("ROLLBACK")
                logger.error(f"Error saving context for {conversation_id}: {e}")
                raise
        
        # Verify the entries were saved correctly by retrieving them
        saved_context = await self.get_context(conversation_id)
        if saved_context:
            saved_entries_count = len(saved_context.get('entries', []))
            logger.debug(f"Verified saved context for {conversation_id} has {saved_entries_count} entries")
        else:
            logger.warning(f"Failed to verify saved context for {conversation_id}")
    
    async def delete_context(self, conversation_id: str) -> None:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The ID of the conversation
        """
        await self._init_db()
        
        async with aiosqlite.connect(self.database_path) as db:
            # Delete the conversation (cascades to entries)
            await db.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            await db.commit()
    
    async def list_contexts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List conversation contexts.
        
        Args:
            limit: The maximum number of contexts to return
            offset: The number of contexts to skip
            
        Returns:
            A list of conversation contexts
        """
        await self._init_db()
        
        contexts = []
        
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get conversations
            async with db.execute(
                """
                SELECT * FROM conversations
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    conversation_id = row['conversation_id']
                    context = await self.get_context(conversation_id)
                    if context:
                        contexts.append(context)
        
        return contexts
    
    async def cleanup_old_contexts(self, max_age_days: int = 30) -> int:
        """
        Delete conversation contexts older than the specified age.
        
        Args:
            max_age_days: The maximum age of contexts to keep, in days
            
        Returns:
            The number of contexts deleted
        """
        await self._init_db()
        
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        
        async with aiosqlite.connect(self.database_path) as db:
            # Get the count of conversations to be deleted
            async with db.execute(
                "SELECT COUNT(*) FROM conversations WHERE timestamp < ?",
                (cutoff_date,)
            ) as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0
            
            # Delete the conversations (cascades to entries)
            await db.execute(
                "DELETE FROM conversations WHERE timestamp < ?",
                (cutoff_date,)
            )
            
            await db.commit()
        
        return count
    
    async def clear_entries(self, conversation_id: str) -> None:
        """
        Clear all entries for a specific conversation ID.
        
        Args:
            conversation_id: The ID of the conversation to clear entries for
        """
        await self._init_db()
        
        logger.debug(f"Clearing entries for conversation {conversation_id}")
        
        async with aiosqlite.connect(self.database_path) as db:
            try:
                # Start an explicit transaction
                await db.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Delete all entries for this conversation
                await db.execute(
                    "DELETE FROM entries WHERE conversation_id = ?",
                    (conversation_id,)
                )
                
                # Commit the transaction
                await db.commit()
                logger.debug(f"Successfully cleared entries for {conversation_id}")
                
            except Exception as e:
                # If any error occurs, roll back the transaction
                await db.execute("ROLLBACK")
                logger.error(f"Error clearing entries for {conversation_id}: {e}")
                raise 