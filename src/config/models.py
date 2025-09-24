from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ProviderConfig:
    model: str
    api_url: str
    temperature: float = 0.3
    max_tokens: int = 1000
    timeout: int = 45
    env_key: Optional[str] = None


@dataclass
class AIConfig:
    base_provider: str = "openrouter"
    context_switching: bool = True
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    context_rules: Dict[str, dict] = field(default_factory=dict)
    prompts: Dict[str, str] = field(default_factory=dict)
    # Deprecated fields for backward compatibility
    model: str = ""
    api_url: str = ""
    temperature: float = 0.4
    max_tokens: int = 250
    timeout: int = 45


@dataclass
class FormatConfig:
    max_subject_length: int = 50
    require_body_for_features: bool = True
    enforce_conventional: bool = True
    allowed_types: List[str] = field(
        default_factory=lambda: [
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "test",
            "chore",
        ]
    )


@dataclass
class ContextConfig:
    wip_keywords: List[str] = field(default_factory=lambda: ["TODO", "FIXME", "WIP"])
    auto_detect: bool = True
    presets: Dict[str, str] = field(default_factory=dict)


@dataclass
class DiffConfig:
    context_reserve: int = 4000
    char_per_line_ratio: int = 80


@dataclass
class Config:
    ai: AIConfig
    format: FormatConfig
    context: ContextConfig
    diff: DiffConfig
