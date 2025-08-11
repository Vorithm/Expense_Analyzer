from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import traceback
import numpy as np
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for communication with Streamlit

# Global DataFrame to hold uploaded data
df_global = None

# Predefined categories
PREDEFINED_CATEGORIES = [
    'Groceries', 'Utilities', 'Rent', 'Entertainment', 'Transportation',
    'Dining', 'Shopping', 'Healthcare', 'Education', 'Insurance',
    'Investment', 'Travel', 'Personal Care', 'Home & Garden', 'Other'
]

def categorize_transaction(description):
    """Categorize transaction based on description"""
    description = str(description).upper()
    
    # Groceries
    if any(keyword in description for keyword in [
        'GROCERY', 'SUPERMARKET', 'FOOD', 'VEGETABLE', 'FRUIT', 'MILK',
        'BREAD', 'RICE', 'DAL', 'OIL', 'SPICE', 'KIRANA', 'GENERAL STORE',
        'BIG BAZAAR', 'RELIANCE FRESH', 'DMART', 'GROFERS', 'BIGBASKET'
    ]):
        return 'Groceries'
    
    # Utilities
    elif any(keyword in description for keyword in [
        'ELECTRICITY', 'POWER', 'GAS', 'WATER', 'INTERNET', 'PHONE',
        'MOBILE', 'BROADBAND', 'WIFI', 'UTILITY', 'BILL', 'PAYMENT',
        'BSNL', 'AIRTEL', 'JIO', 'VODAFONE', 'IDEA', 'MTNL'
    ]):
        return 'Utilities'
    
    # Rent
    elif any(keyword in description for keyword in [
        'RENT', 'HOUSE RENT', 'ACCOMMODATION', 'LEASE', 'RENTAL'
    ]):
        return 'Rent'
    
    # Entertainment
    elif any(keyword in description for keyword in [
        'MOVIE', 'CINEMA', 'NETFLIX', 'AMAZON PRIME', 'HOTSTAR', 'ENTERTAINMENT',
        'GAME', 'GAMING', 'PLAYSTATION', 'XBOX', 'NINTENDO', 'BOOK', 'MAGAZINE',
        'NEWSPAPER', 'MUSIC', 'SPOTIFY', 'YOUTUBE', 'STREAMING'
    ]):
        return 'Entertainment'
    
    # Transportation
    elif any(keyword in description for keyword in [
        'PETROL', 'DIESEL', 'FUEL', 'GAS', 'UBER', 'OLA', 'TAXI', 'BUS',
        'TRAIN', 'METRO', 'PARKING', 'TOLL', 'TRANSPORT', 'CAB', 'AUTO',
        'PETROL PUMP', 'HP', 'SHELL', 'BP', 'INDIAN OIL'
    ]):
        return 'Transportation'
    
    # Dining
    elif any(keyword in description for keyword in [
        'RESTAURANT', 'CAFE', 'FOOD', 'MEAL', 'LUNCH', 'DINNER', 'BREAKFAST',
        'SWIGGY', 'ZOMATO', 'FOODPANDA', 'DOMINOS', 'PIZZA HUT', 'KFC',
        'MCDONALDS', 'SUBWAY', 'CAFETERIA', 'CANTEEN', 'HOTEL', 'BAR', 'PUB'
    ]):
        return 'Dining'
    
    # Shopping
    elif any(keyword in description for keyword in [
        'AMAZON', 'FLIPKART', 'MYNTRA', 'SHOPPING', 'PURCHASE', 'MALL',
        'SHOP', 'RETAIL', 'CLOTHING', 'FASHION', 'SHOES', 'ELECTRONICS',
        'APPLIANCES', 'FURNITURE', 'DECOR', 'LIFESTYLE', 'JABONG',
        'SNAPDEAL', 'PAYTM MALL', 'TATA CLIQ', 'NYKAA', 'LENSKART'
    ]):
        return 'Shopping'
    
    # Healthcare
    elif any(keyword in description for keyword in [
        'HOSPITAL', 'DOCTOR', 'MEDICAL', 'PHARMACY', 'MEDICINE', 'HEALTH',
        'CLINIC', 'DENTAL', 'SURGERY', 'AMBULANCE', 'APOLLO', 'FORTIS',
        'MAX HOSPITAL', 'MEDPLUS', 'NETMEDS', 'PRACTO', 'HEALTHKART'
    ]):
        return 'Healthcare'
    
    # Education
    elif any(keyword in description for keyword in [
        'SCHOOL', 'COLLEGE', 'UNIVERSITY', 'EDUCATION', 'TUITION', 'FEES',
        'COURSE', 'TRAINING', 'BOOKS', 'LIBRARY', 'EXAM', 'BYJU',
        'UNACADEMY', 'VEDANTU', 'STUDENT', 'ACADEMIC'
    ]):
        return 'Education'
    
    # Insurance
    elif any(keyword in description for keyword in [
        'INSURANCE', 'POLICY', 'PREMIUM', 'LIC', 'HDFC LIFE', 'ICICI PRU',
        'SBI LIFE', 'BAJAJ ALLIANZ', 'TATA AIG', 'RELIANCE GENERAL',
        'HEALTH INSURANCE', 'MOTOR INSURANCE', 'TERM INSURANCE'
    ]):
        return 'Insurance'
    
    # Investment
    elif any(keyword in description for keyword in [
        'MUTUAL FUND', 'SIP', 'INVESTMENT', 'TRADING', 'ZERODHA', 'GROWW',
        'ANGEL BROKING', 'UPSTOX', 'PAYTM MONEY', 'KUVERA', 'STOCK',
        'EQUITY', 'BOND', 'FD', 'RD', 'PPF', 'ELSS', 'NSE', 'BSE'
    ]):
        return 'Investment'
    
    # Travel
    elif any(keyword in description for keyword in [
        'IRCTC', 'MAKEMYTRIP', 'GOIBIBO', 'CLEARTRIP', 'YATRA', 'TRAVEL',
        'BOOKING', 'HOTEL', 'FLIGHT', 'TRAIN', 'BUS', 'TICKET', 'VACATION',
        'HOLIDAY', 'TOURISM', 'AIRBNB', 'OYO', 'TREEBO', 'REDBUS'
    ]):
        return 'Travel'
    
    # Personal Care
    elif any(keyword in description for keyword in [
        'SALON', 'PARLOUR', 'BEAUTY', 'COSMETICS', 'SKINCARE', 'HAIRCUT',
        'MASSAGE', 'SPA', 'WELLNESS', 'FITNESS', 'GYM', 'YOGA',
        'PERSONAL CARE', 'GROOMING', 'URBAN COMPANY', 'LAKME'
    ]):
        return 'Personal Care'
    
    # Home & Garden
    elif any(keyword in description for keyword in [
        'HOME DEPOT', 'GARDEN', 'PLANTS', 'NURSERY', 'HARDWARE', 'TOOLS',
        'REPAIR', 'MAINTENANCE', 'PLUMBER', 'ELECTRICIAN', 'CARPENTER',
        'PAINT', 'TILES', 'CEMENT', 'CONSTRUCTION', 'RENOVATION'
    ]):
        return 'Home & Garden'
    
    else:
        return 'Other'

