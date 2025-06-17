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
                    {"role": "system", "content": "Create a 2-sentence competitive intelligence summary focusing on key business developments with a focus on marketing."},
                    {"role": "user", "content": news_text}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content
        except:
            return "Analysis temporarily unavailable."
    
    def render_competitor_card(self, company_name, ticker):
        """Render a compact competitor insight card"""
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.subheader(f"🏢 {company_name}")
                st.caption(f"Ticker: {ticker}")
            
            with col2:
                with st.spinner(f"Analyzing {company_name}..."):
                    articles = self.get_company_news(ticker, company_name)
                    summary = self.generate_brief_summary(company_name, articles)
                    st.write(summary)
                    
                    if articles:
                        st.caption(f"📰 {len(articles)} recent articles")
            
            with col3:
                if st.button("Deep Dive", key=f"dive_{company_name}"):
                    st.session_state[f"show_details_{company_name}"] = True
        
        # Show detailed view if requested
        if st.session_state.get(f"show_details_{company_name}", False):
            with st.expander(f"📊 {company_name} Detailed Analysis", expanded=True):
                articles = self.get_company_news(ticker, company_name, limit=10)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("🤖 Full AI Analysis")
                    full_summary = self.generate_full_summary(company_name, articles)
                    st.write(full_summary)
                
                with col2:
                    st.subheader("📰 Recent Headlines")
                    for article in articles[:5]:
                        st.write(f"**[{article['title']}]({article['url']})**")
                        st.caption(f"Source: {article['source']}")
                
                if st.button("Close Details", key=f"close_{company_name}"):
                    st.session_state[f"show_details_{company_name}"] = False
                    st.rerun()
    
    def generate_full_summary(self, company_name, articles):
        """Generate detailed summary for deep dive"""
        news_text = f"Recent news about {company_name}:\n\n"
        for article in articles:
            news_text += f"Title: {article['title']}\nSummary: {article['description']}\n\n"
        
        try:
            response = self.azure_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a marketing competitive intelligence analyst. Provide high level overview of business updates and their implications on marketing activity for a company."},
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