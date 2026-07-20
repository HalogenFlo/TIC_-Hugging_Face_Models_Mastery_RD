# Chức năng: Cấu hình hệ thống, quản lý driver kết nối cơ sở dữ liệu và model adapters.

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
from typing import Optional, Any, List
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

load_dotenv()

# --- Các hằng số điều phối và vòng lặp ---
MAX_LOOP_STEPS = int(os.getenv("MAX_LOOP_STEPS", 5))
DEFAULT_SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", 5))

# --- Cấu hình Clarification Gate (Cơ chế hỏi lại) ---
CLARIFICATION_THRESHOLD = float(os.getenv("CLARIFICATION_THRESHOLD", 0.75))
MAX_CLARIFICATION_TURNS = int(os.getenv("MAX_CLARIFICATION_TURNS", 3))

# --- Cấu hình Context Compaction (Bộ nén ngữ cảnh) ---
COMPACTION_TOKEN_THRESHOLD = int(os.getenv("COMPACTION_TOKEN_THRESHOLD", 10000))

# --- Cấu hình Effort-Scaling (Giới hạn nỗ lực theo độ khó) ---
EFFORT_BYPASS_MAX_TOOL_CALLS = int(os.getenv("EFFORT_BYPASS_MAX_TOOL_CALLS", 1))
EFFORT_SIMPLE_MAX_TOOL_CALLS = int(os.getenv("EFFORT_SIMPLE_MAX_TOOL_CALLS", 10))
EFFORT_COMPLEX_MAX_TOOL_CALLS = int(os.getenv("EFFORT_COMPLEX_MAX_TOOL_CALLS", 15))

# --- Cấu hình Validation (Ngưỡng xác thực trích dẫn) ---
VALIDATION_SCORE_THRESHOLD = float(os.getenv("VALIDATION_SCORE_THRESHOLD", 0.8))

# --- Các hằng số model mặc định của hệ thống ---
MODEL_ORCHESTRATOR_GPT = "gpt-4o-mini"
MODEL_SUB_AGENT_GPT = "gpt-4o-mini"
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

MODEL_ORCHESTRATOR_GEMINI = "gemini-3.5-flash"
MODEL_SUB_AGENT_GEMINI = "gemini-3.5-flash"
MODEL_EMBEDDING_GEMINI = "gemini-embedding-001"
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# --- Cấu hình Neo4j Database ---
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

# --- Cấu hình Redis (Session Context / Short-term memory) ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# --- Cấu hình Relational Database (Personal Memory / Long-term memory) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_URI = os.getenv("DB_URI") or os.getenv("DATABASE_URL")

# --- DRIVERS & CLIENTS ---
_neo4j_driver: Optional[Driver] = None
_redis_client: Optional[Any] = None
_db_connection: Optional[Any] = None

def get_neo4j_driver() -> Driver:
    global _neo4j_driver
    if _neo4j_driver is None:
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            raise ValueError("Missing Neo4j connection configuration in .env")
            
        try:
            _neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
            _neo4j_driver.verify_connectivity()
        except Exception as e:
            _neo4j_driver = None
            raise ConnectionError(f"Cannot connect to Neo4j database: {str(e)}")
            
    return _neo4j_driver

def close_neo4j_driver() -> None:
    global _neo4j_driver
    if _neo4j_driver is not None:
        try:
            _neo4j_driver.close()
        except Exception as e:
            print(f"Error closing Neo4j Driver: {e}")
        finally:
            _neo4j_driver = None

def get_redis_client() -> Optional[Any]:
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None
            
    try:
        import redis
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        _redis_client.ping()
        return _redis_client
    except ImportError:
        print("[WARNING] 'redis' library is not installed. Please run: pip install redis")
        return None
    except Exception as e:
        print(f"[WARNING] Cannot connect to Redis: {e}")
        _redis_client = None
        return None

def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
        except Exception as e:
            print(f"Error closing Redis Client: {e}")
        finally:
            _redis_client = None

