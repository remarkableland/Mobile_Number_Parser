import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from typing import List

def clean_phone_number(phone) -> str:
    """
    Extract only digits from phone number and ensure it's exactly 10 digits.
    
    Args:
        phone: Phone number (may be string or number)
        
    Returns:
        String containing exactly 10 digits, or empty string if invalid
    """
    if pd.isna(phone) or phone == "":
        return ""
    
    # Convert to string and extract digits only
    if isinstance(phone, (int, float)):
        # For numeric types, convert to int first to avoid scientific notation issues
        phone_str = str(int(phone))
    else:
        phone_str = str(phone)
    
    digits_only = re.sub(r'\D', '', phone_str)
    
    # Ensure we have exactly 10 digits (US phone numbers)
    if len(digits_only) == 10:
        return digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Remove leading 1 (US country code)
        return digits_only[1:]
    elif len(digits_only) == 11 and digits_only.endswith('0'):
        # Remove trailing 0 if it's 11 digits (our bug case)
        return digits_only[:-1]
    else:
        # Invalid length, return empty
        return ""

def generate_output_filename(property_reference_code: str) -> str:
    """
    Generate output filename in format: YYYYMMDD_PropertyReferenceCode_Mobiles_Roor-Ready.csv
    
    Args:
        property_reference_code: User-provided property reference code
        
    Returns:
        Generated filename string
    """
    # Get current date in YYYYMMDD format
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Clean the property reference code for filename (remove invalid characters)
    clean_code = re.sub(r'[<>:"/\\|?*]', '', str(property_reference_code))
    clean_code = clean_code.replace(' ', '_')  # Replace spaces with underscores
    
    # Generate filename
    filename = f"{date_str}_{clean_code}_Mobiles_Roor-Ready.csv"
    
    return filename

