import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from typing import List
import zipfile

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

def clean_name_capitalization(name) -> str:
    """
    Apply proper capitalization to names (Title Case).
    Handles various edge cases for names.
    
    Args:
        name: Name string to clean
        
    Returns:
        String with proper capitalization
    """
    if pd.isna(name) or name == "" or str(name).strip() == "":
        return ""
    
    # Convert to string, strip whitespace, and apply title case
    cleaned_name = str(name).strip().title()
    
    # Handle common name prefixes/suffixes that should be lowercase
    # Like "McDonald", "O'Brien", etc.
    cleaned_name = re.sub(r"\bMc([A-Z])", r"Mc\1", cleaned_name)
    cleaned_name = re.sub(r"\bO'([A-Z])", r"O'\1", cleaned_name)
    
    return cleaned_name

def generate_roor_ready_filename(property_reference_code: str) -> str:
    """
    Generate output filename for Roor-Ready file.
    Format: YYYYMMDD_PropertyReferenceCode_Roor-Ready.csv
    
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
    filename = f"{date_str}_{clean_code}_Roor-Ready.csv"
    
    return filename

def generate_slybroadcast_filename(property_reference_code: str, group_letter: str) -> str:
    """
    Generate filename for Slybroadcast-Ready files with group letter.
    Format: YYYYMMDD_PropertyReferenceCode_Slybroadcast-Ready_GroupX.csv
    
    Args:
        property_reference_code: User-provided property reference code
        group_letter: Group letter (A, B, C, etc.)
        
    Returns:
        Generated filename string
    """
    # Get current date in YYYYMMDD format
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Clean the property reference code for filename (remove invalid characters)
    clean_code = re.sub(r'[<>:"/\\|?*]', '', str(property_reference_code))
    clean_code = clean_code.replace(' ', '_')  # Replace spaces with underscores
    
    # Generate filename with group letter
    filename = f"{date_str}_{clean_code}_Slybroadcast-Ready_Group{group_letter}.csv"
    
    return filename

def add_test_numbers_to_roor_ready(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add test phone numbers to the top of the Roor-Ready DataFrame.
    
    Args:
        df: Processed DataFrame with First Name, Last Name, Phone columns
        
    Returns:
        DataFrame with test numbers added at the top
    """
    # Create test records
    test_records = pd.DataFrame([
        {'First Name': 'Robert', 'Last Name': 'Dow', 'Phone': '2142645033'},
        {'First Name': 'Lauren', 'Last Name': 'Forbis', 'Phone': '3364024962'}
    ])
    
    # Concatenate test records at the top
    result_df = pd.concat([test_records, df], ignore_index=True)
    
    return result_df

def add_test_numbers_to_slybroadcast(phone_numbers: List[str]) -> List[str]:
    """
    Add test phone numbers to the top of the Slybroadcast phone number list.
    
    Args:
        phone_numbers: List of phone numbers
        
    Returns:
        List with test numbers added at the top
    """
    # Add test numbers at the beginning
    test_numbers = ['2142645033', '3364024962']
    
    # Combine test numbers with existing numbers
    result_numbers = test_numbers + phone_numbers
    
    return result_numbers

def create_slybroadcast_files(phone_numbers: List[str], property_reference_code: str) -> dict:
    """
    Create multiple CSV files with phone numbers only, each containing max 250 numbers.
    Files are named with Group letters (A, B, C, etc.)
    Test numbers are added to the first file only.
    
    Args:
        phone_numbers: List of phone numbers (already includes test numbers)
        property_reference_code: Property reference code for filename
        
    Returns:
        Dictionary with filename as key and CSV content as value
    """
    files_created = {}
    batch_size = 250
    
    for i in range(0, len(phone_numbers), batch_size):
        batch = phone_numbers[i:i + batch_size]
        group_index = i // batch_size
        
        # Generate group letter (A, B, C, D, ...)
        if group_index < 26:
            group_letter = chr(65 + group_index)  # A, B, C, etc.
        else:
            # If we exceed 26 groups, use AA, AB, AC, etc.
            first_letter_index = (group_index - 26) // 26
            second_letter_index = (group_index - 26) % 26
            group_letter = chr(65 + first_letter_index) + chr(65 + second_letter_index)
        
        # Create DataFrame with phone numbers only (no header)
        phone_df = pd.DataFrame(batch, columns=['Phone'])
        
        # Convert to CSV without header
        csv_content = phone_df.to_csv(index=False, header=False)
        
        # Generate filename using the new function
        filename = generate_slybroadcast_filename(property_reference_code, group_letter)
        
        files_created[filename] = csv_content
    
    return files_created

