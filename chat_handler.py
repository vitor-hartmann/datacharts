from anthropic import Anthropic
import os
import json
from utils import generate_chart
from dotenv import load_dotenv
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import re  # Add this import for text cleaning

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

anthropic = Anthropic(api_key=api_key)

def clean_response(response):
    """Clean the response text from ContentBlock formatting"""
    # Remove ContentBlock wrapper if present
    if isinstance(response, str):
        # Remove the ContentBlock wrapper and metadata
        cleaned = re.sub(r'\[?ContentBlock\(text=\'|\'?, type=\'text\'\)\]?', '', response)
        # Remove extra quotes if present
        cleaned = cleaned.strip('\'"')
        return cleaned
    return response

def get_data_overview(df):
    """Get an overview of the dataset using Claude"""
    data_info = {
        "columns": df.columns.tolist(),
        "sample": df.head().to_dict(),
        "info": {
            "shape": df.shape,
            "dtypes": df.dtypes.astype(str).to_dict()
        }
    }
    
    prompt = f"""Given this dataset information, provide a brief overview of what the data appears to be about:
    {json.dumps(data_info, indent=2)}
    
    Please provide a concise summary that explains the nature of the dataset and its potential use cases."""
    
    try:
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response = clean_response(str(message.content))
        # Log the interaction
        log_interaction(prompt, response)
        
        return response
    except Exception as e:
        error_msg = f"Error getting data overview: {str(e)}"
        logger.error(error_msg)
        return error_msg

def log_interaction(prompt, response, chart_specs=None):
    """Log interaction with the LLM"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "prompt": prompt,
        "response": clean_response(response),  # Clean the response in logs too
        "chart_specs": chart_specs
    }
    if "llm_logs" not in st.session_state:
        st.session_state.llm_logs = []
    st.session_state.llm_logs.append(log_entry)

def chat_with_data(prompt, df):
    """Handle chat interactions with the dataset"""
    # First, create case-insensitive column mapping
    column_map = {col.lower(): col for col in df.columns}
    
    system_prompt = """You are a data analysis assistant that helps analyze data and create visualizations.
    
    When creating visualizations, you MUST return a JSON object in your response using this exact format:
    {"chart_type": "bar"|"line"|"scatter"|"pie", "x_column": "column_name", "y_column": "column_name", "title": "chart_title"}
    
    For count-based visualizations (e.g., counting occurrences of categories), set y_column as "count".
    
    Available chart types are:
    - "bar" for bar charts (good for categorical comparisons or counts)
    - "line" for line charts (good for trends over time)
    - "scatter" for scatter plots (good for relationship between variables)
    - "pie" for pie charts (good for showing proportions)
    
    Example responses:
    1. For a value-based chart: {"chart_type": "bar", "x_column": "country", "y_column": "value", "title": "Values by Country"}
    2. For a count-based chart: {"chart_type": "bar", "x_column": "country", "y_column": "count", "title": "Count by Country"}
    3. For a pie chart: {"chart_type": "pie", "x_column": "country", "y_column": "count", "title": "Distribution of Countries"}
    
    Always include the JSON when the user asks for a chart or visualization. Column names are case-sensitive, here are the exact column names:
    {df.columns.tolist()}"""
    
    # Provide more context about the data
    data_context = f"""Available columns in the dataset: {df.columns.tolist()}
    Data shape: {df.shape}
    Sample data:
    {df.head().to_string()}
    """
    
    try:
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"{data_context}\n\nUser request: {prompt}"}
            ]
        )
        
        response = clean_response(str(message.content))
        chart = None
        chart_specs = None
        
        # Check if response contains chart specifications
        try:
            # Look for JSON in the response using a more robust method
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                chart_specs = json.loads(json_str)
                
                # Remove the JSON from the response text for cleaner output
                response = response[:start_idx].strip() + response[end_idx:].strip()
                
                # Validate required fields
                required_fields = ["chart_type", "x_column", "y_column", "title"]
                if all(field in chart_specs for field in required_fields):
                    # Try to match column names case-insensitively
                    x_col = chart_specs["x_column"].lower()
                    if x_col in column_map:
                        actual_x_col = column_map[x_col]
                        
                        # Handle count-based charts
                        if chart_specs["y_column"] == "count":
                            # Create a count-based DataFrame
                            count_df = df[actual_x_col].value_counts().reset_index()
                            count_df.columns = [actual_x_col, 'count']
                            chart = generate_chart(
                                count_df,
                                chart_specs["chart_type"],
                                actual_x_col,
                                'count',
                                chart_specs["title"]
                            )
                        else:
                            # Handle regular charts with actual y-column
                            y_col = chart_specs["y_column"].lower()
                            if y_col in column_map:
                                actual_y_col = column_map[y_col]
                                chart = generate_chart(
                                    df,
                                    chart_specs["chart_type"],
                                    actual_x_col,
                                    actual_y_col,
                                    chart_specs["title"]
                                )
                            else:
                                response += f"\n\nError: Column '{chart_specs['y_column']}' not found. Available columns: {', '.join(df.columns)}"
                    else:
                        response += f"\n\nError: Column '{chart_specs['x_column']}' not found. Available columns: {', '.join(df.columns)}"
                else:
                    response += "\n\nError: Invalid chart specification format. Missing required fields."
        except json.JSONDecodeError:
            response += "\n\nError: Could not parse chart specifications."
        except Exception as e:
            response += f"\n\nError generating chart: {str(e)}"
        
        # Log the interaction
        log_interaction(prompt, response, chart_specs)
        
        return response, chart
        
    except Exception as e:
        error_msg = f"Error communicating with Claude: {str(e)}"
        logger.error(error_msg)
        return error_msg, None