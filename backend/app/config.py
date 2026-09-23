from dotenv import load_dotenv
import os

load_dotenv()

Settings = type("Settings", (), {})

Settings.DB_PATH = os.getenv("PCM_DB_PATH", "pcm.db")
Settings.EMBEDDING_MODEL = os.getenv("PCM_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

Settings.LLM_ENABLED = os.getenv("PCM_LLM_ENABLED", "false").lower() == "true"
Settings.LLM_PROVIDER = os.getenv("PCM_LLM_PROVIDER", "anthropic")
Settings.LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
Settings.LLM_MODEL = os.getenv("PCM_LLM_MODEL", "claude-3-5-haiku-latest")

Settings.GROK_API_KEY = os.getenv("GROK_API_KEY", "")
Settings.GROK_MODEL = os.getenv("PCM_GROK_MODEL", "grok-beta")

Settings.SIGNAL_SEMANTIC = os.getenv("PCM_SIGNAL_SEMANTIC", "true").lower() == "true"
Settings.SIGNAL_GIT = os.getenv("PCM_SIGNAL_GIT", "true").lower() == "true"
Settings.SIGNAL_FILES = os.getenv("PCM_SIGNAL_FILES", "true").lower() == "true"
Settings.SIGNAL_BROWSER = os.getenv("PCM_SIGNAL_BROWSER", "true").lower() == "true"
Settings.SIGNAL_TERMINAL = os.getenv("PCM_SIGNAL_TERMINAL", "true").lower() == "true"
Settings.SIGNAL_RECENT_ACTIVITY = os.getenv("PCM_SIGNAL_RECENT_ACTIVITY", "true").lower() == "true"

Settings.WEIGHT_SEMANTIC = float(os.getenv("PCM_WEIGHT_SEMANTIC", "0.3"))
Settings.WEIGHT_PATH = float(os.getenv("PCM_WEIGHT_PATH", "0.3"))
Settings.WEIGHT_GIT = float(os.getenv("PCM_WEIGHT_GIT", "0.2"))
Settings.WEIGHT_RECENT = float(os.getenv("PCM_WEIGHT_RECENT", "0.2"))

Settings.SNAPSHOT_INTERVAL_SECONDS = int(os.getenv("PCM_SNAPSHOT_INTERVAL", "1800"))

Settings.ACCESS_PIN = os.getenv("PCM_ACCESS_PIN", "")
Settings.FACTCHECK_API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY", "")

settings = Settings()