@app.route("/api/upload_csv", methods=["POST"])
def upload_csv():
    global df_global
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Please upload a CSV file"}), 400

        # Read CSV file
        df = pd.read_csv(file)
        
        # Check if DataFrame is empty
        if df.empty:
            return jsonify({"error": "The uploaded CSV file is empty"}), 400
        
        # Remove duplicate header row if it exists
        if len(df) > 0 and df.iloc[0].equals(df.columns):
            df = df.drop(df.index[0]).reset_index(drop=True)
        
        # Clean column names (remove extra spaces)
        df.columns = df.columns.str.strip()
        
        # Validate required columns based on different CSV formats
        required_columns_found = False
        
        # Check for the specific format mentioned: Date, Narration, Unnamed: 2, Value Dt, Withdrawal Amt., Deposit Amt., Closing Balance
        if 'Withdrawal Amt.' in df.columns and 'Deposit Amt.' in df.columns:
            # Convert to numeric, handling various formats
            df['Withdrawal Amt.'] = pd.to_numeric(df['Withdrawal Amt.'].astype(str).str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)
            df['Deposit Amt.'] = pd.to_numeric(df['Deposit Amt.'].astype(str).str.replace(',', '').replace('', '0'), errors='coerce').fillna(0)
            
            # Create a unified Amount column (negative for withdrawals, positive for deposits)
            df['Amount'] = df['Deposit Amt.'] - df['Withdrawal Amt.']
            
            # Use Narration as Description
            if 'Narration' in df.columns:
                df['Description'] = df['Narration'].fillna('No description')
            else:
                df['Description'] = 'No description'
                
            required_columns_found = True
            
        # Check for standard expense format (Amount column exists)
        elif 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace(',', ''), errors='coerce')
            
            # Check for Description column variants
            if 'Description' not in df.columns:
                if 'Narration' in df.columns:
                    df['Description'] = df['Narration'].fillna('No description')
                elif 'Transaction' in df.columns:
                    df['Description'] = df['Transaction'].fillna('No description')
                else:
                    df['Description'] = 'No description'
                    
            required_columns_found = True
        
        if not required_columns_found:
            return jsonify({"error": "CSV must contain either 'Amount' column or 'Withdrawal Amt.' and 'Deposit Amt.' columns"}), 400
        
        # Ensure Date column exists
        if 'Date' not in df.columns:
            return jsonify({"error": "CSV must contain a 'Date' column"}), 400
        
        # Initialize Category column
        df['Category'] = df['Description'].apply(categorize_transaction)
        
        # Add custom_name column for custom categories
        df['custom_name'] = ''
        
        # Remove rows with NaN amounts
        df = df.dropna(subset=['Amount'])
        
        # Add an 'id' column after cleaning the data
        df['id'] = range(1, len(df) + 1)
        
        # Store in global variable
        df_global = df
        
        # Count categories
        category_counts = df['Category'].value_counts().to_dict()
        
        return jsonify({
            "message": "File processed successfully",
            "total_transactions": len(df),
            "categories": category_counts,
            "other_count": category_counts.get('Other', 0)
        }), 200
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        return jsonify({"error": error_msg}), 500

