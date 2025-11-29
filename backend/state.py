"""Cooking session state management and timer system."""
import asyncio
import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import sqlite3
import json


@dataclass
class Timer:
    """Represents a cooking timer."""
    id: str
    label: str
    seconds_total: int
    started_at: float
    status: str = "running"  # running, paused, completed

    @property
    def seconds_remaining(self) -> int:
        """Calculate remaining seconds."""
        if self.status != "running":
            return 0
        elapsed = time.time() - self.started_at
        remaining = max(0, self.seconds_total - int(elapsed))
        return remaining

    @property
    def is_done(self) -> bool:
        """Check if timer is complete."""
        return self.seconds_remaining == 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "seconds_total": self.seconds_total,
            "seconds_remaining": self.seconds_remaining,
            "status": self.status,
            "started_at": self.started_at
        }


@dataclass
class CookingSession:
    """Represents an active cooking session."""
    session_id: str
    recipe: Dict
    current_step: int = 1
    timers: Dict[str, Timer] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    notes: List[str] = field(default_factory=list)
    is_paused: bool = False

    @property
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.recipe.get("steps", []))

    @property
    def current_step_data(self) -> Optional[Dict]:
        """Get current step details."""
        steps = self.recipe.get("steps", [])
        if 1 <= self.current_step <= len(steps):
            return steps[self.current_step - 1]
        return None

    def next_step(self) -> bool:
        """Move to next step."""
        if self.current_step < self.total_steps:
            self.current_step += 1
            return True
        return False

    def previous_step(self) -> bool:
        """Move to previous step."""
        if self.current_step > 1:
            self.current_step -= 1
            return True
        return False

    def add_timer(self, label: str, seconds: int) -> Timer:
        """Add a new timer."""
        timer_id = f"timer_{int(time.time() * 1000)}"
        timer = Timer(
            id=timer_id,
            label=label,
            seconds_total=seconds,
            started_at=time.time()
        )
        self.timers[timer_id] = timer
        return timer

    def get_active_timers(self) -> List[Timer]:
        """Get list of running timers."""
        return [t for t in self.timers.values() if t.status == "running" and not t.is_done]

    def check_timers(self) -> List[Timer]:
        """Check for completed timers."""
        completed = []
        for timer in self.timers.values():
            if timer.status == "running" and timer.is_done:
                timer.status = "completed"
                completed.append(timer)
        return completed

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "recipe": self.recipe,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_data": self.current_step_data,
            "timers": [t.to_dict() for t in self.timers.values()],
            "active_timers": [t.to_dict() for t in self.get_active_timers()],
            "created_at": self.created_at,
            "notes": self.notes,
            "is_paused": self.is_paused
        }
        timer = Timer(
            id=timer_id,
            label=label,
            seconds_total=seconds,
            started_at=time.time()
        )
        self.timers[timer_id] = timer
        return timer
    
    def get_active_timers(self) -> List[Timer]:
        """Get list of running timers."""
        return [t for t in self.timers.values() if t.status == "running" and not t.is_done]
    
    def check_timers(self) -> List[Timer]:
        """Check for completed timers."""
        completed = []
        for timer in self.timers.values():
            if timer.status == "running" and timer.is_done:
                timer.status = "completed"
                completed.append(timer)
        return completed
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "recipe": self.recipe,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_data": self.current_step_data,
            "timers": [t.to_dict() for t in self.timers.values()],
            "active_timers": [t.to_dict() for t in self.get_active_timers()],
            "created_at": self.created_at,
            "notes": self.notes,
            "is_paused": self.is_paused
        }


class SessionManager:
    """Manages cooking sessions with SQLite persistence."""
    
    def __init__(self, db_path: str = "runtime/db.sqlite"):
        """Initialize session manager."""
        import os
        # Create runtime directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.sessions: Dict[str, CookingSession] = {}
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                recipe_json TEXT NOT NULL,
                current_step INTEGER NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                is_paused INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timers (
                timer_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                label TEXT NOT NULL,
                seconds_total INTEGER NOT NULL,
                started_at REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                recipe_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, recipe: Dict) -> CookingSession:
        """Create a new cooking session."""
        session_id = f"session_{int(time.time() * 1000)}"
        session = CookingSession(session_id=session_id, recipe=recipe)
        self.sessions[session_id] = session
        self._save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[CookingSession]:
        """Get session by ID."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try loading from database
        session = self._load_session(session_id)
        if session:
            self.sessions[session_id] = session
        return session
    
    def update_session(self, session: CookingSession):
        """Update session in memory and database."""
        self.sessions[session.session_id] = session
        self._save_session(session)
    
    def _save_session(self, session: CookingSession):
        """Save session to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, recipe_json, current_step, created_at, updated_at, is_paused)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session.session_id,
            json.dumps(session.recipe),
            session.current_step,
            session.created_at,
            time.time(),
            1 if session.is_paused else 0
        ))
        
        # Save timers
        cursor.execute("DELETE FROM timers WHERE session_id = ?", (session.session_id,))
        for timer in session.timers.values():
            cursor.execute("""
                INSERT INTO timers (timer_id, session_id, label, seconds_total, started_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timer.id,
                session.session_id,
                timer.label,
                timer.seconds_total,
                timer.started_at,
                timer.status
            ))
        
        conn.commit()
        conn.close()
    
    def _load_session(self, session_id: str) -> Optional[CookingSession]:
        """Load session from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session = CookingSession(
            session_id=row[0],
            recipe=json.loads(row[1]),
            current_step=row[2],
            created_at=row[3],
            is_paused=bool(row[5]) if len(row) > 5 else False
        )
        
        # Load timers
        cursor.execute("SELECT * FROM timers WHERE session_id = ?", (session_id,))
        for timer_row in cursor.fetchall():
            timer = Timer(
                id=timer_row[0],
                label=timer_row[2],
                seconds_total=timer_row[3],
                started_at=timer_row[4],
                status=timer_row[5]
            )
            session.timers[timer.id] = timer
        
        conn.close()
        return session
    
    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT session_id FROM sessions ORDER BY created_at DESC")
        session_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return session_ids
    
    def save_recipe(self, title: str, description: str, recipe: Dict) -> int:
        """Save a recipe to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recipes (title, description, recipe_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            description,
            json.dumps(recipe),
            time.time(),
            time.time()
        ))
        
        recipe_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return recipe_id
    
    def get_recipe(self, recipe_id: int) -> Optional[Dict]:
        """Get a recipe by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        recipe = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "recipe": json.loads(row[3]),
            "created_at": row[4],
            "updated_at": row[5]
        }
        
        conn.close()
        return recipe
    
    def list_recipes(self) -> List[Dict]:
        """List all recipes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM recipes ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        recipes = []
        for row in rows:
            recipe = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "recipe": json.loads(row[3]),
                "created_at": row[4],
                "updated_at": row[5]
            }
            recipes.append(recipe)
        
        conn.close()
        return recipes


def parse_time_string(time_str: str) -> Optional[int]:
    """
    Parse natural language time string to seconds.
    
    Examples:
        "5 minutes" -> 300
        "1 hour" -> 3600
        "30 seconds" -> 30
        "2m" -> 120
    """
    time_str = time_str.lower().strip()
    
    # Pattern: number + unit
    patterns = [
        (r'(\d+\.?\d*)\s*h(?:ours?)?', 3600),
        (r'(\d+\.?\d*)\s*m(?:in(?:ute)?s?)?', 60),
        (r'(\d+\.?\d*)\s*s(?:ec(?:ond)?s?)?', 1),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, time_str)
        if match:
            value = float(match.group(1))
            return int(value * multiplier)
    
    return None


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager