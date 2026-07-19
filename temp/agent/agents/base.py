# Chức năng: Định nghĩa interface BaseAgent cho mọi tác nhân con (Sub-agent) trong hệ thống.

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type
from pydantic import BaseModel
from state import AgentState

class BaseAgent(ABC):
    """Lớp cơ sở trừu tượng quy định Hợp đồng 4 phần bắt buộc đối với tất cả Sub-agents."""

    def __init__(
        self,
        goal_context: str,
        task_boundary: str,
        skills_tools: List[str],
        output_schema: Type[BaseModel]
    ):
        self.goal_context = goal_context
        self.task_boundary = task_boundary
        self.skills_tools = skills_tools
        self.output_schema = output_schema

    @abstractmethod
    def run(self, state: AgentState) -> Dict[str, Any]:
        """Thực thi suy luận nghiệp vụ của tác nhân và trả về kết quả tuân thủ output_schema."""
        pass