@app.route("/api/get_transactions", methods=["GET"])
def get_transactions():
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available. Please upload a CSV file first."}), 400
    
    try:
        # Select only required columns for display
        display_columns = ['id', 'Date', 'Description', 'Amount', 'Category', 'custom_name']
        available_columns = [col for col in display_columns if col in df_global.columns]
        
        data = df_global[available_columns].to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving transactions: {str(e)}"}), 500

@app.route("/api/get_other_transactions", methods=["GET"])
def get_other_transactions():
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        other_txns = df_global[df_global['Category'] == 'Other']
        display_columns = ['id', 'Date', 'Description', 'Amount', 'Category', 'custom_name']
        available_columns = [col for col in display_columns if col in other_txns.columns]
        
        if len(other_txns) > 0:
            pass # Removed debug print
        
        data = other_txns[available_columns].to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error retrieving other transactions: {str(e)}"}), 500

@app.route("/api/update_category", methods=["POST"])
def update_category():
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        data = request.get_json()
        transaction_id = data.get('id')
        new_category = data.get('category')
        custom_name = data.get('custom_name', '')
        
        if not transaction_id:
            return jsonify({"error": "Transaction ID is required"}), 400
        
        if not new_category:
            return jsonify({"error": "Category is required"}), 400
        
        # Convert transaction_id to int if it's a string
        try:
            transaction_id = int(transaction_id)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid transaction ID format: {transaction_id}"}), 400
        
        # Validate category (allow custom categories)
        if new_category not in PREDEFINED_CATEGORIES and not custom_name:
            return jsonify({"error": "Custom category name is required for non-predefined categories"}), 400
        
        # Update the category and custom name
        mask = df_global['id'] == transaction_id
        
        if not mask.any():
            # Debug: Print available IDs
            available_ids = df_global['id'].tolist()
            return jsonify({
                "error": f"Transaction ID {transaction_id} not found. Available IDs: {available_ids[:10]}..."  # Show first 10 IDs
            }), 404
            
        # Update the category
        df_global.loc[mask, 'Category'] = new_category
        df_global.loc[mask, 'custom_name'] = custom_name
        
        return jsonify({"message": "Category updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Error updating category: {str(e)}"}), 500

