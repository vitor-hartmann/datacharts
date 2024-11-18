import streamlit as st

def show_logs():
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