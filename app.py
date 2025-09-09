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
    1. Delete rows where DNC/Litigator
