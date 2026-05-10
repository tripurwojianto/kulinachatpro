"""Configuration module for the customer service agent."""
import logging
import os
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AgentModel(BaseModel):
    """Agent model settings."""
    name: str = Field(default="customer_service_agent")
    model: str = Field(default="openai/gpt-4o-mini")


class Config(BaseSettings):
    """Configuration settings for the customer service agent."""
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        env_prefix="GOOGLE_",
        case_sensitive=True,
        extra="ignore",       # ← ini fix-nya: abaikan key di luar GOOGLE_*
    )

    agent_settings: AgentModel = Field(default=AgentModel())
    app_name: str = "customer_service_app"
    CLOUD_PROJECT: str = Field(default="")
    CLOUD_LOCATION: str = Field(default="us-central1")
    GENAI_USE_VERTEXAI: str = Field(default="0")
    API_KEY: str | None = Field(default="")
