import streamlit as st
import pandas as pd
import re
import asyncio
from io import BytesIO
from app.utils.ocr import extract_text_from_image
from app.utils.cordination import create_question_classifier_crew, create_simple_classifier_crew
from crewai import Task, Crew, Process
import time

def stream_response(content_text, chunk_size=20, delay=0.05):
    """Synchronous generator to yield response in chunks"""
    for i in range(0, len(content_text), chunk_size):
        yield content_text[i:i + chunk_size]
        time.sleep(delay)  # Simulate typing

def display_response(response_text, stream=False):
    """Display the response from CrewAI"""
    try:
        # Clean up the response text
        content_text = str(response_text)
        
        # Try to extract the main content if it's wrapped in extra formatting
        if "Comprehensive Answer:" in content_text:
            # Split by the comprehensive answer section
            parts = content_text.split("Comprehensive Answer:")
            if len(parts) > 1:
                content_text = "Comprehensive Answer:" + parts[1]
        
        st.markdown("### 📖 Analysis Result")
        if stream:
            placeholder = st.empty()
            displayed_text = ""
            for chunk in stream_response(content_text):
                displayed_text += chunk
                placeholder.success(displayed_text)
        else:
            st.success(content_text)
    except Exception as e:
        st.error(f"⚠️ Failed to parse and display the response: {e}")

def process_single_question_classification(question: str) -> str:
    """Process a single question for classification only"""
    try:
        # Create the classifier agent
        classifier_agent = create_simple_classifier_crew()
        
        # Create a simple classification task
        task = Task(
            description=f"""
            Classify this question: {question}
            
            Categories: Mathematical, Definition, Formulation, Inferential, 
            Differentiation, Analytical, Statistical, Inference
            
            Rules:
            - When word "define" is used, return "Definition"
            - When word "theory" is used, return "Definition" 
            - When word "differentiate" is used, return "Differentiation"
            - When mathematical calculations/numbers/equations are used, return "Mathematical"
            
            Return ONLY the category name.
            """,
            expected_output="A single category name",
            agent=classifier_agent
        )
        
        # Create a crew with the agent and task
        crew = Crew(
            agents=[classifier_agent],
            tasks=[task],
            verbose=False,  # Set to True for debugging
            process=Process.sequential
        )
        
        # Execute the crew and get result
        result = crew.kickoff()
        
        # Extract the result text
        if hasattr(result, 'raw'):
            return result.raw.strip()
        elif hasattr(result, 'result'):
            return result.result.strip()
        else:
            return str(result).strip()
            
    except Exception as e:
        return f"Classification Error: {str(e)}"

# Page Config
st.set_page_config(page_title="Question Classifier", layout="wide")

# --- Sidebar ---
st.sidebar.markdown("## 💡 Question Classifier")
st.sidebar.markdown("Analyze typed or scanned questions to get the category and explanation.")
st.sidebar.markdown("---")

upload_image = st.sidebar.file_uploader("📤 Upload an Image", type=["jpg", "jpeg", "png"], key="img_upload")
upload_excel = st.sidebar.file_uploader("📥 Upload Excel File (.xlsx)", type=["xlsx"], key="xlsx_upload")

st.title("📚 Question Prism (Question Classifier)")

st.subheader("📝 Type a Question")
question_input = st.text_input("Enter your question below:")

if st.button("Classify Question"):
    if question_input.strip() == "":
        st.warning("Please enter a valid question.")
    else:
        with st.spinner("Analyzing question..."):
            try:
                # Create the crew and process the question
                crew_instance = create_question_classifier_crew()
                response = crew_instance.run(question_input)
                
                st.success("✅ Analysis Complete!")
                display_response(response, stream=True)
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")

if upload_image is not None:
    st.subheader("🖼️ Image Classification Result")
    with st.spinner("Extracting text from image..."):
        try:
            image_bytes = upload_image.getvalue()
            extracted_text = asyncio.run(extract_text_from_image(image_bytes))

            if not extracted_text:
                st.error("❌ No text detected in the image.")
            else:
                st.success("✅ Text extracted successfully!")
                st.text_area("Extracted Text", extracted_text, height=150)

                with st.spinner("Analyzing extracted text..."):
                    try:
                        # Create the crew and process the extracted text
                        crew_instance = create_question_classifier_crew()
                        response = crew_instance.run(extracted_text)
                        
                        st.success("✅ Analysis Complete!")
                        display_response(response, stream=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error processing image: {str(e)}")

if upload_excel is not None:
    st.subheader("📊 Excel File Classification Result")
    try:
        contents = upload_excel.read()
        df = pd.read_excel(BytesIO(contents))

        # Determine which column contains questions
        if 'question' in df.columns:
            questions = df['question'].dropna().tolist()
        else:
            questions = df.iloc[:, 0].dropna().tolist()

        if not questions:
            st.error("❌ No questions found in the Excel file.")
        else:
            results = []
            progress_bar = st.progress(0)
            
            for i, question in enumerate(questions):
                try:
                    # Process each question for classification
                    category = process_single_question_classification(str(question))
                    results.append({
                        "Question": question,
                        "Category": category
                    })
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(questions))
                    
                except Exception as e:
                    results.append({
                        "Question": question,
                        "Category": f"Error: {str(e)}"
                    })

            st.success(f"✅ Classified {len(results)} questions successfully!")
            
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)
            
            # Provide download option
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="question_classifications.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ Error processing Excel file: {str(e)}")

# Add some helpful information
st.markdown("---")
st.markdown("### 📋 Classification Categories")
st.markdown("""
- **Mathematical**: Calculations, equations, derivatives, integrals, numeric tasks
- **Definition**: Definitions, theory, explanations, conceptual meaning
- **Formulation**: Deriving or expressing formulas, using principles
- **Inferential**: Inference, interpretation, logical deduction
- **Differentiation**: Compare or classify two or more items
- **Analytical**: Sequences, logic puzzles, arithmetic, patterns
- **Statistical**: Averages, charts, probability, standard deviation
- **Inference**: Drawing conclusions from given information, completing logical statements
""")

st.markdown("### 🔧 Features")
st.markdown("""
- **Text Input**: Type your question directly
- **Image Upload**: Extract text from images using OCR
- **Excel Processing**: Batch classify questions from Excel files
- **Web Search**: Get comprehensive answers using DuckDuckGo and Tavily
- **Real-time Results**: Stream responses for better user experience
""")