import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Page configuration
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# ✨ YOUR NEW PUBLIC BACKEND URL! ✨
# ==============================================================================
# This is the magic link that connects your frontend to your backend on the cloud.
BACKEND_URL = "https://expense-analyzer-49v9.onrender.com"
# ==============================================================================


# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">💰 Expense Analyzer 🚀</h1>', unsafe_allow_html=True)

# Initialize session state
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False

# Predefined categories
PREDEFINED_CATEGORIES = [
    'Groceries', 'Utilities', 'Rent', 'Entertainment', 'Transportation',
    'Dining', 'Shopping', 'Healthcare', 'Education', 'Insurance',
    'Investment', 'Travel', 'Personal Care', 'Home & Garden', 'Other'
]

# File upload and Sample Data section using Tabs
st.header("📂 Step 1: Let's Get Your Data!")
st.info("👋 Welcome aboard! Let's get started. Feed me your CSV file, or take the sample data for a spin to see the magic happen! ✨")
tab1, tab2 = st.tabs(["📤 Upload Your CSV", "🔬 Use Sample Data"])

with tab1:
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload your bank statement CSV file",
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        st.success(f"✅ Great! File uploaded: {uploaded_file.name}")
        if st.button("🚀 Launch Smart Analysis!", type="primary"):
            with st.spinner("Analyzing your data... 🧙‍♂️"):
                files = {'file': uploaded_file}
                try:
                    # We now use the public BACKEND_URL for the API call
                    response = requests.post(f"{BACKEND_URL}/api/upload_csv", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        st.info(f"📊 Processed {result['total_transactions']} transactions")
                        st.session_state.data_updated = True
                        st.rerun()
                    else:
                        st.error(f"❌ Error processing file: {response.json().get('error', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection Error: Could not connect to the backend server. Please ensure the URL is correct and the server is running.")

with tab2:
    st.info("👇 Feeling curious? Click the button below to analyze our pre-loaded sample dataset and see what this app can do!")
    if st.button("Analyze Sample Data"):
        with st.spinner("Processing sample data... 🧪"):
            try:
                # This button now tries to fetch sample data from the backend
                # You would need to add an endpoint like /api/sample_data to your backend for this to work
                response = requests.get(f"{BACKEND_URL}/api/get_sample_data") # Example endpoint
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    st.info(f"📊 Processed {result['total_transactions']} transactions from the sample data.")
                    st.session_state.data_updated = True
                    st.rerun()
                else:
                    st.error(f"❌ Could not load sample data from the backend.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Could not connect to the backend server.")


# Main analysis section
if st.session_state.data_updated or st.button("🔄 Refresh Data"):
    st.header("📊 Your Financial Dashboard")
    st.info("Welcome to your command center! 🚀 Here's the 30,000-foot view of your money—total transactions, net flow, expenses, and sweet, sweet income.")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/get_transactions")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            if not df.empty:
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df.dropna(subset=['Date', 'Amount'], inplace=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Total Transactions 🧾", len(df))
                with col2: st.metric("Net Amount ↔️", f"₹{df['Amount'].sum():,.2f}")
                with col3: st.metric("Total Expenses 💸", f"₹{abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")
                with col4: st.metric("Total Income 💰", f"₹{df[df['Amount'] > 0]['Amount'].sum():,.2f}")

                st.subheader("📈 Where's The Money Going? (Category Analysis) 🍰")
                st.info("Time to slice and dice! 🍕 These charts are your financial magnifying glass, showing you exactly which categories are eating up your cash.")
                summary_response = requests.get(f"{BACKEND_URL}/api/get_expense_summary")
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    if summary_data:
                        category_df = pd.DataFrame(summary_data)
                        total_expense = category_df['Amount'].sum()
                        category_df['Percentage'] = (category_df['Amount'] / total_expense * 100).round(1) if total_expense > 0 else 0
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_pie = px.pie(category_df, values='Amount', names='Category', title='Expense Distribution by Category')
                            st.plotly_chart(fig_pie, use_container_width=True)
                        with col2:
                            fig_bar = px.bar(category_df, x='Category', y='Amount', title='Expense Amount by Category', color='Amount', color_continuous_scale='viridis')
                            fig_bar.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_bar, use_container_width=True)
                        
                        st.subheader("📋 The Nitty-Gritty: Category Details")
                        st.info("For the data lovers! This table gives you the full story on each category, with exact totals and percentages.")
                        category_df['Amount (₹)'] = category_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                        category_df['Percentage'] = category_df['Percentage'].apply(lambda x: f"{x:.1f}%")
                        display_cols = ['Category', 'Amount (₹)', 'Percentage', 'Transaction_Count']
                        st.dataframe(category_df[display_cols], use_container_width=True, hide_index=True)

                st.header("✍️ You're the Boss: Manual Categorization")
                st.info("Our AI did its best, but some things are a mystery! 🛸 Help us out by sorting any uncategorized transactions here. You can even create your own cool categories!")
                other_response = requests.get(f"{BACKEND_URL}/api/get_other_transactions")
                if other_response.status_code == 200:
                    other_data = other_response.json()
                    other_df = pd.DataFrame(other_data) if other_data else pd.DataFrame()
                    if other_df.empty:
                        st.success("✅ Woohoo! All transactions have been categorized!")
                    else:
                        st.write(f"📊 Found {len(other_df)} uncategorized transactions to sort.")
                        other_display = other_df.copy()
                        if 'Amount' in other_display.columns:
                            other_display['Amount (₹)'] = other_display['Amount'].apply(lambda x: f"₹{x:,.2f}")
                        display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
                        available_cols = [col for col in display_cols if col in other_display.columns]
                        st.dataframe(other_display[available_cols], use_container_width=True, hide_index=True)
                        st.subheader("📝 Update a Transaction")
                        cat_tab1, cat_tab2 = st.tabs(["🔄 Quick Categorization", "➕ Add Custom Category"])
                        with cat_tab1:
                            with st.form("categorize_form"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    transaction_options = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                                    selected_transaction_index = st.selectbox("Select Transaction to Categorize", options=range(len(transaction_options)), format_func=lambda x: transaction_options[x], help="Choose one of the uncategorized transactions from the list above.")
                                    selected_id = other_df.iloc[selected_transaction_index]['id']
                                with col2:
                                    new_category = st.selectbox("Select Category", options=PREDEFINED_CATEGORIES, help="Assign the transaction to one of the standard categories.")
                                    custom_description = st.text_input("Custom Description (optional)", help="You can give this transaction a new name if you want.", placeholder="e.g., 'Medical checkup'")
                                submitted = st.form_submit_button("🔄 Update Category", type="primary")
                                if submitted:
                                    update_data = {'id': int(selected_id), 'category': new_category, 'custom_name': custom_description}
                                    update_response = requests.post(f"{BACKEND_URL}/api/update_category", json=update_data)
                                    if update_response.status_code == 200:
                                        st.success(f"✅ Updated transaction ID {selected_id}.")
                                        st.session_state.data_updated = True
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to update category.")
                        with cat_tab2:
                            with st.form("custom_category_form"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    transaction_options_custom = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                                    selected_transaction_custom_index = st.selectbox("Select Transaction for Custom Category", options=range(len(transaction_options_custom)), format_func=lambda x: transaction_options_custom[x], key="custom_transaction_select", help="Choose the transaction you want to create a new category for.")
                                    selected_id_custom = other_df.iloc[selected_transaction_custom_index]['id']
                                    custom_category_name = st.text_input("Custom Category Name", help="Enter a name for your new custom category.", placeholder="e.g., 'Pet Care'")
                                with col2:
                                    keywords_input = st.text_area("Keywords (one per line)", help="Enter keywords to automatically assign similar transactions to this new category in the future.", placeholder="APOLLO\nMEDICAL")
                                submitted_custom = st.form_submit_button("➕ Add Custom Category", type="primary")
                                if submitted_custom:
                                    if not custom_category_name:
                                        st.error("❌ Please enter a custom category name")
                                    else:
                                        keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
                                        custom_data = {'id': int(selected_id_custom), 'custom_category': custom_category_name, 'description_keywords': keywords}
                                        custom_response = requests.post(f"{BACKEND_URL}/api/add_custom_category", json=custom_data)
                                        if custom_response.status_code == 200:
                                            st.success(custom_response.json()['message'])
                                            st.session_state.data_updated = True
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Failed to add custom category.")

                st.title("🔎 Filter & Find Transactions")
                st.info("Be a detective! 🕵️‍♀️ Use the filters below to drill down into your data and find specific transactions.")
                if 'Category' in df.columns:
                    selected_category = st.selectbox("Select Category", ['All'] + sorted(df['Category'].unique()), help="Filter all transactions by a specific category.")
                    selected_name = st.selectbox("Select Name", ['All'] + sorted(df['Description'].unique()), help="Filter all transactions by a specific merchant or description.")
                    filtered_df = df.copy()
                    if selected_category != 'All':
                        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
                    if selected_name != 'All':
                        filtered_df = filtered_df[filtered_df['Description'] == selected_name]
                    st.write("Filtered Data:")
                    display_filtered_df = filtered_df.copy()
                    display_filtered_df['Amount (₹)'] = display_filtered_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                    desired_cols = ['id', 'custom_name', 'Date', 'Category', 'Description', 'Amount (₹)']
                    available_cols = [col for col in desired_cols if col in display_filtered_df.columns]
                    st.dataframe(display_filtered_df[available_cols], use_container_width=True, hide_index=True)
                    if not filtered_df.empty:
                        st.write(f"💰 **Total Amount after filters:** ₹{filtered_df['Amount'].sum():,.2f}")

                st.subheader("📜 The Master List: All Transactions")
                st.info("Behold! Every single transaction from your statement, in all its glory. Nothing hidden, everything in one place.")
                display_df = df.copy()
                display_df['Amount (₹)'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
                available_cols = [col for col in display_cols if col in display_df.columns]
                st.dataframe(display_df[available_cols], use_container_width=True, hide_index=True)
                
                st.header("✨ Level Up: Deep Dive Analysis")
                st.info("Ready to go pro? This is where we get super detailed and uncover the real secrets of your spending habits. 🤓")

                expenses_df = df[df['Amount'] < 0].copy()
                expenses_df['Amount'] = expenses_df['Amount'].abs()

                st.title("📸 Your Financial Selfie: Monthly Snapshot")
                st.info("Say cheese! Here's a quick picture of your income, spending, investments, and savings for the month.")
                total_income = df[df['Amount'] > 0]['Amount'].sum()
                total_spent = expenses_df['Amount'].sum()
                total_invested = expenses_df[expenses_df['Category'] == 'Investment']['Amount'].sum()
                net_savings = total_income - total_spent
                st.write(f"**Total Money Received:** ₹{total_income:,.2f}")
                st.write(f"**Total Money Spent:** ₹{total_spent:,.2f}")
                st.write(f"**Total Money Invested:** ₹{total_invested:,.2f}")
                st.write(f"**Amount Saved:** ₹{net_savings:,.2f}")

                st.title("🤑 Money In")
                st.info("A list of all transactions where you received money. Ka-ching! 💵")
                income_display_df = df[df['Amount'] > 0][['Date', 'Description', 'Amount', 'Category']].copy()
                income_display_df['Amount'] = income_display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(income_display_df, use_container_width=True, hide_index=True)

                st.title('📊 Category Spending Ranked')
                st.info("This bar chart ranks your spending categories from highest to lowest. What's taking the top spot?")
                category_wise_sum = expenses_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
                st.write(category_wise_sum)
                st.bar_chart(category_wise_sum)

                st.title('🍔 Daily Spending on Dining')
                st.info("This line chart tracks your spending on 'Dining'. Are you spending more on weekends? 🍕")
                dining_df = df[df["Category"] == "Dining"].copy()
                
                if not dining_df.empty:
                    dining_df['Amount'] = dining_df['Amount'].abs()
                    daily_spending_food = dining_df.groupby(dining_df['Date'].dt.date)['Amount'].sum()
                    st.write(daily_spending_food)
                    st.line_chart(daily_spending_food)
                else:
                    st.info("No spending recorded in 'Dining' category for this period.")
                
                st.title('🍰 Top Categories (Pie Chart)')
                st.info("Here's a pie chart showing the percentage breakdown of your top 8 spending categories.")
                category_sort = category_wise_sum[category_wise_sum > 0].nlargest(8)
                if not category_sort.empty:
                    st.write("Top 8 Categories:")
                    st.write(category_sort)
                    fig1, ax1 = plt.subplots()
                    wedges, texts, autotexts = ax1.pie(category_sort, autopct='%1.1f%%', startangle=90, textprops=dict(color="w"))
                    ax1.axis('equal')
                    ax1.legend(wedges, category_sort.index, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                    plt.setp(autotexts, size=10, weight="bold")
                    st.pyplot(fig1)
                
                st.title('🛍️ Top Merchants Ranked')
                st.info("This bar chart shows the top 15 specific merchants or people you pay most often.")
                name_wise_amount = expenses_df.groupby("Description")["Amount"].sum().sort_values(ascending=False)
                name_sort_top15 = name_wise_amount.nlargest(15)
                st.write(name_sort_top15)
                st.bar_chart(name_sort_top15)
                
                st.title("🎯 Top Merchants (Pie Chart)")
                st.info("A pie chart showing the percentage breakdown of your top 7 merchants or recipients.")
                name_sort_top7 = name_wise_amount[name_wise_amount > 0].nlargest(7)
                if not name_sort_top7.empty:
                    st.write("Top 7 Spenders:")
                    st.write(name_sort_top7)
                    fig2, ax2 = plt.subplots()
                    ax2.pie(name_sort_top7, labels=name_sort_top7.index, autopct='%1.1f%%', startangle=90)
                    ax2.axis('equal')
                    st.pyplot(fig2)
                
                st.title("📉 Daily Expense Tracker")
                st.info("This line chart shows the rhythm of your total daily spending. Spikes can mean big purchases or bill payments!")
                daily_expenses = expenses_df.groupby(expenses_df['Date'].dt.date)['Amount'].sum()
                st.write(daily_expenses)
                st.line_chart(daily_expenses)

            else:
                st.info("Awaiting data to display analysis.")
        else:
            st.error("Failed to retrieve transactions.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Sidebar Info
st.sidebar.header("ℹ️ Information")
st.sidebar.info("""
**Simple Expense Analyzer Features:**
- 📁 Upload CSV bank statements
- 🏷️ Smart expense categorization
- 📊 Financial overview & analysis
- ✏️ Manual category correction
- ➕ Custom category creation
- 🔄 Real-time data processing
""")
st.sidebar.header("📋 Instructions")
st.sidebar.markdown("""
1. **Upload** your bank statement CSV file
2. **Click** 'Launch Smart Analysis' to process
3. **Review** the financial overview
4. **Use Manual Categorization** for uncategorized transactions
5. **Explore** the detailed analysis and graphs
""")
st.sidebar.header("🔧 CSV Format Support")
st.sidebar.info("""
**Format 1:** Standard  
- Date, Description, Amount  
**Format 2:** Bank Statement  
- Date, Narration, Withdrawal Amt., Deposit Amt.  
**Note:** The app handles both formats automatically.
""")
