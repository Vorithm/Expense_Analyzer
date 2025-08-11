import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import matplotlib.pyplot as plt

# ==============================================================================
# BACKEND LOGIC (Merged into a single script to replace localhost calls)
# ==============================================================================

# Initialize session state for DataFrame and app state
if "df_global" not in st.session_state:
    st.session_state.df_global = None
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False

def categorize_transaction(description):
    """Categorize transaction based on description"""
    description = str(description).upper()
    category_map = {
        'Groceries': ['GROCERY','SUPERMARKET','FOOD','VEGETABLE','FRUIT','MILK','BREAD','RICE','DAL','OIL','SPICE','KIRANA','GENERAL STORE','BIG BAZAAR','RELIANCE FRESH','DMART','GROFERS','BIGBASKET'],
        'Utilities': ['ELECTRICITY','POWER','GAS','WATER','INTERNET','PHONE','MOBILE','BROADBAND','WIFI','UTILITY','BILL','PAYMENT','BSNL','AIRTEL','JIO','VODAFONE','IDEA','MTNL'],
        'Rent': ['RENT','HOUSE RENT','ACCOMMODATION','LEASE','RENTAL'],
        'Entertainment': ['MOVIE','CINEMA','NETFLIX','AMAZON PRIME','HOTSTAR','ENTERTAINMENT','GAME','GAMING','PLAYSTATION','XBOX','NINTENDO','BOOK','MAGAZINE','NEWSPAPER','MUSIC','SPOTIFY','YOUTUBE','STREAMING'],
        'Transportation': ['PETROL','DIESEL','FUEL','GAS','UBER','OLA','TAXI','BUS','TRAIN','METRO','PARKING','TOLL','TRANSPORT','CAB','AUTO','PETROL PUMP','HP','SHELL','BP','INDIAN OIL'],
        'Dining': ['RESTAURANT','CAFE','FOOD','MEAL','LUNCH','DINNER','BREAKFAST','SWIGGY','ZOMATO','FOODPANDA','DOMINOS','PIZZA HUT','KFC','MCDONALDS','SUBWAY','CAFETERIA','CANTEEN','HOTEL','BAR','PUB'],
        'Shopping': ['AMAZON','FLIPKART','MYNTRA','SHOPPING','PURCHASE','MALL','SHOP','RETAIL','CLOTHING','FASHION','SHOES','ELECTRONICS','APPLIANCES','FURNITURE','DECOR','LIFESTYLE','JABONG','SNAPDEAL','PAYTM MALL','TATA CLIQ','NYKAA','LENSKART'],
        'Healthcare': ['HOSPITAL','DOCTOR','MEDICAL','PHARMACY','MEDICINE','HEALTH','CLINIC','DENTAL','SURGERY','AMBULANCE','APOLLO','FORTIS','MAX HOSPITAL','MEDPLUS','NETMEDS','PRACTO','HEALTHKART'],
        'Education': ['SCHOOL','COLLEGE','UNIVERSITY','EDUCATION','TUITION','FEES','COURSE','TRAINING','BOOKS','LIBRARY','EXAM','BYJU','UNACADEMY','VEDANTU','STUDENT','ACADEMIC'],
        'Insurance': ['INSURANCE','POLICY','PREMIUM','LIC','HDFC LIFE','ICICI PRU','SBI LIFE','BAJAJ ALLIANZ','TATA AIG','RELIANCE GENERAL','HEALTH INSURANCE','MOTOR INSURANCE','TERM INSURANCE'],
        'Investment': ['MUTUAL FUND','SIP','INVESTMENT','TRADING','ZERODHA','GROWW','ANGEL BROKING','UPSTOX','PAYTM MONEY','KUVERA','STOCK','EQUITY','BOND','FD','RD','PPF','ELSS','NSE','BSE'],
        'Travel': ['IRCTC','MAKEMYTRIP','GOIBIBO','CLEARTRIP','YATRA','TRAVEL','BOOKING','HOTEL','FLIGHT','TRAIN','BUS','TICKET','VACATION','HOLIDAY','TOURISM','AIRBNB','OYO','TREEBO','REDBUS'],
        'Personal Care': ['SALON','PARLOUR','BEAUTY','COSMETICS','SKINCARE','HAIRCUT','MASSAGE','SPA','WELLNESS','FITNESS','GYM','YOGA','PERSONAL CARE','GROOMING','URBAN COMPANY','LAKME'],
        'Home & Garden': ['HOME DEPOT','GARDEN','PLANTS','NURSERY','HARDWARE','TOOLS','REPAIR','MAINTENANCE','PLUMBER','ELECTRICIAN','CARPENTER','PAINT','TILES','CEMENT','CONSTRUCTION','RENOVATION'],
    }
    for cat, keywords in category_map.items():
        if any(keyword in description for keyword in keywords):
            return cat
    return 'Other'

