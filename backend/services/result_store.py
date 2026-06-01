from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from threading import Lock

class ResultStore:
    """Thread-safe singleton result store for agent pipeline results."""
    
    _instance = None
    _lock = Lock()
    MAX_JOBS = 100
    JOB_EXPIRY_HOURS = 1
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._results = {}
                    cls._instance._store_lock = Lock()
        return cls._instance
    
    def _cleanup_old_jobs(self) -> None:
        """Remove expired jobs and enforce max jobs limit."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self.JOB_EXPIRY_HOURS)
        
        # Remove expired jobs
        expired = [
            job_id for job_id, job in self._results.items()
            if datetime.fromisoformat(job["created_at"]) < cutoff
        ]
        for job_id in expired:
            del self._results[job_id]
        
        # If still over limit, remove oldest jobs
        if len(self._results) > self.MAX_JOBS:
            sorted_jobs = sorted(
                self._results.items(),
                key=lambda x: x[1]["created_at"]
            )
            to_remove = sorted_jobs[:20]
            for job_id, _ in to_remove:
                del self._results[job_id]
    
    def create_job(self, job_id: str, query: str) -> None:
        """Create a new job entry."""
        with self._store_lock:
            self._cleanup_old_jobs()
            self._results[job_id] = {
                "job_id": job_id,
                "query": query,
                "status": "pending",
                "agent_status": {},
                "logs": [],
                "output": "",
                "results": [],
                "error": "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def update_status(self, job_id: str, status: str) -> None:
        """Update job status."""
        with self._store_lock:
            if job_id in self._results:
                self._results[job_id]["status"] = status
                self._results[job_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def add_log(self, job_id: str, agent: str, event: str, message: str) -> None:
        """Add a log entry for an agent."""
        normalized_event = event if event in {"start", "info", "handoff", "error", "complete"} else "info"
        with self._store_lock:
            if job_id in self._results:
                if normalized_event == "start":
                    self._results[job_id]["agent_status"][agent] = "active"
                elif normalized_event == "complete":
                    self._results[job_id]["agent_status"][agent] = "complete"
                elif normalized_event == "error":
                    self._results[job_id]["agent_status"][agent] = "error"
                self._results[job_id]["logs"].append({
                    "agent": agent,
                    "event": normalized_event,
                    "message": str(message),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self._results[job_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def set_output(self, job_id: str, output: Any) -> None:
        """Set the final output."""
        with self._store_lock:
            if job_id in self._results:
                self._results[job_id]["output"] = output or ""
                self._results[job_id]["updated_at"] = datetime.utcnow().isoformat()

    def set_results(self, job_id: str, results: List[Dict[str, Any]]) -> None:
        """Set structured results for polling clients."""
        with self._store_lock:
            if job_id in self._results:
                self._results[job_id]["results"] = results or []
                self._results[job_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def set_error(self, job_id: str, error: str) -> None:
        """Set error message."""
        with self._store_lock:
            if job_id in self._results:
                self._results[job_id]["error"] = error or ""
                self._results[job_id]["status"] = "failed"
                self._results[job_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result by job ID."""
        with self._store_lock:
            return self._results.get(job_id)
    
    def get_logs(self, job_id: str) -> List[Dict[str, Any]]:
        """Get logs for a job."""
        with self._store_lock:
            if job_id in self._results:
                return self._results[job_id]["logs"]
            return []

# Global singleton instance
result_store = ResultStore()
