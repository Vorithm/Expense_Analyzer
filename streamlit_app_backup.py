import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import re


# ==============================================================================
# BACKEND LOGIC
# ==============================================================================


if "df_global" not in st.session_state:
    st.session_state.df_global = None
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False


def extract_name(narration):
    narration_str = str(narration).upper()
    common_merchants = ['AMAZON', 'FLIPKART', 'SWIGGY', 'ZOMATO', 'MYNTRA', 'RELIANCE', 'UBER', 'OLA', 'NETFLIX']
    for merchant in common_merchants:
        if merchant in narration_str:
            return merchant
    if "UPI" in narration_str:
        match = re.search(r'UPI-([^/-]+)', narration_str)
        if match:
            return match.group(1).strip()
    return 'N/A'


def categorize_transaction(description):
    description = str(description).upper()
    category_map = {
        'Groceries': ['GROCERY','SUPERMARKET','FOOD','VEGETABLE','FRUIT','MILK','BREAD','RICE','DAL','OIL','SPICE','KIRANA','GENERAL STORE','BIG BAZAAR','RELIANCE FRESH','DMART','GROFERS','BIGBASKET','RELIANCE MART'],
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
            df['Deposit Amt.'] = df['Amount'].apply(lambda x: x if x > 0 else 0)
            df['Withdrawal Amt.'] = df['Amount'].apply(lambda x: abs(x) if x < 0 else 0)
        else:
            raise ValueError("CSV must contain 'Amount' or ('Withdrawal Amt.' & 'Deposit Amt.') columns")
        if 'Date' not in df.columns: raise ValueError("CSV must contain a 'Date' column")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Category'] = df['Description'].apply(categorize_transaction)
        df['Name'] = df['Description'].apply(extract_name)
        df['custom_name'] = ''
        df = df.dropna(subset=['Date','Amount'])
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
    if df.empty:
        return pd.DataFrame()
    # Treat expense as: Withdrawal Amt. > 0 OR (Amount < 0) OR (Amount > 0 and non-income-like)
    income_like = {'Investment'}  # extend if needed
    if 'Withdrawal Amt.' in df.columns:
        expenses = df[(df['Withdrawal Amt.'] > 0) | (df['Amount'] < 0) | ((df['Amount'] > 0) & (~df['Category'].isin(income_like)))].copy()
        expenses['Amount'] = expenses.apply(
            lambda r: r['Withdrawal Amt.'] if r['Withdrawal Amt.'] > 0 else abs(r['Amount']), axis=1)
    else:
        expenses = df[(df['Amount'] < 0) | ((df['Amount'] > 0) & (~df['Category'].isin(income_like)))].copy()
        expenses['Amount'] = expenses['Amount'].abs()
    if expenses.empty:
        return pd.DataFrame()
    expenses['Display_Category'] = expenses.apply(lambda r: r['custom_name'] if str(r.get('custom_name','')).strip() else r['Category'], axis=1)
    summary = expenses.groupby('Display_Category').agg(Amount=('Amount','sum'), Transaction_Count=('id','count')).reset_index()
    summary.rename(columns={'Display_Category':'Category'}, inplace=True)
    return summary.sort_values('Amount', ascending=False)


# ==============================================================================
# FRONTEND UI
# ==============================================================================

st.set_page_config(page_title="Expense Analyzer", page_icon="💰", layout="wide", initial_sidebar_state="expanded")


st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)
st.markdown('<h1 class="main-header">💰 Expense Analyzer</h1>', unsafe_allow_html=True)


PREDEFINED_CATEGORIES = [
    'Groceries', 'Utilities', 'Rent', 'Entertainment', 'Transportation',
    'Dining', 'Shopping', 'Healthcare', 'Education', 'Insurance',
    'Investment', 'Travel', 'Personal Care', 'Home & Garden', 'Other'
]


st.header("📁 Upload Bank Statement")
st.info("Upload your CSV or analyze the sample dataset.")
tab1, tab2 = st.tabs(["📤 Upload Your CSV", "🔬 Use Sample Data"])


