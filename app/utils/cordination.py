from crewai import Agent, Crew, Task, Process
from app.utils.agents import (
    create_classifier_agent,
    create_duckduckgo_agent, 
    create_tavily_agent,
    create_coordinator_agent
)
import asyncio
from typing import AsyncGenerator, Optional

class QuestionClassifierCrew:
    """CrewAI implementation of the Question Classifier system"""
    
    def __init__(self, streaming_callback=None):
        self.streaming_callback = streaming_callback
        self.classifier_agent = create_classifier_agent(streaming_callback)
        self.duckduckgo_agent = create_duckduckgo_agent(streaming_callback)
        self.tavily_agent = create_tavily_agent(streaming_callback)
        self.coordinator_agent = create_coordinator_agent(streaming_callback)
        
    def create_classification_task(self, question: str) -> Task:
        """Create a task for question classification"""
        return Task(
            description=f"""
            Classify the following question into one of the predefined categories:
            
            Question: {question}
            
            Categories:
            1. Mathematical — Calculations, equations, derivatives, integrals, numeric tasks
            2. Definition — Definitions, theory, explanations, conceptual meaning  
            3. Formulation — Deriving or expressing formulas, using principles
            4. Inferential — Inference, interpretation, logical deduction
            5. Differentiation — Compare or classify two or more items
            6. Analytical — Sequences, logic puzzles, arithmetic, patterns
            7. Statistical — Averages, charts, probability, standard deviation
            8. Inference — Drawing conclusions from given information, completing logical statements
            
            Rules:
            - When word "define" is used, return only "Definition"
            - When word "theory" is used, return only "Definition"
            - When word "differentiate" is used, return only "Differentiation"
            - When mathematical calculations, numbers, or equations are used, return only "Mathematical"
            
            Respond with ONLY the category name that best fits the question.
            """,
            expected_output="A single category name from the predefined list",
            agent=self.classifier_agent
        )
    
    def create_duckduckgo_search_task(self, question: str) -> Task:
        """Create a task for DuckDuckGo search"""
        return Task(
            description=f"""
            Search for relevant information about the following question using DuckDuckGo:
            
            Question: {question}
            
            Your task:
            1. Use the DuckDuckGo search tool to find relevant information
            2. Analyze the search results for accuracy and relevance
            3. Summarize the key findings from multiple sources
            4. Provide a comprehensive answer based on the search results
            5. Include source citations and links where available
            
            Focus on finding the most current and reliable information available.
            Return a well-structured response with clear explanations.
            """,
            expected_output="Comprehensive answer based on DuckDuckGo search results with source citations",
            agent=self.duckduckgo_agent
        )
    
    def create_tavily_search_task(self, question: str) -> Task:
        """Create a task for Tavily search"""
        return Task(
            description=f"""
            Search for high-quality information about the following question using Tavily Search:
            
            Question: {question}
            
            Your task:
            1. Use the Tavily search tool to find relevant, high-quality information
            2. Leverage Tavily's AI-powered summarization capabilities
            3. Identify the most credible and up-to-date sources
            4. Provide detailed analysis and insights from the search results
            5. Present information in an organized, accessible format
            
            Focus on finding comprehensive, accurate information with proper source attribution.
            Return a detailed response with thorough explanations.
            """,
            expected_output="Detailed answer based on Tavily search results with comprehensive analysis",
            agent=self.tavily_agent
        )
    
    def create_coordination_task(self, question: str) -> Task:
        """Create a coordination task to synthesize all results"""
        return Task(
            description=f"""
            Coordinate and synthesize the results from classification and search tasks for this question:
            
            Question: {question}
            
            Your task:
            1. Review the classification result from the classifier agent
            2. Analyze the search results from both DuckDuckGo and Tavily agents
            3. Synthesize all information into a comprehensive, coherent response
            4. Ensure the answer addresses all aspects of the user's question
            5. Present the final answer in a clear, well-structured format
            
            Structure your response as follows:
            - Question Category: [Classification result]
            - Comprehensive Answer: [Synthesized information from searches]
            - Key Insights: [Important points and takeaways]
            - Sources: [References from search results]
            
            Provide a complete, accurate, and helpful response that fully satisfies the user's query.
            """,
            expected_output="A comprehensive, well-structured answer with classification, synthesis of search results, key insights, and sources",
            agent=self.coordinator_agent,
            context=[]  # Will be populated with previous tasks
        )
    
    def create_crew(self, question: str) -> Crew:
        """Create a crew for processing a question"""
        
        # Create all tasks
        classification_task = self.create_classification_task(question)
        duckduckgo_task = self.create_duckduckgo_search_task(question)
        tavily_task = self.create_tavily_search_task(question)
        coordination_task = self.create_coordination_task(question)
        
        # Set context for coordination task
        coordination_task.context = [classification_task, duckduckgo_task, tavily_task]
        
        # Create and return the crew
        return Crew(
            agents=[
                self.classifier_agent,
                self.duckduckgo_agent, 
                self.tavily_agent,
                self.coordinator_agent
            ],
            tasks=[
                classification_task,
                duckduckgo_task,
                tavily_task,
                coordination_task
            ],
            process=Process.sequential,
            verbose=True,
            output_log_file="question_classifier_crew.log"
        )
    
    def run(self, question: str) -> str:
        """Run the crew to process a question"""
        try:
            crew = self.create_crew(question)
            result = crew.kickoff()
            return result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    async def stream_run(self, question: str) -> AsyncGenerator[dict, None]:
        """Stream the crew execution for real-time updates"""
        try:
            yield {"type": "status", "message": "Starting question analysis...", "agent": "System"}
            
            crew = self.create_crew(question)
            
            # Execute the crew
            result = crew.kickoff()
            
            # Stream the final result
            final_result = result.raw if hasattr(result, 'raw') else str(result)
            
            # Stream the content in chunks for better UX
            chunk_size = 100
            for i in range(0, len(final_result), chunk_size):
                chunk = final_result[i:i+chunk_size]
                yield {
                    "type": "token",
                    "content": chunk,
                    "agent": "Coordinator"
                }
                await asyncio.sleep(0.01)  # Small delay for streaming effect
            
            yield {"type": "status", "message": "Analysis completed", "agent": "System"}
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "agent": "System"
            }

# Create a factory function for easy instantiation
def create_question_classifier_crew(streaming_callback=None) -> QuestionClassifierCrew:
    """Factory function to create a QuestionClassifierCrew instance"""
    return QuestionClassifierCrew(streaming_callback)

# Create a simple classifier-only crew for Excel processing
def create_simple_classifier_crew(streaming_callback=None) -> Crew:
    """Create a simple crew with only classification for batch processing"""
    
    classifier_agent = create_classifier_agent(streaming_callback)
    
    def create_simple_classification_task(question: str) -> Task:
        return Task(
            description=f"""
            Classify this question: {question}
            
            Return ONLY the category name from: Mathematical, Definition, Formulation, 
            Inferential, Differentiation, Analytical, Statistical, Inference
            """,
            expected_output="A single category name",
            agent=classifier_agent
        )
    
    # This will be used differently for batch processing
    return classifier_agent