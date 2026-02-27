"""
RAG Service for StormGuard API
==============================
Retrieval Augmented Generation using LangChain and Pinecone
"""

from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from api.config import get_settings
import pinecone


logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval Augmented Generation Service
    
    Combines vector similarity search with LLM for contextual disaster predictions
    """
    
    def __init__(self):
        """Initialize RAG service with Pinecone and OpenAI"""
        self.settings = get_settings()
        self._initialize_embeddings()
        self._initialize_vectordb()
        self._initialize_llm()
        self._initialize_agent()
    
    def _initialize_embeddings(self):
        """Initialize OpenAI embeddings"""
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model="text-embedding-3-small"
            )
            logger.info("✓ OpenAI embeddings initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise
    
    def _initialize_vectordb(self):
        """Initialize Pinecone vector database"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=self.settings.PINECONE_API_KEY,
                environment=self.settings.PINECONE_ENVIRONMENT
            )
            
            # Get or create Pinecone index
            self.vectordb = Pinecone.from_existing_index(
                index_name=self.settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings
            )
            logger.info(f"✓ Pinecone index '{self.settings.PINECONE_INDEX_NAME}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            logger.warning("RAG queries will fail - ensure Pinecone is configured")
            self.vectordb = None
    
    def _initialize_llm(self):
        """Initialize ChatOpenAI language model"""
        try:
            self.llm = ChatOpenAI(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000
            )
            logger.info("✓ OpenAI LLM initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _initialize_agent(self):
        """Initialize LangChain agent with tools"""
        try:
            # Define tools for the agent
            tools = [
                Tool(
                    name="search_historical_disasters",
                    func=self._search_similar_disasters,
                    description="Search for similar past disasters in the database"
                ),
                Tool(
                    name="calculate_risk_assessment",
                    func=self._assess_risk,
                    description="Assess disaster risk based on current conditions"
                ),
                Tool(
                    name="get_preparedness_info",
                    func=self._get_preparedness,
                    description="Get disaster preparedness and safety information"
                )
            ]
            
            # Initialize memory for conversation
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create agent
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True
            )
            logger.info("✓ LangChain agent with tools initialized")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            self.agent = None
    
    def _search_similar_disasters(self, query: str) -> str:
        """
        Search for similar historical disasters
        
        Args:
            query: Search query about disaster
            
        Returns:
            Similar historical disasters context
        """
        if not self.vectordb:
            return "Vector database not available"
        
        try:
            results = self.vectordb.similarity_search(query, k=3)
            
            if not results:
                return "No similar historical disasters found"
            
            context = "Similar historical disasters:\n"
            for i, doc in enumerate(results, 1):
                context += f"{i}. {doc.page_content}\n"
            
            return context
        except Exception as e:
            logger.error(f"Error searching disasters: {e}")
            return f"Error searching: {str(e)}"
    
    def _assess_risk(self, parameters: str) -> str:
        """
        Assess disaster risk based on parameters
        
        Args:
            parameters: Risk parameters description
            
        Returns:
            Risk assessment
        """
        # This would integrate with your prediction pipeline
        # For now, return a template
        return f"Risk assessment for: {parameters} (to be integrated with prediction model)"
    
    def _get_preparedness(self, disaster_type: str) -> str:
        """
        Get preparedness information for a disaster type
        
        Args:
            disaster_type: Type of disaster
            
        Returns:
            Preparedness information
        """
        preparedness_tips = {
            "hurricane": "Evacuate if in zone, secure home, stock supplies, monitor forecasts",
            "heat_wave": "Stay hydrated, use AC, avoid outdoor activities, check on elderly",
            "flood": "Move to higher ground, don't drive through water, listen to alerts",
            "tornado": "Go to basement, interior room, avoid windows, get low to ground",
            "wildfire": "Evacuate if ordered, close windows, wear masks, have go-bag ready",
            "severe_storm": "Seek shelter, avoid open areas, don't use electronics, stay informed"
        }
        
        return preparedness_tips.get(
            disaster_type.lower(),
            f"Preparedness info for {disaster_type} not available"
        )
    
    async def query_rag(
        self,
        user_message: str,
        user_location: Tuple[float, float],
        session_id: str
    ) -> Dict:
        """
        Query the RAG system with user message
        
        Args:
            user_message: User's question or query
            user_location: (latitude, longitude) tuple
            session_id: Conversation session ID
            
        Returns:
            Dict with response, sources, and metadata
        """
        if not self.agent:
            return {
                "response": "RAG system not initialized",
                "sources": [],
                "tokens_used": 0,
                "error": True
            }
        
        try:
            # Add location context to message
            context_message = f"User location: {user_location}. Query: {user_message}"
            
            # Run agent
            result = self.agent.run(input=context_message)
            
            # Extract sources from vector search
            sources = self._extract_sources(user_message)
            
            return {
                "response": result,
                "sources": sources,
                "tokens_used": self._estimate_tokens(result),
                "error": False
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "tokens_used": 0,
                "error": True
            }
    
    def _extract_sources(self, query: str, k: int = 3) -> List[Dict]:
        """Extract source documents from similarity search"""
        if not self.vectordb:
            return []
        
        try:
            results = self.vectordb.similarity_search_with_scores(query, k=k)
            
            sources = []
            for doc, score in results:
                sources.append({
                    "content": doc.page_content[:200],  # First 200 chars
                    "similarity": float(score),
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                })
            
            return sources
        except Exception as e:
            logger.error(f"Error extracting sources: {e}")
            return []
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens used"""
        # Approximate: 1 token ≈ 4 characters
        return len(text) // 4
    
    async def embed_document(self, document: str, metadata: Dict = None) -> Dict:
        """
        Embed a document (e.g., historical disaster data)
        
        Args:
            document: Document text to embed
            metadata: Optional metadata
            
        Returns:
            Embedding result
        """
        try:
            embedding = self.embeddings.embed_query(document)
            return {
                "success": True,
                "embedding_dim": len(embedding),
                "metadata": metadata or {}
            }
        except Exception as e:
            logger.error(f"Error embedding document: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton"""
    global _rag_service
    
    if _rag_service is None:
        try:
            _rag_service = RAGService()
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            # Return a non-functional stub that won't crash
            return RAGService()
    
    return _rag_service
