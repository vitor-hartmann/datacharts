import streamlit as st
import pandas as pd
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from utils import create_presentation, generate_chart
from chat_handler import get_data_overview, chat_with_data

# Get the directory containing your script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load environment variables
load_dotenv(ENV_PATH)
api_key = os.getenv('ANTHROPIC_API_KEY')

def generate_data_stats(df):
    """Generate basic data quality statistics"""
    stats = {
        "Total Rows": len(df),
        "Total Columns": len(df.columns),
        "Missing Values": df.isnull().sum().sum(),
        "Duplicate Rows": df.duplicated().sum(),
        "Memory Usage": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
    }
    return stats

def main():
    st.set_page_config(page_title="Data Analysis Assistant", layout="wide")
    
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar setup
    with st.sidebar:
        # API key validation
        if not api_key:
            st.error("API key not found!")
            st.stop()
        elif not api_key.startswith('sk-ant'):
            st.error("Invalid API key format!")
            st.stop()
        else:
            st.success("API key valid ✓")
        
        st.divider()
        
        # File upload section
        st.header("Upload Data")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        # Display data preview and stats in sidebar if file is uploaded
        if uploaded_file is not None:
            # Load data if not already in session state
            if 'df' not in st.session_state or st.session_state.uploaded_file != uploaded_file:
                st.session_state.df = pd.read_csv(uploaded_file)
                st.session_state.uploaded_file = uploaded_file
                st.session_state.stats = generate_data_stats(st.session_state.df)
            
            st.divider()
            
            # Data Preview in sidebar
            st.header("Data Preview")
            st.dataframe(st.session_state.df.head(), use_container_width=True)
            
            st.divider()
            
            # Statistics in sidebar
            st.header("Data Quality Statistics")
            for metric, value in st.session_state.stats.items():
                st.metric(metric, value)

    # Main content area
    if 'df' in st.session_state:
        # Add tabs for different sections
        main_tab, logs_tab = st.tabs(["Analysis", "LLM Logs"])
        
        with main_tab:
            st.title("Interactive Data Analysis")
            
            # Suggested prompts section
            st.subheader("Suggested Prompts")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Data Overview"):
                    prompt = "Give me an overview of this dataset"
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    # Get AI response
                    response, chart = chat_with_data(prompt, st.session_state.df)
                    message = {"role": "assistant", "content": response}
                    if chart:
                        message["chart"] = chart
                    st.session_state.messages.append(message)
                    
            with col2:
                if st.button("📈 Show Key Trends"):
                    prompt = "What are the key trends in this data?"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    response, chart = chat_with_data(prompt, st.session_state.df)
                    message = {"role": "assistant", "content": response}
                    if chart:
                        message["chart"] = chart
                    st.session_state.messages.append(message)
                    
            with col3:
                if st.button("🔍 Data Quality Issues"):
                    prompt = "What are the main data quality issues?"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    response, chart = chat_with_data(prompt, st.session_state.df)
                    message = {"role": "assistant", "content": response}
                    if chart:
                        message["chart"] = chart
                    st.session_state.messages.append(message)
                
            st.divider()
            
            # Chat interface
            st.subheader("Chat with your Data")
            
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    if "chart" in message:
                        st.plotly_chart(message["chart"], use_container_width=True)

            # Chat input
            if prompt := st.chat_input("Ask questions about your data"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)

                # Get AI response
                with st.chat_message("assistant"):
                    response, chart = chat_with_data(prompt, st.session_state.df)
                    message = {"role": "assistant", "content": response}
                    if chart:
                        message["chart"] = chart
                        st.plotly_chart(chart, use_container_width=True)
                    st.session_state.messages.append(message)

            # Export to PowerPoint
            if st.session_state.messages:
                if st.button("Export to PowerPoint"):
                    pptx_path = create_presentation(st.session_state.messages)
                    with open(pptx_path, "rb") as file:
                        st.download_button(
                            label="Download Presentation",
                            data=file,
                            file_name="data_analysis.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )

        with logs_tab:
            st.title("LLM Interaction Logs")
            
            if "llm_logs" in st.session_state and st.session_state.llm_logs:
                for log in st.session_state.llm_logs:
                    with st.expander(f"🕒 {log['timestamp']} - {log['prompt'][:50]}..."):
                        st.markdown("### Prompt")
                        st.code(log['prompt'])
                        
                        st.markdown("### Response")
                        st.code(log['response'])
                        
                        if log['chart_specs']:
                            st.markdown("### Chart Specifications")
                            st.json(log['chart_specs'])
                        
                        st.divider()
            else:
                st.info("No logs available yet. Start chatting with your data to see the interaction logs!")
            
            # Add button to clear logs
            if st.button("Clear Logs"):
                st.session_state.llm_logs = []
                st.rerun()

if __name__ == "__main__":
    main()