def process_phone_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process phone data according to new requirements:
    1. Delete rows where DNC/Litigator Scrub contains "DNC"
    2. Keep only specified columns
    3. Add duplicate name columns for Phone2
    4. Stack all phone data into four columns
    5. Keep only "Mobile" phone types
    6. Remove phone type column
    7. Rename headers to "First Name", "Last Name", "Phone"
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with processed data ready for export
    """
    
    # Step 1: Delete rows where "DNC/Litigator Scrub" contains "DNC"
    initial_count = len(df)
    df_filtered = df[~df["DNC/Litigator Scrub"].astype(str).str.contains("DNC", case=False, na=False)].copy()
    dnc_removed = initial_count - len(df_filtered)
    
    st.info(f"✅ Step 1: Removed {dnc_removed} rows with 'DNC' in 'DNC/Litigator Scrub' column")
    
    # Step 2: Keep only the specified columns
    required_columns = ["Matched First Name", "Matched Last Name", "Phone1", "Phone1 Type", "Phone2", "Phone2 Type"]
    missing_columns = [col for col in required_columns if col not in df_filtered.columns]
    
    if missing_columns:
        st.error(f"❌ Missing required columns: {missing_columns}")
        return pd.DataFrame()
    
    # Select only the required columns
    df_selected = df_filtered[required_columns].copy()
    st.info(f"✅ Step 2: Kept only specified columns: {required_columns}")
    
    # Step 3: Insert duplicate name columns for Phone2
    df_selected["Matched First Name2"] = df_selected["Matched First Name"]
    df_selected["Matched Last Name2"] = df_selected["Matched Last Name"]
    st.info(f"✅ Step 3: Added duplicate name columns for Phone2 data")
    
    # Step 4: Stack all phone data into four columns
    phone_data = []
    
    # Process each row
    for _, row in df_selected.iterrows():
        # Add Phone1 data
        if pd.notna(row["Phone1"]) and row["Phone1"] != "" and str(row["Phone1"]) != "0":
            phone_data.append({
                'First Name': row["Matched First Name"],
                'Last Name': row["Matched Last Name"],
                'Phone': row["Phone1"],
                'Phone Type': row["Phone1 Type"] if pd.notna(row["Phone1 Type"]) else ""
            })
        
        # Add Phone2 data
        if pd.notna(row["Phone2"]) and row["Phone2"] != "" and str(row["Phone2"]) != "0":
            phone_data.append({
                'First Name': row["Matched First Name2"],
                'Last Name': row["Matched Last Name2"],
                'Phone': row["Phone2"],
                'Phone Type': row["Phone2 Type"] if pd.notna(row["Phone2 Type"]) else ""
            })
    
    # Create stacked DataFrame
    stacked_df = pd.DataFrame(phone_data)
    st.info(f"✅ Step 4: Stacked phone data - created {len(stacked_df)} phone number records")
    
    if len(stacked_df) == 0:
        st.warning("⚠️ No phone numbers found to process")
        return pd.DataFrame()
    
    # Step 5: Keep only "Mobile" phone types (case insensitive)
    mobile_df = stacked_df[stacked_df['Phone Type'].astype(str).str.lower() == 'mobile'].copy()
    non_mobile_removed = len(stacked_df) - len(mobile_df)
    st.info(f"✅ Step 5: Kept only 'Mobile' phone types - removed {non_mobile_removed} non-mobile numbers")
    
    if len(mobile_df) == 0:
        st.warning("⚠️ No mobile phone numbers found")
        return pd.DataFrame()
    
    # Step 6: Remove phone type column
    final_df = mobile_df[['First Name', 'Last Name', 'Phone']].copy()
    st.info(f"✅ Step 6: Removed phone type column")
    
    # Step 7: Clean phone numbers to exactly 10 digits
    final_df['Phone'] = final_df['Phone'].apply(clean_phone_number)
    
    # Remove any invalid phone numbers after cleaning
    final_df = final_df[final_df['Phone'] != ""].copy()
    
    st.info(f"✅ Step 7: Cleaned phone numbers to exactly 10 digits - final count: {len(final_df)}")
    
    return final_df

def validate_input_file(df: pd.DataFrame) -> bool:
    """
    Validate that the input CSV has expected structure.
    """
    required_columns = ["DNC/Litigator Scrub", "Matched First Name", "Matched Last Name", 
                       "Phone1", "Phone1 Type", "Phone2", "Phone2 Type"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"❌ Missing required columns: {missing_columns}")
        return False
    
    return True

def main():
    st.title("📱 Phone Number Processor")
    st.markdown("---")
    
    st.markdown("""
    This tool processes phone-enhanced CSV files to extract clean mobile phone numbers with names.
    
    **Processing Steps:**
    1. 🚫 Remove rows with 'DNC' in 'DNC/Litigator Scrub' column
    2. 📋 Keep only name and phone columns (Phone1 & Phone2 only)
    3. 📝 Add duplicate name columns for Phone2 data
    4. 📚 Stack all phone data into four columns
    5. 📱 Keep only 'Mobile' phone types
    6. 🗑️ Remove phone type column
    7. 🏷️ Rename headers to "First Name", "Last Name", "Phone"
    """)
    
    st.markdown("---")
    
    # Property Reference Code input
    st.header("📋 Property Reference Code")
    property_reference_code = st.text_input(
        "Enter Property Reference Code:",
        placeholder="e.g., TX-VanZandt-2025-001",
        help="This will be used in the output filename"
    )
    
    if not property_reference_code:
        st.warning("⚠️ Please enter a Property Reference Code before uploading files")
    
    st.markdown("---")
    
    # File upload section
    st.header("📁 Upload Phone-Enhanced CSV")
    uploaded_file = st.file_uploader(
        "Choose your phone-enhanced CSV file",
        type=['csv'],
        help="Upload the CSV file from the third-party phone service",
        disabled=not property_reference_code
    )
    
    if uploaded_file is not None and property_reference_code:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} rows and {len(df.columns)} columns.")
            
            # Show preview of input data
            with st.expander("📊 Preview Input Data (First 5 rows)"):
                # Show only relevant columns for preview
                preview_cols = ["DNC/Litigator Scrub", "Matched First Name", "Matched Last Name", 
                               "Phone1", "Phone1 Type", "Phone2", "Phone2 Type"]
                available_preview_cols = [col for col in preview_cols if col in df.columns]
                if available_preview_cols:
                    st.dataframe(df[available_preview_cols].head())
                else:
                    st.dataframe(df.head())
            
            # Validate input
            if validate_input_file(df):
                st.header("⚙️ Processing Phone Data")
                
                # Process the CSV
                with st.spinner("Processing phone numbers..."):
                    processed_df = process_phone_data(df)
                
                if len(processed_df) > 0:
                    st.header("🎉 Processing Complete!")
                    
                    # Show preview of output data
                    with st.expander("📋 Preview Processed Data (First 10 rows)"):
                        st.dataframe(processed_df.head(10))
                    
                    # Summary statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Input Rows", len(df))
                    with col2:
                        st.metric("Final Records", len(processed_df))
                    with col3:
                        conversion_rate = (len(processed_df) / len(df)) * 100 if len(df) > 0 else 0
                        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
                    
                    # Download section
                    st.header("💾 Download Roor-Ready File")
                    
                    # Convert DataFrame to CSV with headers
                    csv_buffer = io.StringIO()
                    processed_df.to_csv(csv_buffer, index=False, header=True)
                    csv_data = csv_buffer.getvalue()
                    
                    # Generate filename
                    output_filename = generate_output_filename(property_reference_code)
                    
                    st.download_button(
                        label="📥 Download Roor-Ready CSV",
                        data=csv_data,
                        file_name=output_filename,
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    # Show filename info
                    st.info(f"📁 **Filename**: `{output_filename}`")
                    
                    # Show sample of what will be downloaded
                    st.info(f"📄 **Download Preview:** CSV file will contain {len(processed_df)} records with First Name, Last Name, and Phone columns")
                    with st.expander("🔍 Sample Output (First 5 Records)"):
                        st.dataframe(processed_df.head(5))
                
                else:
                    st.error("❌ No mobile phone numbers found after processing. Check your data and try again.")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted and contains the expected columns.")
    
    elif uploaded_file and not property_reference_code:
        st.warning("⚠️ Please enter a Property Reference Code first.")
    else:
        st.info("👆 Please enter a Property Reference Code and upload a phone-enhanced CSV file to get started.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>Phone Number Processor v2.0 | Built with Streamlit</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
