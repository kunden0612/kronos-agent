"""定时任务调度系统 - 支持 cron 表达式解析和自动化任务"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CRON_DIR = str(Path.home() / ".kronos" / "cron")


class CronJob:
    """定时任务"""

    def __init__(self, job_id: str, name: str, command: str, cron_expr: str,
                 enabled: bool = True, description: str = "", tags: List[str] = None,
                 pre_script: str = None, working_dir: str = None, env_vars: Dict[str, str] = None,
                 timeout: int = 3600, max_retries: int = 3):
        self.job_id = job_id
        self.name = name
        self.description = description
        self.command = command
        self.cron_expr = cron_expr
        self.enabled = enabled
        self.tags = tags or []
        self.pre_script = pre_script
        self.working_dir = working_dir
        self.env_vars = env_vars or {}
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.last_run: Optional[datetime] = None
        self.last_status: Optional[str] = None
        self.last_output: Optional[str] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id, "name": self.name, "description": self.description,
            "command": self.command, "cron_expr": self.cron_expr, "enabled": self.enabled,
            "tags": self.tags, "pre_script": self.pre_script, "working_dir": self.working_dir,
            "env_vars": self.env_vars, "timeout": self.timeout, "max_retries": self.max_retries,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_status": self.last_status, "last_output": self.last_output,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count, "created_at": self.created_at, "updated_at": self.updated_at
        }


class CronParser:
    """Cron 表达式解析器"""

    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        values = set()
        
        if field == "*":
            return list(range(min_val, max_val + 1))
        
        for part in field.split(","):
            if "/" in part:
                range_part, step = part.split("/")
                step = int(step)
                
                if range_part == "*":
                    start, end = min_val, max_val
                elif "-" in range_part:
                    start, end = map(int, range_part.split("-"))
                else:
                    start = end = int(range_part)
                
                values.update(range(start, end + 1, step))
            elif "-" in part:
                start, end = map(int, part.split("-"))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))
        
        return sorted([v for v in values if min_val <= v <= max_val])

    @staticmethod
    def parse(cron_expr: str) -> Dict[str, List[int]]:
        parts = cron_expr.split()
        
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        return {
            "minute": CronParser.parse_field(parts[0], 0, 59),
            "hour": CronParser.parse_field(parts[1], 0, 23),
            "day_of_month": CronParser.parse_field(parts[2], 1, 31),
            "month": CronParser.parse_field(parts[3], 1, 12),
            "day_of_week": CronParser.parse_field(parts[4], 0, 6)
        }

    @staticmethod
    def get_next_run(cron_expr: str, base_time: datetime = None) -> datetime:
        parsed = CronParser.parse(cron_expr)
        current = base_time or datetime.now()
        
        for delta_seconds in range(1, 7 * 24 * 3600):
            check_time = current + timedelta(seconds=delta_seconds)
            
            if check_time.minute not in parsed["minute"]:
                continue
            if check_time.hour not in parsed["hour"]:
                continue
            if check_time.day not in parsed["day_of_month"]:
                continue
            if check_time.month not in parsed["month"]:
                continue
            if check_time.weekday() not in parsed["day_of_week"]:
                continue
            
            return check_time.replace(second=0, microsecond=0)
        
        raise ValueError(f"Cannot determine next run time for: {cron_expr}")


class CronScheduler:
    """定时任务调度器"""

    def __init__(self, cron_dir: str = None):
        self._cron_dir = cron_dir or DEFAULT_CRON_DIR
        self._jobs: Dict[str, CronJob] = {}
        self._running = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        
        Path(self._cron_dir).mkdir(parents=True, exist_ok=True)
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="cron-scheduler")
        self._thread.start()
        logger.info("Cron scheduler started")
    
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cron scheduler stopped")
    
    def _run_loop(self) -> None:
        while self._running:
            try:
                now = datetime.now()
                
                with self._lock:
                    for job in self._jobs.values():
                        if not job.enabled:
                            continue
                        
                        job.next_run = CronParser.get_next_run(job.cron_expr)
                        
                        if job.last_run is None:
                            if self._should_run_now(job, now):
                                self._execute_job(job)
                        elif self._should_run_now(job, now):
                            if now - job.last_run > timedelta(seconds=60):
                                self._execute_job(job)
            
            except Exception as e:
                logger.error(f"Cron scheduler error: {e}")
            
            time.sleep(30)
    
    def _should_run_now(self, job: CronJob, now: datetime) -> bool:
        if job.next_run is None:
            job.next_run = CronParser.get_next_run(job.cron_expr)
        
        return now >= job.next_run
    
    def _execute_job(self, job: CronJob) -> None:
        logger.info(f"Executing cron job: {job.name} ({job.job_id})")
        
        job.last_run = datetime.now()
        job.run_count += 1
        
        try:
            result = self._run_command(job)
            job.last_status = "success" if result["returncode"] == 0 else "failed"
            job.last_output = result.get("stdout", "")[:5000]
            
            if job.job_id in self._callbacks:
                try:
                    self._callbacks[job.job_id](job, result)
                except Exception as e:
                    logger.warning(f"Job callback error: {e}")
        
        except Exception as e:
            job.last_status = "error"
            job.last_output = str(e)
            logger.error(f"Cron job execution error: {e}")
        
        job.updated_at = datetime.now().isoformat()
        self._save_jobs()
    
    def _run_command(self, job: CronJob) -> Dict[str, Any]:
        env = os.environ.copy()
        env.update(job.env_vars)
        
        working_dir = job.working_dir or os.getcwd()
        
        if job.pre_script:
            try:
                subprocess.run(job.pre_script, shell=True, cwd=working_dir, env=env, capture_output=True, timeout=job.timeout)
            except Exception as e:
                logger.warning(f"Pre-script error: {e}")
        
        result = subprocess.run(job.command, shell=True, cwd=working_dir, env=env, capture_output=True, text=True, timeout=job.timeout)
        
        return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    
    def _save_jobs(self) -> None:
        jobs_file = Path(self._cron_dir) / "jobs.json"
        
        try:
            with open(jobs_file, "w", encoding="utf-8") as f:
                json.dump({job_id: job.to_dict() for job_id, job in self._jobs.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def _load_jobs(self) -> None:
        jobs_file = Path(self._cron_dir) / "jobs.json"
        
        if not jobs_file.exists():
            return
        
        try:
            with open(jobs_file, "r", encoding="utf-8") as f:
                jobs_data = json.load(f)
            
            for job_id, job_dict in jobs_data.items():
                job = CronJob(
                    job_id=job_dict["job_id"], name=job_dict["name"], command=job_dict["command"],
                    cron_expr=job_dict["cron_expr"], enabled=job_dict.get("enabled", True),
                    description=job_dict.get("description", ""), tags=job_dict.get("tags", []),
                    pre_script=job_dict.get("pre_script"), working_dir=job_dict.get("working_dir"),
                    env_vars=job_dict.get("env_vars", {}), timeout=job_dict.get("timeout", 3600),
                    max_retries=job_dict.get("max_retries", 3)
                )
                job.last_run = datetime.fromisoformat(job_dict["last_run"]) if job_dict.get("last_run") else None
                job.last_status = job_dict.get("last_status")
                job.last_output = job_dict.get("last_output")
                job.run_count = job_dict.get("run_count", 0)
                job.created_at = job_dict.get("created_at", datetime.now().isoformat())
                
                self._jobs[job_id] = job
        
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
    
    def add_job(self, name: str, command: str, cron_expr: str,
                description: str = "", tags: List[str] = None,
                pre_script: str = None, working_dir: str = None,
                env_vars: Dict[str, str] = None, timeout: int = 3600,
                max_retries: int = 3, enabled: bool = True) -> Dict[str, Any]:
        try:
            CronParser.parse(cron_expr)
        except ValueError as e:
            return {"success": False, "error": f"Invalid cron expression: {e}"}
        
        import uuid
        job_id = str(uuid.uuid4().hex[:12])
        
        job = CronJob(
            job_id=job_id, name=name, command=command, cron_expr=cron_expr,
            description=description, tags=tags, pre_script=pre_script,
            working_dir=working_dir, env_vars=env_vars, timeout=timeout,
            max_retries=max_retries, enabled=enabled
        )
        
        job.next_run = CronParser.get_next_run(cron_expr)
        
        with self._lock:
            self._jobs[job_id] = job
            self._save_jobs()
        
        logger.info(f"Added cron job: {name} ({job_id})")
        return {"success": True, "job": job.to_dict()}
    
    def update_job(self, job_id: str, **updates) -> Dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"success": False, "error": "Job not found"}
            
            if "cron_expr" in updates:
                try:
                    CronParser.parse(updates["cron_expr"])
                    job.next_run = CronParser.get_next_run(updates["cron_expr"])
                except ValueError as e:
                    return {"success": False, "error": f"Invalid cron expression: {e}"}
            
            for key in ["name", "command", "cron_expr", "description", "tags",
                       "pre_script", "working_dir", "env_vars", "timeout", "max_retries", "enabled"]:
                if key in updates:
                    setattr(job, key, updates[key])
            
            job.updated_at = datetime.now().isoformat()
            self._save_jobs()
        
        return {"success": True, "job": job.to_dict()}
    
    def delete_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            if job_id not in self._jobs:
                return {"success": False, "error": "Job not found"}
            
            del self._jobs[job_id]
            self._callbacks.pop(job_id, None)
            self._save_jobs()
        
        return {"success": True, "message": "Job deleted"}
    
    def list_jobs(self, tag: str = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        
        if tag:
            jobs = [j for j in jobs if tag in j.tags]
        
        if enabled_only:
            jobs = [j for j in jobs if j.enabled]
        
        return [j.to_dict() for j in jobs]
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.to_dict() if job else None
    
    def trigger_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"success": False, "error": "Job not found"}
        
        self._execute_job(job)
        return {"success": True, "status": job.last_status, "output": job.last_output}
    
    def register_callback(self, job_id: str, callback: Callable) -> None:
        self._callbacks[job_id] = callback
    
    def validate_cron_expr(self, cron_expr: str) -> Dict[str, Any]:
        try:
            parsed = CronParser.parse(cron_expr)
            next_run = CronParser.get_next_run(cron_expr)
            return {"success": True, "valid": True, "parsed": parsed, "next_run": next_run.isoformat()}
        except ValueError as e:
            return {"success": False, "valid": False, "error": str(e)}
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {"name": "cron_add", "description": "Add a new scheduled cron job", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "command": {"type": "string"}, "cron_expr": {"type": "string", "description": "Cron expression (e.g., '0 9 * * *' for daily at 9am)"}, "description": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}, "pre_script": {"type": "string"}, "working_dir": {"type": "string"}, "timeout": {"type": "integer", "default": 3600}, "enabled": {"type": "boolean", "default": True}}, "required": ["name", "command", "cron_expr"]}},
            {"name": "cron_list", "description": "List all scheduled jobs", "parameters": {"type": "object", "properties": {"tag": {"type": "string"}, "enabled_only": {"type": "boolean", "default": False}}, "required": []}},
            {"name": "cron_get", "description": "Get details of a specific job", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
            {"name": "cron_update", "description": "Update an existing cron job", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}, "name": {"type": "string"}, "command": {"type": "string"}, "cron_expr": {"type": "string"}, "enabled": {"type": "boolean"}}, "required": ["job_id"]}},
            {"name": "cron_delete", "description": "Delete a cron job", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
            {"name": "cron_trigger", "description": "Manually trigger a job to run now", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
            {"name": "cron_validate", "description": "Validate a cron expression", "parameters": {"type": "object", "properties": {"cron_expr": {"type": "string"}}, "required": ["cron_expr"]}}
        ]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if tool_name == "cron_add":
                result = self.add_job(name=args.get("name", ""), command=args.get("command", ""), cron_expr=args.get("cron_expr", ""), description=args.get("description", ""), tags=args.get("tags", []), pre_script=args.get("pre_script"), working_dir=args.get("working_dir"), env_vars=args.get("env_vars"), timeout=args.get("timeout", 3600), enabled=args.get("enabled", True))
            elif tool_name == "cron_list":
                result = {"success": True, "jobs": self.list_jobs(tag=args.get("tag"), enabled_only=args.get("enabled_only", False))}
            elif tool_name == "cron_get":
                job = self.get_job(args.get("job_id", ""))
                result = {"success": True, "job": job} if job else {"success": False, "error": "Job not found"}
            elif tool_name == "cron_update":
                result = self.update_job(job_id=args.get("job_id", ""), name=args.get("name"), command=args.get("command"), cron_expr=args.get("cron_expr"), enabled=args.get("enabled"))
            elif tool_name == "cron_delete":
                result = self.delete_job(args.get("job_id", ""))
            elif tool_name == "cron_trigger":
                result = self.trigger_job(args.get("job_id", ""))
            elif tool_name == "cron_validate":
                result = self.validate_cron_expr(args.get("cron_expr", ""))
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Cron tool error: {e}")
            return json.dumps({"success": False, "error": str(e)})