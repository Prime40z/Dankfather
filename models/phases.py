"""
Phase management for the Mafia game.
"""
import asyncio
from typing import Dict, Any, Optional

class PhaseManager:
    """Manages game phases and phase transitions."""
    
    def __init__(self):
        """Initialize the phase manager."""
        self.current_phase = None
        self.phase_data = {}
        self.timer = None
        
    async def start_phase(self, phase_name: str, duration: int = 0, data: Dict[str, Any] = None) -> None:
        """
        Start a new phase.
        
        Args:
            phase_name: The name of the phase to start
            duration: Duration of the phase in seconds (0 for no limit)
            data: Additional data for the phase
        """
        self.current_phase = phase_name
        self.phase_data = data if data is not None else {}
        
        # Cancel existing timer if any
        if self.timer:
            self.timer.cancel()
            self.timer = None
            
        # Set up a new timer if duration is specified
        if duration > 0:
            self.timer = asyncio.create_task(self._phase_timer(duration))
            
    async def _phase_timer(self, duration: int) -> None:
        """
        Timer for phase duration.
        
        Args:
            duration: Duration in seconds
        """
        try:
            await asyncio.sleep(duration)
            # Timer completed - phase should end
            self.timer = None
        except asyncio.CancelledError:
            # Timer was cancelled
            self.timer = None
            
    def get_phase_data(self) -> Dict[str, Any]:
        """Get the current phase data."""
        return self.phase_data
        
    def update_phase_data(self, key: str, value: Any) -> None:
        """Update a specific piece of phase data."""
        self.phase_data[key] = value
        
    def end_phase(self) -> Dict[str, Any]:
        """End the current phase and return the phase data."""
        if self.timer:
            self.timer.cancel()
            self.timer = None
            
        phase_data = self.phase_data
        self.phase_data = {}
        self.current_phase = None
        return phase_data