@app.route("/api/add_custom_category", methods=["POST"])
def add_custom_category():
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        data = request.get_json()
        transaction_id = data.get('id')
        custom_category = data.get('custom_category')
        description_keywords = data.get('description_keywords', [])
        
        if not transaction_id:
            return jsonify({"error": "Transaction ID is required"}), 400
        
        if not custom_category:
            return jsonify({"error": "Custom category name is required"}), 400
        
        # Convert transaction_id to int if it's a string
        try:
            transaction_id = int(transaction_id)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid transaction ID format: {transaction_id}"}), 400
        
        # Update the specific transaction
        mask = df_global['id'] == transaction_id
        
        if not mask.any():
            # Debug: Print available IDs
            available_ids = df_global['id'].tolist()
            return jsonify({
                "error": f"Transaction ID {transaction_id} not found. Available IDs: {available_ids[:10]}..."  # Show first 10 IDs
            }), 404
            
        df_global.loc[mask, 'Category'] = custom_category
        df_global.loc[mask, 'custom_name'] = custom_category
        
        # If keywords provided, update other transactions with similar descriptions
        affected_count = 1  # At least the selected transaction
        if description_keywords:
            for keyword in description_keywords:
                if keyword.strip():
                    keyword_mask = df_global['Description'].str.contains(keyword.strip(), case=False, na=False)
                    df_global.loc[keyword_mask, 'Category'] = custom_category
                    df_global.loc[keyword_mask, 'custom_name'] = custom_category
                    affected_count = df_global[df_global['Category'] == custom_category].shape[0]
        
        return jsonify({
            "message": f"Custom category '{custom_category}' added successfully",
            "affected_transactions": affected_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error adding custom category: {str(e)}"}), 500

@app.route("/api/get_expense_summary", methods=["GET"])
def get_expense_summary():
    """Get expense-only summary for charts"""
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        # Create summary with expenses only (negative amounts)
        expenses = df_global[df_global['Amount'] < 0].copy()
        
        if expenses.empty:
            return jsonify({"error": "No expense data found"}), 400
        
        expenses['Amount'] = expenses['Amount'].abs()
        
        # Create display category (use custom_name if available, otherwise use Category)
        expenses['Display_Category'] = expenses.apply(
            lambda row: row['custom_name'] if row['custom_name'] else row['Category'],
            axis=1
        )
        
        # Get all unique categories to ensure all are represented
        all_categories = expenses['Display_Category'].unique()
        
        # Group by display category and sum amounts
        summary = expenses.groupby('Display_Category').agg({
            'Amount': 'sum',
            'id': 'count'
        }).reset_index()
        summary.columns = ['Category', 'Amount', 'Transaction_Count']
        
        # Ensure all categories are included (even if sum is 0)
        missing_categories = set(all_categories) - set(summary['Category'])
        for cat in missing_categories:
            new_row = pd.DataFrame({
                'Category': [cat],
                'Amount': [0],
                'Transaction_Count': [0]
            })
            summary = pd.concat([summary, new_row], ignore_index=True)
            
        summary = summary.sort_values('Amount', ascending=False)
        summary['Amount'] = summary['Amount'].round(2)
        
        return jsonify(summary.to_dict(orient='records'))
        
    except Exception as e:
        return jsonify({"error": f"Error creating expense summary: {str(e)}"}), 500
    
@app.route("/api/get_all_categories", methods=["GET"])
def get_all_categories():
    global df_global
    if df_global is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        # Get all unique categories including custom ones
        all_categories = df_global['Category'].unique().tolist()
        custom_categories = df_global[df_global['custom_name'] != '']['custom_name'].unique().tolist()
        
        # Combine and deduplicate
        all_categories = list(set(all_categories + custom_categories))
        
        return jsonify({
            "predefined_categories": PREDEFINED_CATEGORIES,
            "all_categories": all_categories,
            "custom_categories": custom_categories
        })
        
    except Exception as e:
        return jsonify({"error": f"Error retrieving categories: {str(e)}"}), 500

# Remove unnecessary endpoints - keep only the essential ones
# Remove: get_budget_status, get_spending_alerts, get_spending_trends, get_recurring_expenses, get_savings_goals, get_financial_insights

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Expense Analyzer API is running"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)