import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from utils import create_presentation, generate_chart
from chat_handler import chat_with_data
from PIL import Image
import base64

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="Data Analysis Assistant", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={} 
)

# Add CSS to hide only the menu items we want to hide
st.markdown("""
    <style>
        /* Hide main menu button and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Hide top-level navigation items */
        header {visibility: hidden;}
        
        /* Hide default page navigation */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Hide the close button and its background */
        button[kind="header"] {display: none;}
        .st-emotion-cache-r421ms {display: none;}
        .st-emotion-cache-1dp5vir {display: none;}
        
        /* Ensure sidebar content is visible */
        [data-testid="stSidebar"] {
            visibility: visible !important;
            height: 100% !important;
        }
        
        /* Ensure sidebar content is visible */
        [data-testid="stSidebarContent"] {
            visibility: visible !important;
        }
        
        /* Improve image quality */
        img {
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }
        
        /* Center logo container */
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem 0;
        }
        
        /* Style for navigation menu */
        .nav-menu {
            margin: 1rem 0;
            padding: 0.5rem 0;
            border-radius: 4px;
        }
        
        /* Style the selectbox */
        .nav-menu .stSelectbox {
            font-family: 'PfizerTomorrow', sans-serif !important;
        }
        
        .nav-menu .stSelectbox > div > div {
            padding: 0.5rem 1rem;
            cursor: pointer;
        }
        
        .nav-menu .stRadio > label {
            font-family: 'PfizerTomorrow', sans-serif !important;
            padding: 0.5rem 1rem;
            cursor: pointer;
        }
        
        .nav-menu .stRadio > label:hover {
            background-color: rgba(0, 0, 238, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Function to load and encode font file
def get_font_base64(font_path):
    if os.path.exists(font_path):
        with open(font_path, "rb") as font_file:
            return base64.b64encode(font_file.read()).decode()
    return None

# Load custom font
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, "assets", "PfizerTomorrow-regular.otf")
font_base64 = get_font_base64(font_path)

# Add custom font CSS if font was loaded successfully
if font_base64:
    st.markdown(f"""
        <style>
            @font-face {{
                font-family: 'PfizerTomorrow';
                src: url(data:font/otf;base64,{font_base64}) format('opentype');
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                font-family: 'PfizerTomorrow', sans-serif !important;
            }}
            
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
                font-family: 'PfizerTomorrow', sans-serif !important;
            }}
            
            .sidebar .sidebar-content {{
                font-family: 'PfizerTomorrow', sans-serif;
            }}
            
            .st-emotion-cache-1788y8l h1,
            .st-emotion-cache-1788y8l h2,
            .st-emotion-cache-1788y8l h3,
            .st-emotion-cache-1788y8l h4 {{
                font-family: 'PfizerTomorrow', sans-serif !important;
            }}
            
            .custom-header {{
                font-family: 'PfizerTomorrow', sans-serif !important;
                font-weight: normal;
            }}

            .blue-header {{
                color: #0000EE;
                font-size: 24px;
                margin-bottom: 20px;
                text-align: center;
            }}
        </style>
    """, unsafe_allow_html=True)

# Initialize states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "Analysis"

# Sidebar layout
with st.sidebar:
    # 2. CXI&AI Header
    st.markdown('<h1 class="blue-header">CXI&AI</h1>', unsafe_allow_html=True)
    
    # 3. Navigation Menu
    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        analysis_btn = st.button("Analysis", key="analysis_btn", use_container_width=True)
    with col2:
        logs_btn = st.button("Logs", key="logs_btn", use_container_width=True)
    
    # Update selected_page based on button clicks
    if logs_btn:
        st.session_state.current_page = "Logs"
    if analysis_btn:
        st.session_state.current_page = "Analysis"
    selected_page = st.session_state.current_page
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Add a divider
    st.divider()
    
    # 5. Rest of sidebar content based on selected page
    if selected_page == "Analysis":
        # File upload section
        st.markdown('<h2 class="custom-header">Upload Data</h2>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            # Load data if not already in session state or if new file
            if 'df' not in st.session_state or st.session_state.uploaded_file != uploaded_file:
                st.session_state.df = pd.read_csv(uploaded_file)
                st.session_state.uploaded_file = uploaded_file
                
                # Display data preview in sidebar
                st.markdown('<h3 class="custom-header">Data Preview</h3>', unsafe_allow_html=True)
                st.dataframe(st.session_state.df.head(), use_container_width=True)
                
                # Display basic statistics
                st.markdown('<h3 class="custom-header">Data Statistics</h3>', unsafe_allow_html=True)
                stats = {
                    "Total Rows": len(st.session_state.df),
                    "Total Columns": len(st.session_state.df.columns),
                    "Missing Values": st.session_state.df.isnull().sum().sum(),
                    "Duplicate Rows": st.session_state.df.duplicated().sum()
                }
                for metric, value in stats.items():
                    st.metric(metric, value)
        
        # 6. PowerPoint download section if there are messages
        if st.session_state.messages:
            st.divider()
            st.markdown('<h2 class="custom-header">Export Analysis</h2>', unsafe_allow_html=True)
            if st.button("📥 Download PowerPoint", use_container_width=True):
                with st.spinner("Creating PowerPoint presentation..."):
                    try:
                        pptx_path = create_presentation(st.session_state.messages)
                        with open(pptx_path, "rb") as file:
                            st.download_button(
                                label="📊 Download Analysis",
                                data=file,
                                file_name="data_analysis.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True
                            )
                        # Clean up the temporary file
                        os.remove(pptx_path)
                    except Exception as e:
                        st.error(f"Error creating presentation: {str(e)}")

# Main content area
if selected_page == "Analysis":
    if 'df' in st.session_state:
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"],
                avatar=os.path.join(current_dir, "assets", "pfe-icon.png") if message["role"] == "assistant" else None
            ):
                st.markdown(message["content"])
                if "chart" in message and message["chart"]:
                    if isinstance(message["chart"], list):
                        for chart in message["chart"]:
                            st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.plotly_chart(message["chart"], use_container_width=True)
        
        # React to user input
        if prompt := st.chat_input("Ask questions about your data"):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get response from Mulesoft API
            with st.chat_message(
                "assistant",
                avatar=os.path.join(current_dir, "assets", "pfe-icon.png")
            ):
                with st.spinner("Thinking..."):
                    response, charts = chat_with_data(prompt, st.session_state.df)
                    st.markdown(response)
                    if charts:
                        if isinstance(charts, list):
                            for chart in charts:
                                st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.plotly_chart(charts, use_container_width=True)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response, "chart": charts})
elif selected_page == "Logs":
    st.title("LLM Interaction Logs")
    
    if "llm_logs" in st.session_state and st.session_state.llm_logs:
        # Add clear logs button
        if st.button("🗑️ Clear Logs", use_container_width=True):
            st.session_state.llm_logs = []
            st.rerun()
        
        # Display logs in reverse chronological order
        for log in reversed(st.session_state.llm_logs):
            with st.expander(f"🕒 {log['timestamp']} - {log['prompt'][:50]}..."):
                st.markdown("### 🗣️ User Prompt")
                st.code(log['prompt'], language="markdown")
                
                st.markdown("### 🤖 Assistant Response")
                st.code(log['response'], language="markdown")
                
                if log.get('chart_specs'):
                    st.markdown("### 📊 Chart Specifications")
                    st.json(log['chart_specs'])
                
                st.divider()
    else:
        st.info("No logs available yet. Start chatting with your data to see the interaction logs!")