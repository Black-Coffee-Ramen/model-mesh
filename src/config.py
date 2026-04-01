from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LLM Router Gateway"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    
    # Routing
    default_routing_strategy: str = "cost"

    class Config:
        env_file = ".env"

settings = Settings()
