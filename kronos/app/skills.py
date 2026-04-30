"""技能管理系统 - 支持自动技能创建、搜索和分享"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class Skill:
    """技能类"""
    
    def __init__(self, skill_id: str, name: str, description: str, content: str,
                 metadata: Dict[str, Any] = None, file_path: str = None):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.content = content
        self.metadata = metadata or {}
        self.file_path = file_path
        self.created_at = metadata.get("created_at", datetime.now().isoformat())
        self.updated_at = metadata.get("updated_at", datetime.now().isoformat())
        self.tags = metadata.get("tags", [])
        self.author = metadata.get("author", "kronos-agent")
        self.version = metadata.get("version", "1.0.0")
        self.usage_count = metadata.get("usage_count", 0)
        self.last_used = metadata.get("last_used")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "file_path": self.file_path
        }
    
    def to_yaml_frontmatter(self) -> str:
        frontmatter = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count
        }
        
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_content}---\n\n{self.content}"
    
    @classmethod
    def from_yaml_content(cls, content: str, file_path: str = None) -> "Skill":
        pattern = r"^---\n(.*?)\n---\n*(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            
            try:
                metadata = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError:
                metadata = {}
            
            name = metadata.get("name", Path(file_path).stem if file_path else "Unknown")
            description = metadata.get("description", "")
        else:
            metadata = {}
            name = Path(file_path).stem if file_path else "Unknown"
            description = ""
            body = content
        
        import uuid
        skill_id = metadata.get("skill_id", str(uuid.uuid4().hex[:12]))
        
        return cls(
            skill_id=skill_id,
            name=name,
            description=description,
            content=body.strip(),
            metadata=metadata,
            file_path=file_path
        )


class SkillManager:
    """技能管理器"""
    
    def __init__(self, skills_dir: str = None):
        self._skills_dir = skills_dir or str(Path.home() / ".kronos" / "skills")
        self._skills: Dict[str, Skill] = {}
        self._name_index: Dict[str, str] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._initialized = False
    
    def _ensure_dir(self) -> None:
        Path(self._skills_dir).mkdir(parents=True, exist_ok=True)
    
    def load_skills(self, skills_dir: str = None) -> int:
        if skills_dir:
            self._skills_dir = skills_dir
        
        self._ensure_dir()
        self._skills.clear()
        self._name_index.clear()
        self._tag_index.clear()
        
        loaded = 0
        for path in Path(self._skills_dir).glob("*.md"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                skill = Skill.from_yaml_content(content, str(path))
                self._add_skill(skill)
                loaded += 1
                
            except Exception as e:
                logger.warning(f"Failed to load skill from {path}: {e}")
        
        self._initialized = True
        logger.info(f"Loaded {loaded} skills from {self._skills_dir}")
        return loaded
    
    def _add_skill(self, skill: Skill) -> None:
        self._skills[skill.skill_id] = skill
        self._name_index[skill.name.lower()] = skill.skill_id
        
        for tag in skill.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if skill.skill_id not in self._tag_index[tag]:
                self._tag_index[tag].append(skill.skill_id)
    
    def _remove_skill_from_index(self, skill: Skill) -> None:
        self._name_index.pop(skill.name.lower(), None)
        
        for tag in skill.tags:
            if tag in self._tag_index:
                self._tag_index[tag] = [sid for sid in self._tag_index[tag] if sid != skill.skill_id]
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
    
    def create_skill(self, name: str, description: str, content: str,
                    tags: List[str] = None, author: str = "kronos-agent",
                    version: str = "1.0.0") -> Dict[str, Any]:
        import uuid
        
        skill_id = str(uuid.uuid4().hex[:12])
        
        metadata = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "author": author,
            "version": version,
            "tags": tags or [],
            "usage_count": 0
        }
        
        skill = Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            content=content,
            metadata=metadata
        )
        
        self._save_skill_to_file(skill)
        self._add_skill(skill)
        
        return {"success": True, "skill": skill.to_dict()}
    
    def _save_skill_to_file(self, skill: Skill) -> None:
        self._ensure_dir()
        
        safe_name = re.sub(r'[^\w\-_. ]', '', skill.name).strip()
        filename = f"{safe_name}_{skill.skill_id}.md"
        file_path = Path(self._skills_dir) / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(skill.to_yaml_frontmatter())
        
        skill.file_path = str(file_path)
    
    def get_skill(self, skill_id: str = None, name: str = None) -> Optional[Skill]:
        if skill_id and skill_id in self._skills:
            return self._skills[skill_id]
        
        if name:
            skill_id = self._name_index.get(name.lower())
            if skill_id:
                return self._skills.get(skill_id)
        
        return None
    
    def update_skill(self, skill_id: str, **updates) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            return {"success": False, "error": "Skill not found"}
        
        self._remove_skill_from_index(skill)
        
        if "name" in updates:
            skill.name = updates["name"]
        if "description" in updates:
            skill.description = updates["description"]
        if "content" in updates:
            skill.content = updates["content"]
        if "tags" in updates:
            skill.tags = updates["tags"]
        
        skill.metadata["updated_at"] = datetime.now().isoformat()
        
        if "version" in updates:
            skill.version = updates["version"]
        
        self._save_skill_to_file(skill)
        self._add_skill(skill)
        
        return {"success": True, "skill": skill.to_dict()}
    
    def delete_skill(self, skill_id: str) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            return {"success": False, "error": "Skill not found"}
        
        if skill.file_path and Path(skill.file_path).exists():
            Path(skill.file_path).unlink()
        
        self._remove_skill_from_index(skill)
        del self._skills[skill_id]
        
        return {"success": True, "message": "Skill deleted"}
    
    def search_skills(self, query: str, limit: int = 10) -> List[Skill]:
        if not query:
            return list(self._skills.values())[:limit]
        
        query_lower = query.lower()
        scored = []
        
        for skill in self._skills.values():
            score = 0
            
            if query_lower in skill.name.lower():
                score += 10
            if query_lower in skill.description.lower():
                score += 5
            if any(query_lower in tag.lower() for tag in skill.tags):
                score += 3
            if query_lower in skill.content.lower():
                score += 1
            
            if score > 0:
                scored.append((score, skill))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]
    
    def list_skills(self, tag: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        if tag and tag in self._tag_index:
            skill_ids = self._tag_index[tag]
            skills = [self._skills[sid] for sid in skill_ids if sid in self._skills]
        else:
            skills = list(self._skills.values())
        
        skills.sort(key=lambda s: s.metadata.get("usage_count", 0), reverse=True)
        
        return [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "description": s.description,
                "tags": s.tags,
                "version": s.version,
                "usage_count": s.metadata.get("usage_count", 0),
                "updated_at": s.metadata.get("updated_at")
            }
            for s in skills[:limit]
        ]
    
    def record_usage(self, skill_id: str) -> None:
        skill = self._skills.get(skill_id)
        if skill:
            skill.metadata["usage_count"] = skill.metadata.get("usage_count", 0) + 1
            skill.metadata["last_used"] = datetime.now().isoformat()
            self._save_skill_to_file(skill)
    
    def generate_skill_from_task(self, task_description: str, solution: str,
                                 task_name: str = None, tags: List[str] = None) -> Dict[str, Any]:
        name = task_name or self._extract_task_name(task_description)
        
        content_parts = [
            f"# {name}\n",
            f"## Task Description\n{task_description}\n",
            "## Solution\n```\n" + solution.strip() + "\n```\n",
            "## Notes\n",
            "- This skill was automatically generated by Kronos Agent",
            f"- Generated at: {datetime.now().isoformat()}"
        ]
        
        content = "\n".join(content_parts)
        description = task_description[:200] if len(task_description) > 200 else task_description
        
        default_tags = ["auto-generated", "kronos-agent"]
        if tags:
            default_tags.extend(tags)
        
        return self.create_skill(
            name=name,
            description=description,
            content=content,
            tags=default_tags
        )
    
    def _extract_task_name(self, description: str) -> str:
        words = re.findall(r'\b\w+\b', description)
        
        important_words = [w for w in words if len(w) > 3 and w.lower() not in 
                          {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'been', 'were', 'they', 'their'}]
        
        if important_words:
            return " ".join(important_words[:4]).title()
        
        return f"Task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def export_skill(self, skill_id: str, format: str = "yaml") -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            return {"success": False, "error": "Skill not found"}
        
        if format == "yaml":
            return {"success": True, "content": skill.to_yaml_frontmatter(), "format": "yaml"}
        else:
            return {"success": True, "content": json.dumps(skill.to_dict(), indent=2, ensure_ascii=False), "format": "json"}
    
    def import_skill(self, content: str, format: str = "yaml") -> Dict[str, Any]:
        try:
            if format == "yaml":
                skill = Skill.from_yaml_content(content)
            else:
                data = json.loads(content)
                import uuid
                skill = Skill(
                    skill_id=data.get("skill_id", str(uuid.uuid4().hex[:12])),
                    name=data.get("name", "Imported Skill"),
                    description=data.get("description", ""),
                    content=data.get("content", ""),
                    metadata=data.get("metadata", {}),
                    file_path=data.get("file_path")
                )
            
            existing_id = self._name_index.get(skill.name.lower())
            if existing_id:
                return {"success": False, "error": f"Skill with name '{skill.name}' already exists"}
            
            self._save_skill_to_file(skill)
            self._add_skill(skill)
            
            return {"success": True, "skill": skill.to_dict()}
        
        except Exception as e:
            logger.error(f"Failed to import skill: {e}")
            return {"success": False, "error": str(e)}
    
    def get_skill_by_name(self, name: str, auto_create: bool = False) -> Optional[Skill]:
        return self.get_skill(name=name)
    
    def is_skill_ready(self, skill_id: str) -> bool:
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        
        if skill.file_path:
            return Path(skill.file_path).exists()
        
        return True
    
    def check_all_skills_ready(self) -> Dict[str, Any]:
        results = {"total": len(self._skills), "ready": 0, "broken": [], "unused": []}
        
        for skill in self._skills.values():
            if self.is_skill_ready(skill.skill_id):
                results["ready"] += 1
                
                if skill.metadata.get("usage_count", 0) == 0:
                    results["unused"].append({
                        "skill_id": skill.skill_id,
                        "name": skill.name,
                        "created_at": skill.metadata.get("created_at")
                    })
            else:
                results["broken"].append({
                    "skill_id": skill.skill_id,
                    "name": skill.name,
                    "file_path": skill.file_path
                })
        
        return results
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {"name": "skill_create", "description": "Create a new reusable skill", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}, "content": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["name", "description", "content"]}},
            {"name": "skill_list", "description": "List all available skills", "parameters": {"type": "object", "properties": {"tag": {"type": "string"}, "limit": {"type": "integer", "default": 50}}, "required": []}},
            {"name": "skill_search", "description": "Search for skills by query", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
            {"name": "skill_get", "description": "Get skill details by name or ID", "parameters": {"type": "object", "properties": {"skill_id": {"type": "string"}, "name": {"type": "string"}}, "required": []}},
            {"name": "skill_update", "description": "Update an existing skill", "parameters": {"type": "object", "properties": {"skill_id": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"}, "content": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["skill_id"]}},
            {"name": "skill_delete", "description": "Delete a skill", "parameters": {"type": "object", "properties": {"skill_id": {"type": "string"}}, "required": ["skill_id"]}},
            {"name": "skill_generate", "description": "Auto-generate a skill from task and solution", "parameters": {"type": "object", "properties": {"task": {"type": "string"}, "solution": {"type": "string"}, "name": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["task", "solution"]}},
            {"name": "skill_export", "description": "Export a skill to share", "parameters": {"type": "object", "properties": {"skill_id": {"type": "string"}, "format": {"type": "string", "enum": ["yaml", "json"]}}, "required": ["skill_id"]}},
            {"name": "skill_import", "description": "Import a skill from content", "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "format": {"type": "string", "enum": ["yaml", "json"]}}, "required": ["content"]}},
            {"name": "skill_status", "description": "Check status of all skills", "parameters": {"type": "object", "properties": {}, "required": []}}
        ]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if tool_name == "skill_create":
                result = self.create_skill(name=args.get("name", ""), description=args.get("description", ""), content=args.get("content", ""), tags=args.get("tags", []))
            elif tool_name == "skill_list":
                result = {"success": True, "skills": self.list_skills(tag=args.get("tag"), limit=args.get("limit", 50))}
            elif tool_name == "skill_search":
                result = {"success": True, "skills": [s.to_dict() for s in self.search_skills(query=args.get("query", ""), limit=args.get("limit", 10))]}
            elif tool_name == "skill_get":
                skill = self.get_skill(skill_id=args.get("skill_id"), name=args.get("name"))
                if skill:
                    self.record_usage(skill.skill_id)
                    result = {"success": True, "skill": skill.to_dict()}
                else:
                    result = {"success": False, "error": "Skill not found"}
            elif tool_name == "skill_update":
                result = self.update_skill(skill_id=args.get("skill_id", ""), name=args.get("name"), description=args.get("description"), content=args.get("content"), tags=args.get("tags"))
            elif tool_name == "skill_delete":
                result = self.delete_skill(skill_id=args.get("skill_id", ""))
            elif tool_name == "skill_generate":
                result = self.generate_skill_from_task(task_description=args.get("task", ""), solution=args.get("solution", ""), task_name=args.get("name"), tags=args.get("tags"))
            elif tool_name == "skill_export":
                result = self.export_skill(skill_id=args.get("skill_id", ""), format=args.get("format", "yaml"))
            elif tool_name == "skill_import":
                result = self.import_skill(content=args.get("content", ""), format=args.get("format", "yaml"))
            elif tool_name == "skill_status":
                result = self.check_all_skills_ready()
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Skill tool error: {e}")
            return json.dumps({"success": False, "error": str(e)})