import streamlit as st
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import AzureOpenAI

# --- Competitor Intelligence Module ---
class CompetitorIntelligenceModule:
    def __init__(self):
        # Try Streamlit secrets first (for cloud deployment)
        try:
            self.alpha_vantage_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
            azure_api_key = st.secrets["AZURE_OPENAI_API_KEY"]
            azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]
        except:
            # Fall back to environment variables (for local development)
            load_dotenv()
            self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        self.azure_client = AzureOpenAI(
            api_key=azure_api_key,
            api_version="2024-02-01",
            azure_endpoint=azure_endpoint
        )
        self.competitors = {
            "Progressive": "PGR",
            "Allstate": "ALL", 
            "Travelers": "TRV",
            "Root Insurance": "ROOT",
            "Lemonade": "LMND"
        }
    
    def get_company_news(self, ticker, company_name, limit=5):
        """Fetch limited news for lightweight display"""
        try:
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={self.alpha_vantage_key}"
            response = requests.get(url)
            data = response.json()
            
            if 'feed' not in data:
                return []
            
            articles = []
            for item in data['feed'][:limit]:  # Limit articles for performance
                articles.append({
                    'title': item.get('title', 'No title'),
                    'url': item.get('url', '#'),
                    'source': item.get('source', 'Unknown'),
                    'description': item.get('summary', ''),
                })
            return articles
        except:
            return []
    
    def generate_brief_summary(self, company_name, articles):
        """Generate concise summary for landing page"""
        if not articles:
            return "No recent news available."
        
        news_text = f"Recent {company_name} news:\n"
        for article in articles[:3]:  # Only top 3 for brief summary
            news_text += f"- {article['title']}\n"
        
        try:
            response = self.azure_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Create a 2-sentence competitive intelligence summary including key business developments with a focus on potential impacts on marketing activity."},
                    {"role": "user", "content": news_text}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content
        except:
            return "Analysis temporarily unavailable."
    
    def render_competitor_card(self, company_name, ticker):
        """Render a compact competitor insight card with manual trigger"""
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.subheader(f"🏢 {company_name}")
                st.caption(f"Ticker: {ticker}")
                
                # Manual trigger button
                if st.button(f"🔄 Refresh {company_name}", key=f"refresh_{company_name}"):
                    st.session_state[f"trigger_{company_name}"] = True
            
            with col2:
                # Only fetch data if manually triggered
                if st.session_state.get(f"trigger_{company_name}", False):
                    with st.spinner(f"Analyzing {company_name}..."):
                        articles = self.get_company_news(ticker, company_name)
                        summary = self.generate_brief_summary(company_name, articles)
                        st.write(summary)
                        
                        if articles:
                            st.caption(f"📰 {len(articles)} recent articles")
                            # Store data in session state
                            st.session_state[f"data_{company_name}"] = {
                                'summary': summary,
                                'articles': articles,
                                'timestamp': datetime.now()
                            }
                else:
                    # Show cached data or prompt
                    cached_data = st.session_state.get(f"data_{company_name}")
                    if cached_data:
                        st.write(cached_data['summary'])
                        st.caption(f"📰 {len(cached_data['articles'])} articles")
                        st.caption(f"🕒 Last updated: {cached_data['timestamp'].strftime('%H:%M:%S')}")
                    else:
                        st.info("Click 'Refresh' to load latest insights")
            
            with col3:
                if st.button("Deep Dive", key=f"dive_{company_name}"):
                    st.session_state[f"show_details_{company_name}"] = True
        
        # Show detailed view if requested
        if st.session_state.get(f"show_details_{company_name}", False):
            cached_data = st.session_state.get(f"data_{company_name}")
            if cached_data:
                with st.expander(f"📊 {company_name} Detailed Analysis", expanded=True):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader("🤖 Full AI Analysis")
                        full_summary = self.generate_full_summary(company_name, cached_data['articles'])
                        st.write(full_summary)
                    
                    with col2:
                        st.subheader("📰 Recent Headlines")
                        for article in cached_data['articles'][:5]:
                            st.write(f"**[{article['title']}]({article['url']})**")
                            st.caption(f"Source: {article['source']}")
                    
                    if st.button("Close Details", key=f"close_{company_name}"):
                        st.session_state[f"show_details_{company_name}"] = False
                        st.rerun()
            else:
                st.warning("Please refresh data first before viewing details")
    
    def generate_full_summary(self, company_name, articles):
        """Generate detailed summary for deep dive"""
        news_text = f"Recent news about {company_name}:\n\n"
        for article in articles:
            news_text += f"Title: {article['title']}\nSummary: {article['description']}\n\n"
        
        try:
            response = self.azure_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a marketing competitive intelligence analyst. Provide a two sentence high level overview of business updates with a focus on shifts in business strategy. Then provide a separate two-or-three sentence overview of insights related to marketing activity, potential opportunities they may pursue to acquire customers or overall position in the marketplace in comparison to competitors. Your goal is to provide insightful snippets of information that would be relevant to a direct marketing team."},
                    {"role": "user", "content": news_text}
                ],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content
        except:
            return "Detailed analysis temporarily unavailable."
    
    def render_module(self):
        """Render the complete competitor intelligence module"""
        st.header("📈 Competitor Intelligence")
        st.markdown("*AI-powered insights on key insurance competitors*")
        
        # Add refresh all button
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("🔄 Refresh All Data", type="primary"):
                for company_name in self.competitors.keys():
                    st.session_state[f"trigger_{company_name}"] = True
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All Cache"):
                for company_name in self.competitors.keys():
                    if f"data_{company_name}" in st.session_state:
                        del st.session_state[f"data_{company_name}"]
                    if f"trigger_{company_name}" in st.session_state:
                        del st.session_state[f"trigger_{company_name}"]
                st.rerun()
        
        st.markdown("---")
        
        for company_name, ticker in self.competitors.items():
            self.render_competitor_card(company_name, ticker)
            st.markdown("---")

# --- Usage in your main Insights Agent app ---
def main():
    st.set_page_config(page_title="Insights Agent", layout="wide")
    st.title("🎯 Insights Agent Dashboard")
    
    # Initialize the competitor intelligence module
    competitor_intel = CompetitorIntelligenceModule()
    
    # Render the module as part of your larger dashboard
    competitor_intel.render_module()
    
    # Add other modules here...
    # st.header("📊 Other Insights Module")
    # st.header("📋 Another Module")

if __name__ == "__main__":
    main()