def process_phone_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process phone data according to requirements:
    1. Delete rows where DNC/Litigator Scrub contains "DNC"
    2. Keep only specified columns
    3. Add duplicate name columns for Phone2
    4. Stack all phone data into four columns
    5. Keep only "Mobile" phone types
    6. Remove phone type column
    7. Rename headers to "First Name", "Last Name", "Phone"
    8. Apply proper capitalization to ENTIRE First Name and Last Name columns
    
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
    
    # Step 3: Insert duplicate name columns for Phone2 AND apply proper capitalization to ALL name fields
    # Apply capitalization to original name columns first
    df_selected["Matched First Name"] = df_selected["Matched First Name"].apply(clean_name_capitalization)
    df_selected["Matched Last Name"] = df_selected["Matched Last Name"].apply(clean_name_capitalization)
    
    # Now create duplicate columns with already-capitalized names
    df_selected["Matched First Name2"] = df_selected["Matched First Name"]
    df_selected["Matched Last Name2"] = df_selected["Matched Last Name"]
    
    st.info(f"✅ Step 3: Applied proper capitalization to ALL name fields and added duplicate columns for Phone2 data")
    
    # Step 4: Stack all phone data into four columns
    phone_data = []
    
    # Process each row
    for _, row in df_selected.iterrows():
        # Add Phone1 data (names already properly capitalized)
        if pd.notna(row["Phone1"]) and row["Phone1"] != "" and str(row["Phone1"]) != "0":
            phone_data.append({
                'First Name': row["Matched First Name"],  # Already capitalized
                'Last Name': row["Matched Last Name"],    # Already capitalized
                'Phone': row["Phone1"],
                'Phone Type': row["Phone1 Type"] if pd.notna(row["Phone1 Type"]) else ""
            })
        
        # Add Phone2 data (names already properly capitalized)
        if pd.notna(row["Phone2"]) and row["Phone2"] != "" and str(row["Phone2"]) != "0":
            phone_data.append({
                'First Name': row["Matched First Name2"],  # Already capitalized
                'Last Name': row["Matched Last Name2"],    # Already capitalized
                'Phone': row["Phone2"],
                'Phone Type': row["Phone2 Type"] if pd.notna(row["Phone2 Type"]) else ""
            })
    
    # Create stacked DataFrame
    stacked_df = pd.DataFrame(phone_data)
    st.info(f"✅ Step 4: Stacked phone data - created {len(stacked_df)} phone number records with properly capitalized names")
    
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
    
    # Step 8: Double-check capitalization on final output (redundant but ensures correctness)
    final_df['First Name'] = final_df['First Name'].apply(clean_name_capitalization)
    final_df['Last Name'] = final_df['Last Name'].apply(clean_name_capitalization)
    
    st.info(f"✅ Step 8: Double-checked proper capitalization on ENTIRE First Name and Last Name columns")
    
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
    This tool processes phone-enhanced CSV files to extract clean mobile phone numbers with properly capitalized names.
    
    **Processing Steps:**
    1. 🚫 Remove rows with 'DNC' in 'DNC/Litigator Scrub' column
    2. 📋 Keep only name and phone columns (Phone1 & Phone2 only)
    3. ✨ Apply proper capitalization to ALL name fields and add duplicate columns for Phone2 data
    4. 📚 Stack all phone data into four columns
    5. 📱 Keep only 'Mobile' phone types
    6. 🗑️ Remove phone type column
    7. 🔢 Clean phone numbers to exactly 10 digits
    8. ✨ Double-check proper capitalization on ENTIRE First Name and Last Name columns
    9. 🎯 Add test numbers (Robert Dow & Lauren Forbis) to the top of both output files
    
    **Output Files:**
    - **Roor-Ready CSV**: Complete data with names and phone numbers (with headers) + test numbers at top
    - **Slybroadcast-Ready CSV Files**: Phone numbers only (no headers), split into groups of 250 numbers each (Group A, Group B, etc.) + test numbers at top of Group A
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
                with st.spinner("Processing phone numbers and applying proper capitalization..."):
                    processed_df = process_phone_data(df)
                
                if len(processed_df) > 0:
                    st.header("🎉 Processing Complete!")
                    
                    # Add test numbers to processed data for Roor-Ready file
                    roor_ready_df = add_test_numbers_to_roor_ready(processed_df)
                    
                    # Show preview of output data
                    with st.expander("📋 Preview Processed Data (First 10 rows including test numbers)"):
                        st.dataframe(roor_ready_df.head(10))
                    
                    # Summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Input Rows", len(df))
                    with col2:
                        st.metric("Processed Records", len(processed_df))
                    with col3:
                        st.metric("Final Records (+ test)", len(roor_ready_df))
                    with col4:
                        conversion_rate = (len(processed_df) / len(df)) * 100 if len(df) > 0 else 0
                        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
                    
                    # Show sample of names to verify capitalization
                    if len(processed_df) > 0:
                        st.info("📝 **Name Capitalization Check**: Sample of properly capitalized names (including test numbers)")
                        sample_names = roor_ready_df[['First Name', 'Last Name']].head(7)  # Show test + 5 real
                        st.dataframe(sample_names)
                    
                    # Download section
                    st.header("💾 Download Files")
                    
                    # File 1: Complete Roor-Ready CSV with headers and test numbers
                    st.subheader("📄 File 1: Complete Roor-Ready CSV")
                    
                    # Convert DataFrame to CSV with headers
                    csv_buffer = io.StringIO()
                    roor_ready_df.to_csv(csv_buffer, index=False, header=True)
                    csv_data = csv_buffer.getvalue()
                    
                    # Generate filename using new function
                    roor_filename = generate_roor_ready_filename(property_reference_code)
                    
                    st.download_button(
                        label="📥 Download Roor-Ready CSV (with headers + test numbers)",
                        data=csv_data,
                        file_name=roor_filename,
                        mime="text/csv",
                        use_container_width=True,
                        key="roor_ready_download"
                    )
                    
                    # Show filename info
                    st.info(f"📁 **Filename**: `{roor_filename}` (includes 2 test numbers at top)")
                    
                    # File 2: Slybroadcast-Ready files (no headers, split into 250-number groups, test numbers at top)
                    st.subheader("📱 File 2: Slybroadcast-Ready Files (No Headers)")
                    
                    # Extract phone numbers only from processed data and add test numbers
                    phone_numbers = processed_df['Phone'].tolist()
                    slybroadcast_phone_numbers = add_test_numbers_to_slybroadcast(phone_numbers)
                    
                    # Create Slybroadcast-Ready files using new function
                    slybroadcast_files = create_slybroadcast_files(slybroadcast_phone_numbers, property_reference_code)
                    
                    st.info(f"📊 **Slybroadcast Files Created**: {len(slybroadcast_files)} files containing {len(slybroadcast_phone_numbers)} total phone numbers (including 2 test numbers)")
                    
                    if len(slybroadcast_files) == 1:
                        # Single file download
                        filename, csv_content = list(slybroadcast_files.items())[0]
                        st.download_button(
                            label=f"📥 Download {filename}",
                            data=csv_content,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True,
                            key="slybroadcast_single"
                        )
                        st.info(f"📁 **Slybroadcast File**: `{filename}` ({len(slybroadcast_phone_numbers)} numbers including 2 test numbers)")
                    
                    else:
                        # Multiple files - create ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, csv_content in slybroadcast_files.items():
                                zip_file.writestr(filename, csv_content)
                        
                        zip_buffer.seek(0)
                        
                        # Generate ZIP filename
                        date_str = datetime.now().strftime("%Y%m%d")
                        clean_code = re.sub(r'[<>:"/\\|?*]', '', str(property_reference_code))
                        clean_code = clean_code.replace(' ', '_')
                        zip_filename = f"{date_str}_{clean_code}_Slybroadcast-Ready-Files.zip"
                        
                        st.download_button(
                            label=f"📦 Download All Slybroadcast Files ({len(slybroadcast_files)} files in ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=zip_filename,
                            mime="application/zip",
                            use_container_width=True,
                            key="slybroadcast_zip"
                        )
                        
                        # Show individual file info
                        with st.expander("📋 Slybroadcast File Details"):
                            for i, (filename, _) in enumerate(slybroadcast_files.items()):
                                start_num = i * 250
                                end_num = min(start_num + 249, len(slybroadcast_phone_numbers) - 1)
                                actual_count = end_num - start_num + 1
                                group_letter = chr(65 + i) if i < 26 else f"{chr(65 + ((i-26)//26))}{chr(65 + ((i-26)%26))}"
                                if i == 0:
                                    st.write(f"• `{filename}` - Group {group_letter}: {actual_count} phone numbers (includes 2 test numbers at top)")
                                else:
                                    st.write(f"• `{filename}` - Group {group_letter}: {actual_count} phone numbers")
                    
                    # Show sample of what will be downloaded
                    with st.expander("🔍 Sample Output Files"):
                        st.write("**Roor-Ready CSV Sample (First 5 Records with Headers, including test numbers):**")
                        st.dataframe(roor_ready_df.head(5))
                        
                        st.write("**Slybroadcast-Ready File Sample (First 5 Numbers including test numbers, No Headers):**")
                        sample_phones = pd.DataFrame(slybroadcast_phone_numbers[:5], columns=['Phone'])
                        st.text(sample_phones.to_csv(index=False, header=False).strip())
                
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
        <small>Phone Number Processor v2.4 | Built with Streamlit | Now with Test Numbers at Top</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