with tab1:
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], label_visibility="collapsed")
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        if st.button("🚀 Launch Smart Analysis", type="primary"):
            with st.spinner("Processing your data..."):
                try:
                    backend_upload_csv(uploaded_file)
                    st.success("✅ File processed successfully")
                    st.session_state.data_updated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")


with tab2:
    st.info("Click to analyze the pre-loaded sample dataset.")
    if st.button("Analyze Sample Data"):
        with st.spinner("Processing sample data..."):
            try:
                with open("sample_data.csv", "rb") as f:
                    backend_upload_csv(f)
                    st.success("✅ Sample processed")
                    st.session_state.data_updated = True
                    st.rerun()
            except FileNotFoundError:
                st.error("❌ sample_data.csv not found.")
            except Exception as e:
                st.error(f"❌ Error processing sample file: {str(e)}")


if st.session_state.data_updated or st.button("🔄 Refresh Data"):
    st.header("📊 Financial Overview")
    try:
        df = backend_get_transactions_df()
        if not df.empty:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df.dropna(subset=['Date', 'Amount'], inplace=True)

            categories_found = int(df['Category'].nunique(dropna=True))
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: st.metric("Total Transactions", len(df))
            with col2: st.metric("Categories Found", f"{ categories_found}")
            with col3: st.metric("Net Amount", f"₹{df['Amount'].sum():,.2f}")
            with col4: st.metric("Total Expenses", f"₹{abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")
            with col5: st.metric("Total Income", f"₹{df[df['Amount'] > 0]['Amount'].sum():,.2f}")
            

            st.subheader("📋 All Transactions")
            display_df = df.copy()
            display_df['Amount (₹)'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
            display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
            available_cols = [c for c in display_cols if c in display_df.columns]
            st.dataframe(display_df[available_cols], use_container_width=True, hide_index=True)


            st.subheader("📈 Category Analysis")
            st.info("Expense distribution by category.")
            category_df = backend_get_expense_summary_df()
            if not category_df.empty:
                total_expense = category_df['Amount'].sum()
                category_df['Percentage'] = (category_df['Amount'] / total_expense * 100).round(1) if total_expense > 0 else 0

                c1, c2 = st.columns(2)
                with c1:
                    fig_pie = px.pie(category_df, values='Amount', names='Category', title='Expense Distribution by Category')
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c2:
                    fig_bar = px.bar(category_df, x='Category', y='Amount', title='Expense Amount by Category', color='Amount', color_continuous_scale='viridis')
                    fig_bar.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_bar, use_container_width=True)

                st.subheader("📋 Category Details")
                category_df['Amount (₹)'] = category_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                category_df['Percentage'] = category_df['Percentage'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(category_df[['Category','Amount (₹)','Percentage','Transaction_Count']], use_container_width=True, hide_index=True)


            st.header("✏ Manual Categorization")
            other_df = backend_get_other_df()
            if other_df.empty:
                st.success("✅ All transactions categorized!")
            else:
                st.write(f"📊 Found {len(other_df)} uncategorized transactions")
                od = other_df.copy()
                if 'Amount' in od.columns:
                    od['Amount (₹)'] = od['Amount'].apply(lambda x: f"₹{abs(x):,.2f}")
                cols = ['Date', 'Description', 'Amount (₹)', 'Category']
                st.dataframe(od[[c for c in cols if c in od.columns]], use_container_width=True, hide_index=True)


                cat_tab1, cat_tab2 = st.tabs(["🔄 Quick Categorization", "➕ Add Custom Category"])
                with cat_tab1:
                    with st.form("categorize_form"):
                        colA, colB = st.columns(2)
                        with colA:
                            options = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                            idx = st.selectbox("Select Transaction", options=range(len(options)), format_func=lambda x: options[x])
                            sel_id = other_df.iloc[idx]['id']
                        with colB:
                            new_cat = st.selectbox("Select Category", options=PREDEFINED_CATEGORIES)
                            custom_desc = st.text_input("Custom Description (optional)", placeholder="e.g., 'Medical checkup'")
                        if st.form_submit_button("🔄 Update Category", type="primary"):
                            try:
                                backend_update_category(int(sel_id), new_cat, custom_desc)
                                st.success(f"✅ Updated transaction ID {sel_id}.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed: {str(e)}")
                with cat_tab2:
                    with st.form("custom_category_form"):
                        colA, colB = st.columns(2)
                        with colA:
                            options2 = [f"ID {row['id']}: {str(row['Description'])[:50]}... - ₹{abs(row['Amount']):,.2f}" for _, row in other_df.iterrows()]
                            idx2 = st.selectbox("Select Transaction", options=range(len(options2)), format_func=lambda x: options2[x], key="custom_transaction_select")
                            sel_id2 = other_df.iloc[idx2]['id']
                            custom_cat_name = st.text_input("Custom Category Name", placeholder="e.g., 'Pet Care'")
                        with colB:
                            kw_input = st.text_area("Keywords (one per line)", placeholder="APOLLO\nMEDICAL")
                        if st.form_submit_button("➕ Add Custom Category", type="primary"):
                            if not custom_cat_name:
                                st.error("❌ Please enter a custom category name")
                            else:
                                try:
                                    kws = [k.strip() for k in kw_input.split('\n') if k.strip()]
                                    backend_add_custom_category(int(sel_id2), custom_cat_name, kws)
                                    st.success("✅ Custom category added.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed: {str(e)}")


            st.title("🔎 Choose the Category or Name")
            st.info("Filter to specific transactions.")
            if 'Category' in df.columns:
                selected_category = st.selectbox("Select Category", ['All'] + sorted(df['Category'].unique()))
                selected_name = st.selectbox("Select Name", ['All'] + sorted(df['Description'].unique()))
                filtered_df = df.copy()
                if selected_category != 'All':
                    filtered_df = filtered_df[filtered_df['Category'] == selected_category]
                if selected_name != 'All':
                    filtered_df = filtered_df[filtered_df['Description'] == selected_name]
                st.write("Filtered Data:")
                df_disp = filtered_df.copy()
                df_disp['Amount (₹)'] = df_disp['Amount'].apply(lambda x: f"₹{x:,.2f}")
                desired_cols = ['id', 'custom_name', 'Date', 'Category', 'Description', 'Amount (₹)']
                st.dataframe(df_disp[[c for c in desired_cols if c in df_disp.columns]], use_container_width=True, hide_index=True)
                if not filtered_df.empty:
                    st.write(f"💰 Total after filters: ₹{filtered_df['Amount'].sum():,.2f}")

            st.header("✨ Detailed Financial Analysis")
            st.info("Deeper insights into spending patterns.")

            # Build expenses_df for downstream charts
            expenses_df = df[df['Amount'] < 0].copy()
            expenses_df['Amount'] = expenses_df['Amount'].abs()

            st.title("Money Received")
            money_received_df = df[df["Deposit Amt."] > 0].copy()
            money_received_df['Date'] = pd.to_datetime(money_received_df['Date']).dt.strftime('%Y-%m-%d')

            st.dataframe(
                money_received_df[['Date', 'Name', 'Category', 'Deposit Amt.']],
                use_container_width=True,
                hide_index=True)
            
            st.title('Category-wise Withdrawal Amount Sum:')
            st.info("Bar plot of total withdrawals per category, with a table of categories and totals.")

            # Group by Category to get total withdrawal amount and counts
            cat_sum = (expenses_df.groupby("Category", dropna=False)["Amount"].sum().sort_values(ascending=False))
            cat_count = expenses_df.groupby("Category", dropna=False)["Amount"].count()

            # Build complete table with all categories from df (including those with zero withdrawals)
            all_cats = sorted(df['Category'].dropna().unique().tolist())
            cat_df = pd.DataFrame({"Category": all_cats}).merge(pd.DataFrame({"Category": cat_sum.index, "Withdrawal Amount": cat_sum.values}),
                on="Category",how="left").merge(
                pd.DataFrame({"Category": cat_count.index, "Transaction Count": cat_count.values}),on="Category",how="left")
            cat_df["Withdrawal Amount"] = cat_df["Withdrawal Amount"].fillna(0.0).astype(float)
            cat_df["Transaction Count"] = cat_df["Transaction Count"].fillna(0).astype(int)
            cat_df = cat_df.sort_values("Withdrawal Amount", ascending=False)

            # Table
            show_df = cat_df.copy()
            show_df["Withdrawal Amount (₹)"] = show_df["Withdrawal Amount"].apply(lambda x: f"₹{x:,.2f}")
            show_df = show_df[["Category", "Withdrawal Amount (₹)", "Transaction Count"]]
            st.subheader("Categories and Totals")
            st.dataframe(show_df, use_container_width=True, hide_index=True)
            
            # Bar chart
            plot_df = cat_df.set_index("Category")[["Withdrawal Amount"]]
            if plot_df.empty:
                st.info("No expense categories to display.")
            else:
                st.bar_chart(plot_df, use_container_width=True)

            st.title('🍔 Daily Spending on Dining')
            dining_df = df[df["Category"] == "Dining"].copy()
            if not dining_df.empty:
                dining_df['Amount'] = dining_df['Amount'].abs()
                daily_spending_food = dining_df.groupby(dining_df['Date'].dt.date)['Amount'].sum()
                st.write(daily_spending_food)
                st.line_chart(daily_spending_food)
            else:
                st.info("No spending recorded in 'Dining' category.")
            
            st.title('Category-wise Withdrawal Amount Distribution')
            st.info("Percentage share of total withdrawals per category.")

            # Use only categories with positive totals for the pie chart
            pie_df = cat_df[cat_df["Withdrawal Amount"] > 0].copy()
            if pie_df.empty:
                st.info("No positive withdrawal totals to display.")
            else:
                fig_pie_withdraw = px.pie(
                    pie_df,
                    names="Category",
                    values="Withdrawal Amount",
                    title="Category-wise Withdrawal Amount Distribution"
                )
                st.plotly_chart(fig_pie_withdraw, use_container_width=True)

           
            st.title("📉 Daily Expense Overview")
            daily_expenses = expenses_df.groupby(expenses_df['Date'].dt.date)['Amount'].sum()
            st.write(daily_expenses)
            st.line_chart(daily_expenses)
            
            
            TIPS = [
                "🚀 Small savings today become big money tomorrow.", 
                "⛔ Don’t compare your lifestyle with others — focus on your goals.", 
                "🥳 Celebrate small financial wins.", 
                "🌟 Every rupee you save is a step toward freedom.",
                "📅 Plan your week so you avoid last-minute expensive choices.",
                "🛑 Don’t buy things to impress others.",
                "🎯 Spend on experiences, not just things.",
                "💰 Save a little before you start spending.",
                "🛍 A discount isn’t saving if you don’t really need it.", 
                "🤔 If you can’t buy it twice, think before buying once.",
                "⏳ Wait 1 day before buying something you want — avoid impulse shopping.", 
                "✍️ Write down all your spending for a week — see where money goes.",
                "📦 Buy only what you need, not what’s trending.",
                "📝 Make a shopping list and stick to it.",
                "🔍 Compare prices before buying anything big.", 
                "📅 Pay bills on time — no extra charges!", 
                "🏆 Good quality lasts longer than cheap replacements.",
                "🎯 Pay off the loan with the highest interest first.", 
                "💳 Avoid paying just the “minimum” on credit cards.",
                "🛡 Use credit only if you can pay in full.",
                "📉 Keep credit use below 30% of your limit. ",
                "🛑 Don’t take EMI unless you really need it. ",
                "⏰ Remember loan dates — no late fees. ",
                "🚫 Avoid small personal loans.",
                "🔄 Change to a loan with lower interest if you can.", 
                "🤝 Co-sign loans only if you 100% trust the person. ",
                "⚠ Stay away from payday loans — super high cost. ",
                "🛒 Always eat before grocery shopping — no hunger buys!", 
                "📊 Review your monthly expenses and cut 1–2 wasteful ones.", 
                "🎯 Set small saving goals — easier to achieve. ",
                "📱 Use budgeting apps to track your money. ",
                "🛡 Keep some cash hidden for emergencies. ",
                "🏦 Open a separate account only for savings.", 
                "🚫 Avoid shopping when bored — find free activities instead." 
            ]

            # State
            if "tip_visible" not in st.session_state:
                st.session_state.tip_visible = False
            if "tips_pool" not in st.session_state:
                st.session_state.tips_pool = TIPS.copy()
            if "current_tip" not in st.session_state:
                st.session_state.current_tip = None

            # Optional: light styling
            st.markdown("""
            <style>
            .pill-btn {
                display: inline-block; padding: 8px 14px; border-radius: 999px;
                background: #1f77b4; color: white; font-weight: 600; border: none;
            }
            .tip-card {
                border: 1px solid rgba(31,119,180,.15); border-radius: 10px;
                padding: 12px 14px; background: rgba(31,119,180,.05);
            }
            </style>
            """, unsafe_allow_html=True)

            col_tip1, col_tip2 = st.columns([1, 4])
            with col_tip1:
                if st.button("💡 Tip Jar", type="primary"):
                    import random
                    if not st.session_state.tips_pool:
                        # Reset pool when all have been shown
                        st.session_state.tips_pool = TIPS.copy()
                    st.session_state.current_tip = random.choice(st.session_state.tips_pool)
                    st.session_state.tips_pool.remove(st.session_state.current_tip)
                    st.session_state.tip_visible = True

            with col_tip2:
                if st.session_state.tip_visible and st.session_state.current_tip:
                    st.markdown(f"<div class='tip-card'>{st.session_state.current_tip}</div>", unsafe_allow_html=True)
                else:
                    st.caption("Click the Tip Jar to reveal a helpful tip.")

            # Centered closing messages (smaller font)
            st.markdown(
                "<div style='text-align:center; font-size:1.40rem; margin:12px 0;'>"
                "Hope today’s insights were helpful. Come back anytime to track, reflect, and optimize your finances. ✨"
                "</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<div style='text-align:center; font-size:1.80rem; margin-bottom:6px;'>"
                "Wallet vibes updated. Catch you on the next swipe. 💳"
                "</div>",
                unsafe_allow_html=True
            )
        
        else:
            st.info("Awaiting data to display analysis.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")


# Sidebar
st.sidebar.header("ℹ Information")
st.sidebar.info("""
- 📁 Upload CSV bank statements
- 🏷️Smart expense categorization
- 📊Financial overview & analysis
- 📋Manual category correction
- 📈Custom category creation
- 🔄Real-time data processing

**Enhanced Categories:**
- 🥬 Groceries
- 🏠 Utilities  
- 🏘️ Rent
- 🎬 Entertainment
- 🚗 Transportation
- 🍽️ Dining
- 🛒 Shopping
- 🏥 Healthcare
- 🎓 Education
- 🛡️ Insurance
- 💰 Investment
- ✈️ Travel
- 💅 Personal Care
- 🏡 Home & Garden
- ❓ Other
""")

st.sidebar.header("📋 Instructions")
st.sidebar.markdown("""
1. Upload your bank statement CSV file
2. Click 'Launch Smart Analysis' to process
3. Review the financial overview
4. Use Manual Categorization for uncategorized transactions
5. Explore the detailed analysis and graphs
""")
st.sidebar.header("🔧 CSV Format Support")
st.sidebar.info("""
Format 1: Standard — Date, Description, Amount
Format 2: Bank Statement — Date, Narration, Withdrawal Amt., Deposit Amt.
Note: The app handles both formats automatically.
""")