def backend_upload_csv(file):
    try:
        if file is None: raise ValueError("No file provided")
        df = pd.read_csv(file)
        if df.empty: raise ValueError("The uploaded CSV file is empty")
        
        if len(df) > 0 and df.iloc[0].tolist() == df.columns.tolist():
            df = df.drop(df.index[0]).reset_index(drop=True)
            
        df.columns = df.columns.astype(str).str.strip()
        
        if 'Withdrawal Amt.' in df.columns and 'Deposit Amt.' in df.columns:
            df['Withdrawal Amt.'] = pd.to_numeric(df['Withdrawal Amt.'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df['Deposit Amt.'] = pd.to_numeric(df['Deposit Amt.'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df['Amount'] = df['Deposit Amt.'] - df['Withdrawal Amt.']
            df['Description'] = df.get('Narration', 'No description').fillna("No description")
        elif 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(',', ''), errors='coerce')
            df['Description'] = df.get('Description', df.get('Narration', 'No description')).fillna("No description")
        else:
            raise ValueError("CSV must contain 'Amount' or ('Withdrawal Amt.' & 'Deposit Amt.') columns")
            
        if 'Date' not in df.columns: raise ValueError("CSV must contain a 'Date' column")
        
        df['Category'] = df['Description'].apply(categorize_transaction)
        df['custom_name'] = ''
        df = df.dropna(subset=['Amount'])
        df['id'] = range(1, len(df) + 1)
        st.session_state.df_global = df
        
        return {"message": "File processed successfully", "total_transactions": len(df)}
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")

def backend_get_transactions_df():
    return st.session_state.df_global.copy() if st.session_state.df_global is not None else pd.DataFrame()

def backend_get_other_df():
    df = backend_get_transactions_df()
    return df[df['Category'] == 'Other'].copy() if not df.empty else pd.DataFrame()

def backend_update_category(transaction_id, new_category, custom_name=""):
    df = backend_get_transactions_df()
    if df.empty: raise ValueError("No data available")
    mask = df['id'] == int(transaction_id)
    if not mask.any(): raise ValueError(f"Transaction ID {transaction_id} not found.")
    df.loc[mask, 'Category'] = new_category
    df.loc[mask, 'custom_name'] = custom_name
    st.session_state.df_global = df
    return {"message": "Category updated successfully"}

def backend_add_custom_category(transaction_id, custom_category, description_keywords=None):
    df = backend_get_transactions_df()
    if df.empty: raise ValueError("No data available")
    mask = df['id'] == int(transaction_id)
    if not mask.any(): raise ValueError(f"Transaction ID {transaction_id} not found.")
    df.loc[mask, 'Category'] = custom_category
    df.loc[mask, 'custom_name'] = custom_category
    if description_keywords:
        for keyword in description_keywords:
            if keyword:
                keyword_mask = df['Description'].str.contains(keyword, case=False, na=False)
                df.loc[keyword_mask, 'Category'] = custom_category
                df.loc[keyword_mask, 'custom_name'] = custom_category
    st.session_state.df_global = df
    return {"message": f"Custom category '{custom_category}' added successfully."}

def backend_get_expense_summary_df():
    df = backend_get_transactions_df()
    if df.empty: return pd.DataFrame()
    expenses = df[df['Amount'] < 0].copy()
    if expenses.empty: return pd.DataFrame()
    expenses['Amount'] = expenses['Amount'].abs()
    expenses['Display_Category'] = expenses.apply(lambda r: r['custom_name'] if r['custom_name'] else r['Category'], axis=1)
    summary = expenses.groupby('Display_Category').agg(Amount=('Amount', 'sum'), Transaction_Count=('id', 'count')).reset_index()
    summary.rename(columns={'Display_Category': 'Category'}, inplace=True)
    return summary.sort_values('Amount', ascending=False)

# ==============================================================================
# FRONTEND UI (Your code, with backend calls replaced)
# ==============================================================================

# Page configuration
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
st.markdown('<h1 class="main-header">💰 Expense Analyzer</h1>', unsafe_allow_html=True)

# Predefined categories
PREDEFINED_CATEGORIES = [
    'Groceries', 'Utilities', 'Rent', 'Entertainment', 'Transportation',
    'Dining', 'Shopping', 'Healthcare', 'Education', 'Insurance',
    'Investment', 'Travel', 'Personal Care', 'Home & Garden', 'Other'
]

# File upload and Sample Data section using Tabs
st.header("📁 Upload Bank Statement")
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
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        if st.button("🚀 Launch Smart Analysis", type="primary"):
            with st.spinner("Processing your data..."):
                try:
                    result = backend_upload_csv(uploaded_file)
                    st.success(f"✅ {result['message']}")
                    st.info(f"📊 Processed {result['total_transactions']} transactions")
                    st.session_state.data_updated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")

with tab2:
    st.info("👇 Feeling curious? Click the button below to analyze the pre-loaded sample dataset.")
    if st.button("Analyze Sample Data"):
        with st.spinner("Processing sample data...🧪"):
            try:
                # ===== THIS IS THE CORRECTED LINE =====
                # It now looks for the standard filename 'sample_data.csv'
                with open("sample_data.csv", "rb") as f:
                    result = backend_upload_csv(f)
                    st.success(f"✅ {result['message']}")
                    st.info(f"📊 Processed {result['total_transactions']} transactions from the sample data.")
                    st.session_state.data_updated = True
                    st.rerun()
            except FileNotFoundError:
                # The error message is now clearer
                st.error("❌ Error: sample_data.csv not found. Please make sure this file is in your project folder.")
            except Exception as e:
                st.error(f"❌ Error processing sample file: {str(e)}")


# Main analysis section (using your refresh logic)
if st.session_state.data_updated or st.button("🔄 Refresh Data"):
    st.header("📊 Financial Overview")
    
    try:
        df = backend_get_transactions_df()
        
        if not df.empty:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df.dropna(subset=['Date', 'Amount'], inplace=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Transactions", len(df))
            with col2: st.metric("Net Amount", f"₹{df['Amount'].sum():,.2f}")
            with col3: st.metric("Total Expenses", f"₹{abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")
            with col4: st.metric("Total Income", f"₹{df[df['Amount'] > 0]['Amount'].sum():,.2f}")

            st.subheader("📈 Category Analysis")
            st.info("Time to slice and dice! 🍕 These charts are your financial magnifying glass, showing you exactly which categories are eating up your cash.")
            category_df = backend_get_expense_summary_df()
            if not category_df.empty:
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
                
                st.subheader("📋 Category Details")
                st.info("For the data lovers! This table gives you the full story on each category, with exact totals and percentages.")
                category_df['Amount (₹)'] = category_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                category_df['Percentage'] = category_df['Percentage'].apply(lambda x: f"{x:.1f}%")
                display_cols = ['Category', 'Amount (₹)', 'Percentage', 'Transaction_Count']
                st.dataframe(category_df[display_cols], use_container_width=True, hide_index=True)

            st.header("✏ You're the Boss: Manual Categorization")
            other_df = backend_get_other_df()
            if other_df.empty:
                st.success("✅ Woohoo! All transactions have been categorized!")
            else:
                st.write(f"📊 Found {len(other_df)} uncategorized transactions")
                other_display = other_df.copy()
                if 'Amount' in other_display.columns:
                    other_display['Amount (₹)'] = other_display['Amount'].apply(lambda x: f"₹{abs(x):,.2f}")
                display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
                available_cols = [col for col in display_cols if col in other_display.columns]
                st.dataframe(other_display[available_cols], use_container_width=True, hide_index=True)
                
                st.subheader("📝 Update Transaction Category")
                cat_tab1, cat_tab2 = st.tabs(["🔄 Quick Categorization", "➕ Add Custom Category"])
                with cat_tab1:
                    with st.form("categorize_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            transaction_options = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                            selected_transaction_index = st.selectbox("Select Transaction to Categorize", options=range(len(transaction_options)), format_func=lambda x: transaction_options[x])
                            selected_id = other_df.iloc[selected_transaction_index]['id']
                        with col2:
                            new_category = st.selectbox("Select Category", options=PREDEFINED_CATEGORIES, help="Choose from predefined categories")
                            custom_description = st.text_input("Custom Description (optional)", help="Add a specific description", placeholder="e.g., 'Medical checkup'")
                        submitted = st.form_submit_button("🔄 Update Category", type="primary")
                        if submitted:
                            try:
                                backend_update_category(int(selected_id), new_category, custom_description)
                                st.success(f"✅ Updated transaction ID {selected_id}.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to update category: {str(e)}")
                with cat_tab2:
                    with st.form("custom_category_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            transaction_options_custom = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                            selected_transaction_custom_index = st.selectbox("Select Transaction for Custom Category", options=range(len(transaction_options_custom)), format_func=lambda x: transaction_options_custom[x], key="custom_transaction_select")
                            selected_id_custom = other_df.iloc[selected_transaction_custom_index]['id']
                            custom_category_name = st.text_input("Custom Category Name", help="Enter a name for your custom category", placeholder="e.g., 'Pet Care'")
                        with col2:
                            keywords_input = st.text_area("Keywords (one per line)", help="Enter keywords to auto-categorize similar transactions", placeholder="APOLLO\nMEDICAL")
                        submitted_custom = st.form_submit_button("➕ Add Custom Category", type="primary")
                        if submitted_custom:
                            if not custom_category_name:
                                st.error("❌ Please enter a custom category name")
                            else:
                                try:
                                    keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
                                    result = backend_add_custom_category(int(selected_id_custom), custom_category_name, keywords)
                                    st.success(result['message'])
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to add custom category: {str(e)}")

            st.title("🔎 Choose the Category or Name")
            st.info("Be a detective! 🕵‍♀ Use the filters below to drill down into your data and find specific transactions.")
            if 'Category' in df.columns:
                selected_category = st.selectbox("Select Category", ['All'] + sorted(df['Category'].unique()))
                selected_name = st.selectbox("Select Name", ['All'] + sorted(df['Description'].unique()))
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
                    st.write(f"💰 *Total Amount after filters:* ₹{filtered_df['Amount'].sum():,.2f}")

            st.subheader("📋 All Transactions")
            display_df = df.copy()
            display_df['Amount (₹)'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
            display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
            available_cols = [col for col in display_cols if col in display_df.columns]
            st.dataframe(display_df[available_cols], use_container_width=True, hide_index=True)
            
            st.header("✨ Detailed Financial Analysis")
            st.info("Ready to go pro? This is where we get super detailed and uncover the real secrets of your spending habits. 🤓")

            expenses_df = df[df['Amount'] < 0].copy()
            expenses_df['Amount'] = expenses_df['Amount'].abs()

            st.title("📸 Your Financial Selfie: Monthly Financial Snapshot")
            total_income = df[df['Amount'] > 0]['Amount'].sum()
            total_spent = expenses_df['Amount'].sum()
            total_invested = expenses_df[expenses_df['Category'] == 'Investment']['Amount'].sum()
            net_savings = total_income - total_spent
            st.write(f"*Total Money Received:* ₹{total_income:,.2f}")
            st.write(f"*Total Money Spent:* ₹{total_spent:,.2f}")
            st.write(f"*Total Money Invested:* ₹{total_invested:,.2f}")
            st.write(f"*Amount Saved:* ₹{net_savings:,.2f}")

            st.title("🤑 Money In")
            st.info("A list of all transactions where you received money. Ka-ching! 💵")
            income_display_df = df[df['Amount'] > 0][['Date', 'Description', 'Amount', 'Category']].copy()
            income_display_df['Amount'] = income_display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(income_display_df, use_container_width=True, hide_index=True)

            st.title('Category-wise Withdrawal Amount Sum:')
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
                st.info("No spending recorded in 'Dining' category.")
            
            st.title('Category-wise Withdrawal Amount Distribution')
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
            
            st.title('Name wise Withdrawal Amount Distribution')
            st.info("This bar chart shows the top 15 specific merchants or people you pay most often.")
            name_wise_amount = expenses_df.groupby("Description")["Amount"].sum().sort_values(ascending=False)
            name_sort_top15 = name_wise_amount.nlargest(15)
            st.write(name_sort_top15)
            st.bar_chart(name_sort_top15)
            
            st.title("Percentage distribution by Name")
            st.info("A pie chart showing the percentage breakdown of your top 7 merchants or recipients.")
            name_sort_top7 = name_wise_amount[name_wise_amount > 0].nlargest(7)
            if not name_sort_top7.empty:
                st.write("Top 7 Spenders:")
                st.write(name_sort_top7)
                fig2, ax2 = plt.subplots()
                ax2.pie(name_sort_top7, labels=name_sort_top7.index, autopct='%1.1f%%', startangle=90)
                ax2.axis('equal')
                st.pyplot(fig2)
            
            st.title("📉 Daily Expense Overview")
            st.info("This line chart shows the rhythm of your total daily spending. Spikes can mean big purchases or bill payments!")
            daily_expenses = expenses_df.groupby(expenses_df['Date'].dt.date)['Amount'].sum()
            st.write(daily_expenses)
            st.line_chart(daily_expenses)

        else:
            st.info("Awaiting data to display analysis.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

# Sidebar Info
st.sidebar.header("ℹ Information")
st.sidebar.info("""
*Simple Expense Analyzer Features:*
- 📁 Upload CSV bank statements
- 🏷 Smart expense categorization
- 📊 Financial overview & analysis
- ✏ Manual category correction
- ➕ Custom category creation
- 🔄 Real-time data processing
""")
st.sidebar.header("📋 Instructions")
st.sidebar.markdown("""
1. *Upload* your bank statement CSV file
2. *Click* 'Launch Smart Analysis' to process
3. *Review* the financial overview
4. *Use Manual Categorization* for uncategorized transactions
5. *Explore* the detailed analysis and graphs
""")
st.sidebar.header("🔧 CSV Format Support")
st.sidebar.info("""
*Format 1:* Standard  
- Date, Description, Amount  
*Format 2:* Bank Statement  
- Date, Narration, Withdrawal Amt., Deposit Amt.  
*Note:* The app handles both formats automatically.
""")
