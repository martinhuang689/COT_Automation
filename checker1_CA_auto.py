import re
from datetime import date


# Helper function to extract a field from text using a pattern
def extract_field(text, pattern, split_tab=False):
    """Extract a field from text using a pattern, optionally splitting by tab."""
    match = re.search(pattern, text)
    if match:
        value = match.group(1).strip()
        if split_tab:
            value = value.split('\t')[0].strip()
        return value
    return "Not found"

# Function to extract all fields and counts
def extract_all_fields(text):
    """Extract all required fields and counts from the text, returning a dictionary."""
    # Define regular expression patterns
    field_configs = {
        "name": {"pattern": r'姓名：\s*([^：\n]+)', "split_tab": False},
        "nameENG": {"pattern": r'姓名拼音：\s*([^：\n]+)', "split_tab": False},
        "pass_address": {"pattern": r'證件住址：\s*([^：\n]+)', "split_tab": True},
        "res_address": {"pattern": r'住宅地址：\s*([^：\n]+)', "split_tab": True},
        "comp_address": {"pattern": r'公司地址：\s*([^：\n]+)', "split_tab": True},
        "comp_name": {"pattern": r'公司名稱：\s*([^：\n]+)', "split_tab": False},
        "emp_status": {"pattern": r'工作狀況：\s*([^：\n]+)', "split_tab": True},
        "industry": {"pattern": r'行業：\s*([^：\n]+)', "split_tab": True},
        "occupation": {"pattern": r'職業：\s*([^：\n]+)', "split_tab": False},
        "tax_id": {"pattern": r'稅務編號：\s*(\d+)', "split_tab": False},
        "email": {"pattern": r'電子郵箱：\s*(\S+)', "split_tab": False},
        "sources": {"pattern": r'资金来源\s*([^：\n]+)', "split_tab": True},
        "passportdate": {"pattern": r'證件有效期：\s*([^：\n]+)', "split_tab": True},
        "liquidasset": {"pattern": r'流动资产\(港币\)\s*([^：\n]+)', "split_tab": True},
        "networth": {"pattern": r'资产净值\(港币\)\s*([^：\n]+)', "split_tab": True},
        "income": {"pattern": r'年薪\(港币\)\s*([^：\n]+)', "split_tab": True},
        "duration": {"pattern": r'受雇年期：\s*([^：\n]+)', "split_tab": True},
    }

    # Fields that require counting
    fields_to_count = ["tax_id", "res_address"]

    # Extract all fields
    data = {}
    for field, config in field_configs.items():
        data[field] = extract_field(text, config["pattern"], config["split_tab"])

    # Count occurrences for specified fields
    for field in fields_to_count:
        if data[field] != "Not found":
            data[f"{field}_count"] = len(re.findall(re.escape(data[field]), text))
        else:
            data[f"{field}_count"] = 0

    return data

def extract_numbers(s):
    """Extract all numbers from the string, removing commas."""
    number_strings = re.findall(r'\d{1,3}(?:,\d{3})*', s)
    numbers = [int(num.replace(',', '')) for num in number_strings]
    return numbers

def extract_number(s):
    """Extract the largest number from the string."""
    numbers = extract_numbers(s)
    if numbers:
        return max(numbers)
    else:
        return 0

# Function to process financial data (assumed from original context)
def extract_largest_number(liquidasset, networth, income, duration):
    """Process financial data and perform comparisons."""
    num1 = extract_number(liquidasset)
    num2 = extract_number(networth)
    num3 = extract_number(income)
    if duration == "Not found":
        num4 = 0
    else:
        try:
            num4 = int(duration)
        except ValueError:
            num4 = 0
    return num1, num2, num1 <= num2, num3, num3 * num4, num3 * num4 >= num2, num4

# Function to check if a date is valid and in the future or today (assumed from original context)
def check_date(date_str):
    """Check if a date is valid and in the future or today."""
    today = date.today()
    try:
        given_date = date.fromisoformat(date_str)
        return given_date >= today
    except ValueError:
        return "Invalid date format"