def get_db_connection() -> Optional[Any]:
    global _db_connection
    if _db_connection is not None:
        try:
            if hasattr(_db_connection, "closed") and _db_connection.closed == 0:
                return _db_connection
            if hasattr(_db_connection, "ping"):
                _db_connection.ping(reconnect=True)
                return _db_connection
        except Exception:
            _db_connection = None
            
    # Ưu tiên kết nối qua URI nếu có sử dụng SQLAlchemy
    if DB_URI:
        try:
            from sqlalchemy import create_engine
            if DB_URI.startswith("sqlite"):
                engine = create_engine(DB_URI)
            else:
                engine = create_engine(DB_URI, pool_size=5, max_overflow=10)
            _db_connection = engine.connect()
            return _db_connection
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARNING] Cannot connect to DB via URI using SQLAlchemy: {e}")
            
    # Fallback kết nối trực tiếp PostgreSQL bằng psycopg2
    try:
        import psycopg2
        _db_connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        return _db_connection
    except ImportError:
        # Nếu không có psycopg2, thử pymysql (cho MySQL)
        try:
            import pymysql
            _db_connection = pymysql.connect(
                host=DB_HOST,
                port=int(DB_PORT) if DB_PORT else 3306,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            return _db_connection
        except ImportError:
            print("[WARNING] DB connection libraries ('psycopg2', 'pymysql', or 'sqlalchemy') are not installed.")
    except Exception as e:
        print(f"[WARNING] Cannot connect to relational database: {e}")

    # Fallback tự động sang SQLite cục bộ nếu không kết nối được PostgreSQL/MySQL
    try:
        print("[INFO] Auto fallback database connection to local SQLite (tic_personal_memory.db)")
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///tic_personal_memory.db")
        _db_connection = engine.connect()
        return _db_connection
    except Exception as e:
        print(f"[WARNING] Auto fallback to SQLite failed: {e}")
        _db_connection = None
        return None

def close_db_connection() -> None:
    global _db_connection
    if _db_connection is not None:
        try:
            _db_connection.close()
        except Exception as e:
            print(f"Error closing DB Connection: {e}")
        finally:
            _db_connection = None

def close_all_connections() -> None:
    """Đóng toàn bộ kết nối đang mở."""
    close_neo4j_driver()
    close_redis_client()
    close_db_connection()

# --- HÀM KHỞI TẠO MODEL ---
class OpenAIModelAdapter:
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name

    def generate(self, messages: list, response_schema: Optional[Any] = None, **kwargs) -> str:
        if response_schema:
            from pydantic import BaseModel
            # Nếu response_schema là một lớp kế thừa từ Pydantic BaseModel
            if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
                response = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=messages,
                    response_format=response_schema,
                    **kwargs
                )
                return response.choices[0].message.content
            else:
                # Nếu response_schema là một dict JSON Schema
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "strict": True,
                        "schema": response_schema
                    }
                }
                
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

class GeminiModelAdapter:
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name

    def generate(self, messages: list, response_schema: Optional[Any] = None, **kwargs) -> str:
        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        # Xây dựng config cho google.genai SDK
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if response_schema:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = response_schema
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config if config else None,
        )
        return response.text

def get_ai_model(model_name: str, provider: str = "openai") -> Any:
    provider = provider.lower()
    
    # Tự động mapping model name phù hợp với provider để tránh lỗi hardcode model name của provider khác
    if provider == "openai" and "gemini" in model_name.lower():
        model_name = "gpt-4o-mini"
    elif provider == "gemini" and ("gpt" in model_name.lower() or "openai" in model_name.lower()):
        model_name = "gemini-3.5-flash"
        
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Thiếu cấu hình GITHUB_TOKEN hoặc OPENAI_API_KEY trong file .env")
            
        base_url = GITHUB_MODELS_ENDPOINT if os.getenv("GITHUB_TOKEN") else None
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        return OpenAIModelAdapter(client, model_name)
        
    elif provider == "gemini":
        from google import genai
        api_key = os.getenv("Gemini_OpenAI") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Thiếu cấu hình Gemini_OpenAI hoặc GEMINI_API_KEY trong file .env")
            
        client = genai.Client(api_key=api_key)
        return GeminiModelAdapter(client, model_name)
        
    else:
        raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ. Chỉ hỗ trợ 'openai' hoặc 'gemini'.")


def get_embedding(text: str, provider: str = DEFAULT_PROVIDER) -> List[float]:
    """Sinh vector embedding từ văn bản với số chiều là 3072."""
    # Bắt buộc sử dụng gemini cho embedding để đồng nhất không gian vector của Neo4j DB
    provider = "gemini"
    provider = provider.lower()
    
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Thiếu cấu hình GITHUB_TOKEN hoặc OPENAI_API_KEY trong file .env")
            
        base_url = GITHUB_MODELS_ENDPOINT if os.getenv("GITHUB_TOKEN") else None
        client = OpenAI(base_url=base_url, api_key=api_key)
        
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
        
    elif provider == "gemini":
        from google import genai
        from google.genai import types
        api_key = os.getenv("Gemini_OpenAI") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Thiếu cấu hình Gemini_OpenAI hoặc GEMINI_API_KEY trong file .env")
            
        client = genai.Client(api_key=api_key)
        
        response = client.models.embed_content(
            model=MODEL_EMBEDDING_GEMINI,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=3072)
        )
        return response.embeddings[0].values
        
    else:
        raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ để sinh embedding.")