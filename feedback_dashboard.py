import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import time
import requests
import numpy as np
from collections import Counter
import os
import sys

# Add parent directory to path for config access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.config import config

# Set page configuration
st.set_page_config(
    page_title="GoAssist - Feedback Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .positive-metric {
        border-left-color: #28a745;
    }
    .negative-metric {
        border-left-color: #dc3545;
    }
    .neutral-metric {
        border-left-color: #ffc107;
    }
    .sidebar-content {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .update-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_feedback_data():
    """Load feedback data from database with better error handling"""
    
    try:
        api_url = f"http://localhost:8000/chat/feedback/list"
        feedback_resp = requests.get(api_url, timeout=30)

        df = pd.DataFrame(feedback_resp.json())

        if df.empty:
            return pd.DataFrame()
        
        # Process JSON fields with better error handling
        def parse_json_safely(field):
            try:
                if pd.isna(field) or field is None or field == '':
                    return []
                if isinstance(field, str):
                    return json.loads(field)
                return []
            except (json.JSONDecodeError, TypeError):
                return []

        df['liked_aspects_list'] = df['liked_aspects'].apply(parse_json_safely)
        df['issues_list'] = df['issues'].apply(parse_json_safely)

        # Fill NaN values for user columns
        df['username'] = df['username'].fillna('Anonymous')
        df['user_full_name'] = df['user_full_name'].fillna('Anonymous User')
        
        # Convert timestamp with error handling
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            st.warning(f"Warning: Could not parse timestamps: {str(e)}")
            df['timestamp'] = datetime.now()  # Fallback
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading feedback data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_response_data():
    """Load response data from database"""
    
    try:
        api_url = f"http://localhost:8000/chat/reponse/list"
        response_resp = requests.get(api_url, timeout=30)
        print(response_resp.json())
        df = pd.DataFrame(response_resp.json())
        
        if df.empty:
            return pd.DataFrame()
        
        if not df.empty:
            df['query_time'] = pd.to_datetime(df['query_time'])
            # Fill NaN values for user columns
            df['username'] = df['username'].fillna('Anonymous')
            df['user_full_name'] = df['user_full_name'].fillna('Anonymous User')
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading response data: {str(e)}")
        return pd.DataFrame()

def create_overview_metrics(df):
    """Create overview metrics cards"""
    if df.empty:
        st.warning("📊 No feedback data available")
        return
    
    # Calculate metrics
    total_feedback = len(df)
    positive_feedback = len(df[df['feedback_type'] == 'positive'])
    negative_feedback = len(df[df['feedback_type'] == 'negative'])
    avg_rating = df['rating'].mean() if not df['rating'].isna().all() else 0
    
    # Recent feedback (last 24 hours)
    recent_cutoff = datetime.now() - timedelta(hours=24)
    recent_feedback = len(df[df['timestamp'] > recent_cutoff])
    
    # Recommendation rate
    recommend_yes = len(df[df['recommend'] == 'Yes'])
    recommend_rate = (recommend_yes / total_feedback * 100) if total_feedback > 0 else 0
    
    # Display metrics in columns
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Feedback", total_feedback, delta=f"+{recent_feedback} (24h)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container positive-metric">', unsafe_allow_html=True)
        st.metric("Positive", positive_feedback, 
                 delta=f"{positive_feedback/total_feedback*100:.1f}%" if total_feedback > 0 else "0%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container negative-metric">', unsafe_allow_html=True)
        st.metric("Negative", negative_feedback,
                 delta=f"{negative_feedback/total_feedback*100:.1f}%" if total_feedback > 0 else "0%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container neutral-metric">', unsafe_allow_html=True)
        st.metric("Avg Rating", f"{avg_rating:.1f}/10", 
                 delta="⭐" if avg_rating >= 7 else "⚠️" if avg_rating >= 5 else "❌")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Recommend Rate", f"{recommend_rate:.1f}%",
                 delta="👍" if recommend_rate >= 70 else "👎")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col6:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("24h Activity", recent_feedback,
                 delta="Active" if recent_feedback > 0 else "Quiet")
        st.markdown('</div>', unsafe_allow_html=True)

def create_feedback_trends(df):
    """Create feedback trends over time"""
    if df.empty:
        st.warning("No data available for feedback trends")
        return
    
    st.subheader("📈 Feedback Trends Over Time")
    
    try:
        # Group by date
        df['date'] = df['timestamp'].dt.date
        daily_feedback = df.groupby(['date', 'feedback_type']).size().reset_index(name='count')
        
        if daily_feedback.empty:
            st.info("No feedback trends data available")
            return
        
        # Create trend chart
        fig = px.line(daily_feedback, x='date', y='count', color='feedback_type',
                      title="Daily Feedback Trends",
                      color_discrete_map={'positive': '#28a745', 'negative': '#dc3545'})
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Feedback",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating feedback trends: {str(e)}")

def create_rating_distribution(df):
    """Create rating distribution charts"""
    if df.empty or df['rating'].isna().all():
        st.warning("No rating data available")
        return
    
    st.subheader("⭐ Rating Distribution")
    
    col1, col2 = st.columns(2)
    
    try:
        with col1:
            # Rating histogram
            fig_hist = px.histogram(df, x='rating', nbins=10, 
                                   title="Rating Distribution",
                                   color_discrete_sequence=['#1f77b4'])
            fig_hist.update_layout(
                xaxis_title="Rating (1-10)",
                yaxis_title="Frequency",
                height=400
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Rating by feedback type
            fig_box = px.box(df, x='feedback_type', y='rating',
                            title="Rating by Feedback Type",
                            color='feedback_type',
                            color_discrete_map={'positive': '#28a745', 'negative': '#dc3545'})
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating rating distribution: {str(e)}")

def create_feedback_breakdown(df):
    """Create feedback type breakdown"""
    if df.empty:
        st.warning("No data available for feedback breakdown")
        return
    
    st.subheader("🔍 Feedback Breakdown")
    
    col1, col2 = st.columns(2)
    
    try:
        with col1:
            # Pie chart for feedback types
            feedback_counts = df['feedback_type'].value_counts()
            if not feedback_counts.empty:
                fig_pie = px.pie(values=feedback_counts.values, names=feedback_counts.index,
                                title="Feedback Type Distribution",
                                color_discrete_map={'positive': '#28a745', 'negative': '#dc3545'})
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No feedback type data available")
        
        with col2:
            # Recommendation breakdown
            recommend_counts = df['recommend'].value_counts()
            if not recommend_counts.empty:
                fig_rec = px.bar(x=recommend_counts.index, y=recommend_counts.values,
                                title="Recommendation Breakdown",
                                color=recommend_counts.index,
                                color_discrete_map={'Yes': '#28a745', 'No': '#dc3545'})
                fig_rec.update_layout(
                    xaxis_title="Would Recommend",
                    yaxis_title="Count",
                    showlegend=False
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            else:
                st.info("No recommendation data available")
    except Exception as e:
        st.error(f"Error creating feedback breakdown: {str(e)}")

def create_word_analysis(df):
    """Create word analysis for feedback"""
    if df.empty:
        st.warning("No data available for word analysis")
        return
    
    st.subheader("📝 Feedback Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Most Liked Aspects (Positive Feedback)**")
        positive_df = df[df['feedback_type'] == 'positive']
        if not positive_df.empty:
            all_aspects = []
            for aspects_list in positive_df['liked_aspects_list']:
                all_aspects.extend(aspects_list)
            
            if all_aspects:
                aspect_counts = Counter(all_aspects)
                aspect_df = pd.DataFrame(aspect_counts.most_common(10), 
                                       columns=['Aspect', 'Count'])
                
                fig = px.bar(aspect_df, x='Count', y='Aspect', orientation='h',
                           title="Top Liked Aspects",
                           color='Count',
                           color_continuous_scale='Greens')
                fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No liked aspects data available")
        else:
            st.info("No positive feedback available")
    
    with col2:
        st.write("**Common Issues (Negative Feedback)**")
        negative_df = df[df['feedback_type'] == 'negative']
        if not negative_df.empty:
            all_issues = []
            for issues_list in negative_df['issues_list']:
                all_issues.extend(issues_list)
            
            if all_issues:
                issue_counts = Counter(all_issues)
                issue_df = pd.DataFrame(issue_counts.most_common(10), 
                                      columns=['Issue', 'Count'])
                
                fig = px.bar(issue_df, x='Count', y='Issue', orientation='h',
                           title="Top Issues",
                           color='Count',
                           color_continuous_scale='Reds')
                fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No issues data available")
        else:
            st.info("No negative feedback available")

def create_time_analysis(df):
    """Create time-based analysis"""
    if df.empty:
        st.warning("No data available for time analysis")
        return
    
    st.subheader("⏰ Time-based Analysis")
    
    col1, col2 = st.columns(2)
    
    try:
        with col1:
            # Hourly distribution
            df['hour'] = df['timestamp'].dt.hour
            hourly_feedback = df.groupby('hour').size().reset_index(name='count')
            
            fig_hourly = px.bar(hourly_feedback, x='hour', y='count',
                               title="Feedback by Hour of Day",
                               color='count',
                               color_continuous_scale='Blues')
            fig_hourly.update_layout(
                xaxis_title="Hour (24h format)",
                yaxis_title="Number of Feedback",
                height=400
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        with col2:
            # Weekly distribution
            df['weekday'] = df['timestamp'].dt.day_name()
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_feedback = df.groupby('weekday').size().reindex(weekday_order, fill_value=0).reset_index(name='count')
            
            fig_weekly = px.bar(weekly_feedback, x='weekday', y='count',
                               title="Feedback by Day of Week",
                               color='count',
                               color_continuous_scale='Oranges')
            fig_weekly.update_layout(
                xaxis_title="Day of Week",
                yaxis_title="Number of Feedback",
                height=400
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating time analysis: {str(e)}")

def create_recent_feedback_table(df):
    """Create recent feedback table"""
    if df.empty:
        st.warning("No recent feedback data available")
        return
    
    st.subheader("📋 Recent Feedback")
    
    try:
        # Show last 10 feedback entries
        recent_df = df.head(10).copy()
        
        # Format the data for display
        display_df = recent_df[['timestamp', 'username', 'feedback_type', 'rating', 'recommend']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['feedback_type'] = display_df['feedback_type'].str.title()
        
        # Add query preview
        display_df['query_preview'] = recent_df['query'].apply(
            lambda x: x[:50] + "..." if pd.notna(x) and len(str(x)) > 50 else str(x) if pd.notna(x) else "N/A"
        )
        
        # Reorder columns
        display_df = display_df[['timestamp', 'username', 'feedback_type', 'rating', 'recommend', 'query_preview']]
        display_df.columns = ['Time', 'User', 'Type', 'Rating', 'Recommend', 'Query Preview']
        
        # Style the dataframe
        def style_feedback_type(val):
            if val == 'Positive':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Negative':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        styled_df = display_df.style.applymap(style_feedback_type, subset=['Type'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    except Exception as e:
        st.error(f"Error creating recent feedback table: {str(e)}")

def create_response_analytics(response_df):
    """Create analytics for response data"""
    if response_df.empty:
        st.warning("No response data available")
        return
    
    st.subheader("🤖 Response Analytics")
    
    col1, col2 = st.columns(2)
    
    try:
        with col1:
            # Response volume over time
            response_df['date'] = response_df['query_time'].dt.date
            daily_responses = response_df.groupby('date').size().reset_index(name='count')
            
            fig = px.line(daily_responses, x='date', y='count',
                         title="Daily Response Volume",
                         color_discrete_sequence=['#ff7f0e'])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Response length distribution
            response_df['response_length'] = response_df['response'].str.len()
            
            fig = px.histogram(response_df, x='response_length',
                              title="Response Length Distribution",
                              color_discrete_sequence=['#2ca02c'])
            fig.update_layout(
                xaxis_title="Response Length (characters)",
                yaxis_title="Frequency",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating response analytics: {str(e)}")

def create_user_analytics(df):
    """Create user-based analytics"""
    if df.empty or 'username' not in df.columns:
        return
    
    st.subheader("👥 User Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User activity
        user_activity = df.groupby('username').size().sort_values(ascending=False).head(10)
        
        fig = px.bar(x=user_activity.values, y=user_activity.index, orientation='h',
                    title="Top 10 Most Active Users",
                    color=user_activity.values,
                    color_continuous_scale='Blues')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        fig.update_xaxes(title="Number of Feedback")
        fig.update_yaxes(title="Users")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average rating by user (for users with at least 3 feedback)
        user_ratings = df.groupby('username')['rating'].agg(['mean', 'count']).reset_index()
        user_ratings = user_ratings[user_ratings['count'] >= 3]  # At least 3 feedback
        user_ratings = user_ratings.sort_values('mean', ascending=False).head(10)
        
        if not user_ratings.empty:
            fig = px.bar(user_ratings, x='username', y='mean',
                        title="Average Rating by User (min 3 feedback)",
                        color='mean',
                        color_continuous_scale='RdYlGn')
            fig.update_layout(height=400)
            fig.update_xaxes(title="Users", tickangle=45)
            fig.update_yaxes(title="Average Rating")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for user rating analysis")

def main():
    """Main dashboard function"""
    # Header
    st.markdown('<h1 class="main-header">📊 GoAssist Feedback Analytics Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Add auto-refresh
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Load data first to get user list
    with st.spinner("📊 Loading feedback data..."):
        df = load_feedback_data()
        response_df = load_response_data()
    
    # Sidebar filters
    st.sidebar.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.sidebar.header("🎛️ Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )
    
    # User filter - Fixed: Only show if data exists
    selected_users = ['All Users']  # Default
    if not df.empty and 'username' in df.columns:
        unique_users = ['All Users'] + sorted(df['username'].dropna().unique().tolist())
        selected_users = st.sidebar.multiselect(
            "Select Users",
            options=unique_users,
            default=['All Users']
        )

    # Feedback type filter
    feedback_types = st.sidebar.multiselect(
        "Feedback Type",
        options=['positive', 'negative'],
        default=['positive', 'negative']
    )
    
    # Rating range filter
    rating_range = st.sidebar.slider(
        "Rating Range",
        min_value=1,
        max_value=10,
        value=(1, 10)
    )
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Check if data loaded successfully
    if df.empty:
        st.warning("⚠️ No feedback data found.")
        st.info("💡 This could mean:")
        st.info("- No feedback has been submitted yet")
        st.info("- Database connection issues")
        st.info("- Table 'ai_assistant_feedback' doesn't exist or is empty")
        
        # Still show the interface even with no data
        st.subheader("📊 Dashboard Interface")
        st.write("The dashboard is ready to display data once feedback is submitted.")
        return
    
    # Apply filters with proper error handling
    try:
        filtered_df = df.copy()
        
        # Apply date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[(filtered_df['timestamp'].dt.date >= start_date) & 
                        (filtered_df['timestamp'].dt.date <= end_date)]
        
        # Apply user filter - Fixed logic
        if 'All Users' not in selected_users and selected_users:
            filtered_df = filtered_df[filtered_df['username'].isin(selected_users)]
        
        # Apply feedback type filter
        if feedback_types:
            filtered_df = filtered_df[filtered_df['feedback_type'].isin(feedback_types)]
        
        # Apply rating filter with safety check
        if not filtered_df['rating'].isna().all():
            filtered_df = filtered_df[(filtered_df['rating'] >= rating_range[0]) & 
                                    (filtered_df['rating'] <= rating_range[1])]
    
    except Exception as filter_error:
        st.error(f"Error applying filters: {str(filter_error)}")
        filtered_df = df  # Use unfiltered data as fallback
    
    # Check if any data remains after filtering
    if filtered_df.empty:
        st.warning("⚠️ No data matches the current filters. Try adjusting your filter criteria.")
        return
    
    # Show update indicator
    st.markdown(
        f'<div class="update-indicator">Last updated: {datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True
    )
    
    # Show filter summary
    st.info(f"📊 Showing {len(filtered_df)} records out of {len(df)} total feedback entries")
    
    # Create dashboard sections with the filtered data
    try:
        create_overview_metrics(filtered_df)
        st.markdown("---")
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            create_feedback_trends(filtered_df)
        
        with col2:
            create_feedback_breakdown(filtered_df)
        
        st.markdown("---")
        create_rating_distribution(filtered_df)
        st.markdown("---")
        create_word_analysis(filtered_df)
        st.markdown("---")
        create_time_analysis(filtered_df)
        st.markdown("---")
        create_user_analytics(filtered_df)
        st.markdown("---")
        create_response_analytics(response_df)
        st.markdown("---")
        create_recent_feedback_table(filtered_df)
        
    except Exception as viz_error:
        st.error(f"Error creating visualizations: {str(viz_error)}")
        st.write("Raw data preview:")
        st.dataframe(filtered_df.head())
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 GoAssist Feedback Analytics Dashboard | 
            Real-time insights into user feedback | 
            Last updated: {}
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()