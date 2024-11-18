from utils import generate_chart
from dotenv import load_dotenv
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import re  # Add this import for text cleaning
import requests  # Add this import
import os  # Add this import
import json  # Add this import

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_oauth_token():
    """Get OAuth token for Mulesoft API"""
    try:
        response = requests.post(
            os.getenv('OAUTH_TOKEN_URL'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'client_credentials',
                'client_id': os.getenv('OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('OAUTH_CLIENT_SECRET')
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        logger.error(f"Error getting OAuth token: {str(e)}")
        raise

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
    """Get an overview of the dataset using Mulesoft API"""
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
        # Get OAuth token
        access_token = get_oauth_token()

        # Prepare messages for Mulesoft API
        messages = [{"role": "user", "content": prompt}]
        
        # Make request to Mulesoft API
        response = requests.post(
            os.getenv('MULESOFT_API_URL'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Accept': '*/*'
            },
            json={
                "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "max_tokens": 500,
                "messages": messages
            }
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get('result', '')
        
        # Log the interaction
        log_interaction(prompt, response_text)
        
        return clean_response(response_text)
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
    # Initialize llm_logs in session state if it doesn't exist
    if "llm_logs" not in st.session_state:
        st.session_state.llm_logs = []
        
    # First, create case-insensitive column mapping
    column_map = {col.lower(): col for col in df.columns}
    
    system_prompt = f"""You are a data analysis assistant that helps analyze data and create visualizations.
    
    When creating visualizations, you MUST return a JSON object in your response using this exact format:
    {{"chart_type": "bar"|"line"|"scatter"|"pie"|"word_cloud", "x_column": "column_name", "y_column": "column_name", "title": "chart_title"}}
    
    For word clouds, use this format instead:
    {{"chart_type": "word_cloud", "text_column": "column_name", "title": "chart_title"}}
    
    Available chart types are:
    - "bar" for bar charts (good for categorical comparisons or counts)
    - "line" for line charts (good for trends over time)
    - "scatter" for scatter plots (good for relationship between variables)
    - "pie" for pie charts (good for showing proportions)
    - "word_cloud" for text analysis (good for visualizing frequent terms in text)
    
    Example responses:
    1. For a value-based chart: {{"chart_type": "bar", "x_column": "country", "y_column": "value", "title": "Values by Country"}}
    2. For a count-based chart: {{"chart_type": "bar", "x_column": "country", "y_column": "count", "title": "Count by Country"}}
    3. For a word cloud: {{"chart_type": "word_cloud", "text_column": "comments", "title": "Word Cloud of Comments"}}
    
    Column names are case-sensitive, here are the exact column names:
    {df.columns.tolist()}"""
    
    # Provide more context about the data
    data_context = f"""Available columns in the dataset: {df.columns.tolist()}
    Data shape: {df.shape}
    Sample data:
    {df.head().to_string()}
    """
    
    try:
        # Make request to Mulesoft API
        access_token = get_oauth_token()
        
        response = requests.post(
            os.getenv('MULESOFT_API_URL'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Accept': '*/*'
            },
            json={
                "model": "anthropic.claude-3-sonnet-v1:0",
                "max_tokens": 1000,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{data_context}\n\nUser request: {prompt}"}
                ]
            }
        )
        response.raise_for_status()
        result = response.json()
        response_text = result.get('result', '')
        
        response_text = clean_response(response_text)
        chart = None
        chart_specs = None
        
        # Process charts and get final response
        try:
            # Look for all JSON objects in the response
            charts = []
            response_text_clean = response_text
            
            while True:
                start_idx = response_text_clean.find("{")
                if start_idx == -1:
                    break
                    
                # Find the matching closing brace
                brace_count = 1
                end_idx = start_idx + 1
                
                while brace_count > 0 and end_idx < len(response_text_clean):
                    if response_text_clean[end_idx] == '{':
                        brace_count += 1
                    elif response_text_clean[end_idx] == '}':
                        brace_count -= 1
                    end_idx += 1
                
                if brace_count == 0:
                    json_str = response_text_clean[start_idx:end_idx]
                    try:
                        chart_specs = json.loads(json_str)
                        
                        # Handle word cloud separately
                        if chart_specs.get("chart_type") == "word_cloud":
                            if "text_column" in chart_specs:
                                text_col = chart_specs["text_column"].lower()
                                if text_col in column_map:
                                    actual_text_col = column_map[text_col]
                                    chart = generate_chart(
                                        df,
                                        "word_cloud",
                                        text_column=actual_text_col,
                                        title=chart_specs["title"]
                                    )
                                    charts.append(chart)
                        else:
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
                                        charts.append(chart)
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
                                            charts.append(chart)
                    except json.JSONDecodeError:
                        continue
                    
                    # Remove the processed JSON from the text
                    response_text_clean = response_text_clean[end_idx:]
                else:
                    break
            
            # Log the interaction
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prompt": prompt,
                "response": response_text,
                "chart_specs": chart_specs
            }
            st.session_state.llm_logs.append(log_entry)
            
            # Return the response and charts
            if charts:
                return response_text, charts[0] if len(charts) == 1 else charts
            return response_text, None
            
        except Exception as e:
            error_msg = f"\n\nError generating chart: {str(e)}"
            # Log error interaction
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prompt": prompt,
                "response": response_text + error_msg,
                "chart_specs": None
            }
            st.session_state.llm_logs.append(log_entry)
            return response_text + error_msg, None
        
    except Exception as e:
        error_msg = f"Error communicating with Mulesoft API: {str(e)}"
        logger.error(error_msg)
        # Log error interaction
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": prompt,
            "response": error_msg,
            "chart_specs": None
        }
        st.session_state.llm_logs.append(log_entry)
        return error_msg, None