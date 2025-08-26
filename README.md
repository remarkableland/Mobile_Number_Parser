# Mobile_Number_Parser
Parses Mobile Numbers from Direct Skip

# Phone Number Processor

A Streamlit web application that processes phone-enhanced CSV files to extract clean mobile phone numbers for marketing campaigns.

## Features

- **DNC Filtering**: Automatically removes records flagged with 'DNC' in the DNC/Litigator Scrub column
- **Phone Stacking**: Combines Phone1-3 data into a single list for easier processing
- **Mobile-Only Filter**: Keeps only phone numbers marked as 'Mobile' type
- **Clean Output**: Generates digits-only phone numbers ready for dialing systems
- **Data Validation**: Validates input files and provides helpful error messages
- **Preview Functionality**: Shows preview of both input and output data
- **Processing Statistics**: Displays conversion rates and processing metrics

## Processing Steps

The application follows these exact steps:

1. **Remove DNC Records**: Deletes all rows where "DNC" appears in the "DNC/Litigator Scrub" column
2. **Column Selection**: Keeps only Phone1, Phone1 Type, Phone2, Phone2 Type, Phone3, Phone3 Type columns
3. **Data Stacking**: Stacks all phone data into Column A (numbers) and Column B (types)
4. **Mobile Filter**: Keeps only records where phone type is "Mobile"
5. **Type Removal**: Deletes Column B (phone types)
6. **Number Cleaning**: Extracts digits-only phone numbers for final output

## Required Input Columns

Your input CSV must contain these columns:
- `DNC/Litigator Scrub`
- `Phone1` and `Phone1 Type`
- `Phone2` and `Phone2 Type` 
- `Phone3` and `Phone3 Type`

## Installation

### Local Development

1. Clone this repository:
```bash
git clone <your-repo-url>
cd phone-number-processor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Deploy the app by selecting `app.py` as your main file

## Usage

1. **Upload CSV**: Upload your phone-enhanced CSV file from the third-party service
2. **Review Processing**: Watch the step-by-step processing with live statistics
3. **Preview Results**: Review the cleaned mobile phone numbers
4. **Download**: Get your final CSV with digits-only mobile numbers

## Output Format

The final CSV contains:
- **No headers** - just clean phone numbers
- **Digits only** - no formatting, spaces, or special characters
- **Mobile numbers only** - residential and other types filtered out
- **DNC compliant** - all DNC flagged records removed

## File Structure

```
phone-number-processor/
│
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore file
```

## Example Workflow

1. **Input**: CSV with mixed phone types from third-party service
2. **Processing**: App filters, stacks, and cleans the data
3. **Output**: Clean CSV with mobile numbers ready for dialing

```
Input:  Smith,John,5551234567,Mobile,5559876543,Residential,5555555555,Mobile
Output: 5551234567
        5555555555
```

## Error Handling

The application handles:
- Missing required columns
- Invalid file formats
- Empty phone numbers
- Corrupted data
- No mobile numbers found

## Requirements

- Python 3.8 or higher
- Streamlit 1.28.0 or higher
- Pandas 2.0.0 or higher

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please create an issue in the GitHub repository.
