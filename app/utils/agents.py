from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from app.utils.tools import duckduckgo_tool, tavily_tool
from app.utils.prompts import get_classification_prompt, get_duckduckgo_prompt, get_tavily_prompt
from dotenv import load_dotenv
import os

load_dotenv()

class LLMManager:
    """Manages LLM instances for different agents"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
    def get_openai_llm(self, streaming_callback=None):
        """Get OpenAI LLM instance"""
        return ChatOpenAI(
            model="gpt-4o",
            api_key=self.openai_api_key,
            streaming=streaming_callback is not None,
            callbacks=[streaming_callback] if streaming_callback else None,
            temperature=0.1
        )
    
    def get_groq_llm(self, streaming_callback=None):
        """Get Groq LLM instance"""
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=self.groq_api_key,
            streaming=streaming_callback is not None,
            callbacks=[streaming_callback] if streaming_callback else None,
            temperature=0.1
        )

llm_manager = LLMManager()

def create_classifier_agent(streaming_callback=None):
    """Create a classifier agent for categorizing questions"""
    
    # Get LLM instance
    llm = llm_manager.get_openai_llm(streaming_callback)
    
    return Agent(
        role="Question Classifier",
        goal=get_classification_prompt(),
        backstory="""
        You are an expert question classifier with deep knowledge of educational taxonomy.
        You specialize in analyzing questions and categorizing them into specific educational categories.
        Your classifications help determine the most appropriate approach for answering different types of questions.
        
        You must analyze the user's question and classify it into one of these categories:
        - Mathematical: Calculations, equations, derivatives, integrals, numeric tasks
        - Definition: Definitions, theory, explanations, conceptual meaning
        - Formulation: Deriving or expressing formulas, using principles
        - Inferential: Inference, interpretation, logical deduction
        - Differentiation: Compare or classify two or more items
        - Analytical: Sequences, logic puzzles, arithmetic, patterns
        - Statistical: Averages, charts, probability, standard deviation
        - Inference: Drawing conclusions from given information, completing logical statements
        
        Key classification rules:
        - When the word "define" is used, classify as "Definition"
        - When the word "theory" is used, classify as "Definition" 
        - When the word "differentiate" is used, classify as "Differentiation"
        - When mathematical calculations, numbers, or equations are involved, classify as "Mathematical"
        - Be precise and follow the classification guidelines strictly
        """,
        verbose=True,
        llm=llm,
        max_iter=1,
        allow_delegation=False
    )

def create_duckduckgo_agent(streaming_callback=None):
    """Create a DuckDuckGo search agent"""
    
    # Get LLM instance
    llm = llm_manager.get_openai_llm(streaming_callback)
    
    return Agent(
        role="DuckDuckGo Search Specialist",
        goal="Search for relevant information using DuckDuckGo and provide comprehensive answers",
        backstory="""
        You are a skilled web search specialist who excels at finding relevant information using DuckDuckGo.
        You know how to craft effective search queries and interpret search results to provide accurate,
        comprehensive answers to user questions.
        
        Your approach:
        1. Analyze the user's question to understand what information is needed
        2. Craft effective search queries using DuckDuckGo
        3. Evaluate search results for relevance and accuracy
        4. Synthesize information from multiple sources
        5. Present findings in a clear, organized manner
        
        You focus on finding the most current and reliable information available through web search.
        Always cite your sources and provide links when available.
        """,
        tools=[duckduckgo_tool],
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

def create_tavily_agent(streaming_callback=None):
    """Create a Tavily search agent"""
    
    # Get LLM instance  
    llm = llm_manager.get_openai_llm(streaming_callback)
    
    return Agent(
        role="Tavily Search Specialist", 
        goal="Search for high-quality information using Tavily Search API and provide detailed insights",
        backstory="""
        You are an expert research specialist who uses Tavily's AI-powered search capabilities
        to find high-quality, relevant information for user queries.
        
        Your expertise includes:
        1. Formulating precise search queries for optimal results
        2. Leveraging Tavily's AI summarization capabilities
        3. Identifying the most credible and up-to-date sources
        4. Providing comprehensive analysis of search results
        5. Presenting information in an organized, accessible format
        
        You excel at finding detailed, accurate information and providing thorough explanations
        that help users understand complex topics. You always verify information quality and
        provide proper attribution to sources.
        """,
        tools=[tavily_tool],
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

def create_coordinator_agent(streaming_callback=None):
    """Create a coordinator agent to orchestrate the workflow"""
    
    # Get LLM instance
    llm = llm_manager.get_openai_llm(streaming_callback)
    
    return Agent(
        role="Coordinator",
        goal="Coordinate question classification and information gathering to provide comprehensive answers",
        backstory="""
        You are a master coordinator who orchestrates a team of specialists to provide
        comprehensive answers to user questions. You understand how to leverage different
        types of expertise to create complete, accurate responses.
        
        Your workflow:
        1. Analyze the user's question to understand the scope and requirements
        2. Coordinate with the classifier to determine the question category
        3. Direct search specialists to gather relevant information
        4. Synthesize all findings into a coherent, comprehensive answer
        5. Ensure the response addresses all aspects of the user's question
        
        You excel at combining different types of information and perspectives to create
        well-rounded, informative responses that fully satisfy user needs.
        """,
        verbose=True,
        llm=llm,
        allow_delegation=True
    )