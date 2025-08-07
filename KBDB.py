import os
import logging
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2 import sql
from openai import OpenAI
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Global SQL queries
SEARCH_QUERY = """
SELECT
    d.doc_id,
    d.name AS doc_name,
    dc.content AS matching_content
FROM embeddings e
JOIN document_chunks dc ON e.chunk_id = dc.chunk_id
JOIN documents d ON dc.doc_id = d.doc_id
WHERE e.model = %s AND e.task = %s
ORDER BY e.embedding {operator} %s::vector {order_direction}
LIMIT %s;
"""

# Dataclasses
@dataclass
class Model:
    model:  str
    prefix: str = ""
    suffix: str = ""
    distance_metric: str = "cosine"  # cosine, inner_product, l2

@dataclass
class Task:
    name: str
    description: str

# Model and task configurations
MODELS = {
    "qa":           Model(model="nomic-embed-text:v1.5",                 prefix="search_query: "  ),
    "style":        Model(model="nomic-embed-text:v1.5",                 prefix="classification: "),
    "semantic":     Model(model="nomic-embed-text:v1.5",                 prefix="clustering: "    ),
    "similar_code": Model(model="hamidakach/nomic-embed-text-v1.5-GGUF", prefix="clustering: "    ),
}

TASKS = {
    "style":        Task(name="style",        description="Search for content clustered by theme or style"),
    "qa":           Task(name="qa",           description="Search optimized for question->answer pairs"   ),
    "semantic":     Task(name="semantic",     description="Search based on semantic similarity"           ),
    "similar_code": Task(name="similar_code", description="Search for similar code snippets"              ),
}

# Distance metric mappings
DISTANCE_OPERATORS = {
    "cosine":        "<=>",
    "inner_product": "<#>",
    "l2":            "<->",
}

DISTANCE_ORDER = {
    "cosine":        "ASC" ,
    "inner_product": "DESC", 
    "l2":            "ASC" ,
}

class RAGMCPServer:
    def __init__(self):
        self.db_conn = None
        self.openai_client = None
        self._initialize_connections()
        
    def _initialize_connections(self):
        """Initialize database and OpenAI connections"""
        try:
            # Initialize database connection
            self.db_conn = psycopg2.connect(
                host=os.getenv("RM_DB_HOST"),
                port=os.getenv("RM_DB_PORT"),
                database=os.getenv("RM_DB_NAME"),
                user=os.getenv("RM_DB_USER"),
                password=os.getenv("RM_DB_PASSWORD")
            )
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.fatal(f"Failed to connect to database: {e}")
            sys.exit(1)
            
        try:
            # Initialize OpenAI client
            self.openai_client = OpenAI(
                api_key=os.getenv("RM_OPENAI_API_KEY"),
                base_url=os.getenv("RM_OPENAI_ENDPOINT")
            )
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.fatal(f"Failed to initialize OpenAI client: {e}")
            sys.exit(1)
    
    def _get_embedding(self, text: str, model: Model) -> List[float]:
        """Get embedding for text using specified model configuration"""
        try:
            formatted_text = f"{model.prefix}{text}{model.suffix}"
            response = self.openai_client.embeddings.create(
                model=model.model,  # Use the model's specified embedding model
                input=formatted_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise
    
    def _search_database(self, query_embedding: List[float], model: Model, task: Task, top_k: int) -> List[Dict[str, Any]]:
        """Search database for similar embeddings"""
        try:
            operator = DISTANCE_OPERATORS[model.distance_metric]
            order_direction = DISTANCE_ORDER[model.distance_metric]
            
            formatted_query = SEARCH_QUERY.format(
                operator=operator,
                order_direction=order_direction,
            )

            logger.debug(f"Executing search query: {formatted_query}")
            
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    formatted_query,
                    (model.model, task.name, query_embedding, top_k),
                )

                logger.debug(f"Executed query: {cursor.query.decode('utf-8')}")

                results = cursor.fetchall()

                return [
                    {
                        "doc_id": str(row[0]),
                        "doc_name": row[1],
                        "matching_content": row[2],
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            raise
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for MCP response"""
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted_parts = []
        for i, result in enumerate(results, 1):
            formatted_parts.append(
                f"--- Result {i} | {result['doc_name']} | {result['doc_id']} ---\n"
                f"--- Document Start ---\n"
                f"Content: {result['matching_content']}\n"
                f"--- Document End ---\n"
            )
        
        return "\n".join(formatted_parts)

# Initialize FastMCP and RAG server
rag_server = RAGMCPServer()
mcp = FastMCP("KBDB")

@mcp.tool
def search_style(query: str, top_k: int = 3) -> str:
    """Search for content clustered by theme or style"""
    try:
        model = MODELS["style"]
        task  = TASKS["style"]
        
        logger.debug(f"Style search query: {query}")
        logger.debug(f"Using model: {model.model}, task: {task.name}, top_k: {top_k}")

        query_embedding = rag_server._get_embedding(query, model)
        results = rag_server._search_database(query_embedding, model, task, top_k)
        
        logger.debug(f"Style search results: {results}")

        return rag_server._format_results(results)
    except Exception as e:
        logger.error(f"Style search failed: {e}")
        return f"Search failed: {str(e)}"

@mcp.tool
def search_qa(query: str, top_k: int = 3) -> str:
    """Search optimized for question-answer pairs"""
    try:
        model = MODELS["qa"]
        task  = TASKS["qa"]
        
        logger.debug(f"QA search query: {query}")
        logger.debug(f"Using model: {model.model}, task: {task.name}, top_k: {top_k}")

        query_embedding = rag_server._get_embedding(query, model)
        results = rag_server._search_database(query_embedding, model, task, top_k)
        
        logger.debug(f"QA search results: {results}")

        return rag_server._format_results(results)
    except Exception as e:
        logger.error(f"QA search failed: {e}")
        return f"Search failed: {str(e)}"

@mcp.tool
def search_semantic_similarity(query: str, top_k: int = 3) -> str:
    """Search based on semantic similarity"""
    try:
        model = MODELS["semantic"]
        task  = TASKS["semantic"]
        
        logger.debug(f"Semantic search query: {query}")
        logger.debug(f"Using model: {model.model}, task: {task.name}, top_k: {top_k}")

        query_embedding = rag_server._get_embedding(query, model)
        results = rag_server._search_database(query_embedding, model, task, top_k)
        
        logger.debug(f"Semantic search results: {results}")

        return rag_server._format_results(results)
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return f"Search failed: {str(e)}"

if __name__ == "__main__":
    mcp.run()
