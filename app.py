import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from typing import List

def generate_output_filename(df: pd.DataFrame) -> str:
    """
    Generate output filename in format: YYYYMMDD_CustomField_Mobiles.csv
    
    Args:
        df: Original DataFrame to extract custom field from
        
    Returns:
        Generated filename string
    """
    # Get current date in YYYYMMDD format
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Try to get custom field value from first row
    custom_field = ""
    if "Input Custom Field 1" in df.columns:
        first_custom_field = df["Input Custom Field 1"].dropna().iloc[0] if len(df["Input Custom Field 1"].dropna()) > 0 else ""
        if first_custom_field:
            # Clean the custom field for filename (remove invalid characters)
            custom_field = re.sub(r'[<>:"/\\|?*]', '', str(first_custom_field))
            custom_field = custom_field.replace(' ', '_')  # Replace spaces with underscores
    
    # Generate filename
    if custom_field:
        filename = f"{date_str}_{custom_field}_Mobiles.csv"
    else:
        filename = f"{date_str}_Mobiles.csv"
    
    return filename
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

def process_phone_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process phone data according to requirements:
    1. Delete rows where DNC/Litigator Scrub contains "DNC"
    2. Keep only Phone1, Phone1 Type, Phone2, Phone2 Type, Phone3, Phone3 Type columns
    3. Stack all phone columns 
    4. Delete rows where phone type is not "Mobile"
    5. Keep only phone numbers (digits only)
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with cleaned mobile phone numbers only
    """
    
    # Step 1: Delete rows where "DNC/Litigator Scrub" contains "DNC"
    initial_count = len(df)
    df_filtered = df[~df["DNC/Litigator Scrub"].astype(str).str.contains("DNC", case=False, na=False)].copy()
    dnc_removed = initial_count - len(df_filtered)
    
    st.info(f"✅ Step 1: Removed {dnc_removed} rows with 'DNC' in 'DNC/Litigator Scrub' column")
    
    # Step 2: Keep only the specified phone columns
    required_columns = ["Phone1", "Phone1 Type", "Phone2", "Phone2 Type", "Phone3", "Phone3 Type"]
    missing_columns = [col for col in required_columns if col not in df_filtered.columns]
    
    if missing_columns:
        st.error(f"❌ Missing required columns: {missing_columns}")
        return pd.DataFrame()
    
    # Select only the required columns
    df_phones_only = df_filtered[required_columns].copy()
    st.info(f"✅ Step 2: Kept only phone columns: {required_columns}")
    
    # Step 3: Stack all phone columns
    phone_data = []
    
    phone_columns = [
        ("Phone1", "Phone1 Type"),
        ("Phone2", "Phone2 Type"), 
        ("Phone3", "Phone3 Type")
    ]
    
    for _, row in df_phones_only.iterrows():
        for phone_col, type_col in phone_columns:
            phone = row[phone_col]
            phone_type = row[type_col]
            
            # Only add if phone number exists
            if pd.notna(phone) and phone != "" and str(phone) != "0":
                phone_data.append({
                    'Column A': phone,
                    'Column B': phone_type if pd.notna(phone_type) else ""
                })
    
    # Create stacked DataFrame
    stacked_df = pd.DataFrame(phone_data)
    st.info(f"✅ Step 3: Stacked phone data - created {len(stacked_df)} phone number records")
    
    if len(stacked_df) == 0:
        st.warning("⚠️ No phone numbers found to process")
        return pd.DataFrame()
    
    # Step 4: Keep only "Mobile" phone types (case insensitive)
    mobile_df = stacked_df[stacked_df['Column B'].astype(str).str.lower() == 'mobile'].copy()
    non_mobile_removed = len(stacked_df) - len(mobile_df)
    st.info(f"✅ Step 4: Kept only 'Mobile' phone types - removed {non_mobile_removed} non-mobile numbers")
    
    if len(mobile_df) == 0:
        st.warning("⚠️ No mobile phone numbers found")
        return pd.DataFrame()
    
    # Step 5: Remove Column B (phone type)
    final_df = mobile_df[['Column A']].copy()
    st.info(f"✅ Step 5: Removed phone type column (Column B)")
    
    # Step 6: Clean phone numbers to digits only and ensure 10 digits
    final_df['Column A'] = final_df['Column A'].apply(clean_phone_number)
    
    # Remove any invalid phone numbers after cleaning
    final_df = final_df[final_df['Column A'] != ""].copy()
    
    st.info(f"✅ Step 6: Cleaned phone numbers to exactly 10 digits - final count: {len(final_df)}")
    
    return final_df

def validate_input_file(df: pd.DataFrame) -> bool:
    """
    Validate that the input CSV has expected structure.
    """
    required_columns = ["DNC/Litigator Scrub", "Phone1", "Phone1 Type", "Phone2", "Phone2 Type", "Phone3", "Phone3 Type"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"❌ Missing required columns: {missing_columns}")
        return False
    
    # Check for Input Custom Field 1 (optional but recommended)
    if "Input Custom Field 1" not in df.columns:
        st.warning("⚠️ 'Input Custom Field 1' column not found. Filename will use date only.")
    
    return True

def main():
    st.title("📱 Phone Number Processor")
    st.markdown("---")
    
    st.markdown("""
    This tool processes phone-enhanced CSV files to extract clean mobile phone numbers.
    
    **Processing Steps:**
    1. 🚫 Remove rows with 'DNC' in 'DNC/Litigator Scrub' column
    2. 📋 Keep only Phone1-3 and Phone1-3 Type columns
    3. 📚 Stack all phone data into two columns
    4. 📱 Keep only 'Mobile' phone types
    5. 🗑️ Remove phone type column
    6. 🔢 Extract digits-only phone numbers
    """)
    
    st.markdown("---")
    
    # File upload section
    st.header("📁 Upload Phone-Enhanced CSV")
    uploaded_file = st.file_uploader(
        "Choose your phone-enhanced CSV file",
        type=['csv'],
        help="Upload the CSV file from the third-party phone service"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} rows and {len(df.columns)} columns.")
            
            # Show preview of input data
            with st.expander("📊 Preview Input Data (First 5 rows)"):
                # Show only relevant columns for preview
                preview_cols = ["DNC/Litigator Scrub", "Phone1", "Phone1 Type", "Phone2", "Phone2 Type", "Phone3", "Phone3 Type"]
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
                        st.metric("Mobile Numbers Found", len(processed_df))
                    with col3:
                        conversion_rate = (len(processed_df) / len(df)) * 100 if len(df) > 0 else 0
                        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
                    
                    # Download section
                    st.header("💾 Download Clean Phone Numbers")
                    
                    # Convert DataFrame to CSV
                    csv_buffer = io.StringIO()
                    processed_df.to_csv(csv_buffer, index=False, header=False)  # No header, just phone numbers
                    csv_data = csv_buffer.getvalue()
                    
                    # Generate filename using date + custom field + "Mobiles"
                    output_filename = generate_output_filename(df)
                    
                    st.download_button(
                        label="📥 Download Mobile Phone Numbers CSV",
                        data=csv_data,
                        file_name=output_filename,
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    # Show filename info
                    st.info(f"📁 **Filename**: `{output_filename}`")
                    
                    # Show sample of what will be downloaded
                    st.info(f"📄 **Download Preview:** CSV file will contain {len(processed_df)} phone numbers (digits only, no headers)")
                    with st.expander("🔍 Sample Output (First 10 Numbers)"):
                        sample_numbers = processed_df['Column A'].head(10).tolist()
                        for i, number in enumerate(sample_numbers, 1):
                            st.text(f"{i:2d}. {number}")
                
                else:
                    st.error("❌ No mobile phone numbers found after processing. Check your data and try again.")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted and contains the expected columns.")
    
    else:
        st.info("👆 Please upload a phone-enhanced CSV file to get started.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>Phone Number Processor v1.0 | Built with Streamlit</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
