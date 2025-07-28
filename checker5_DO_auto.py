from datetime import datetime
import colorama
from colorama import Fore, Style
import pyperclip

def parse_value(value_str):
    """Parse financial values that may be in range, inequality, or specific formats."""
    value_str = value_str.replace("HKD", "").replace(",", "").strip()
    if value_str.startswith("<"):
        upper = int(value_str[1:]) - 1
        return (0, upper)
    elif "–" in value_str:
        lower, upper = map(int, value_str.split("–"))
        return (lower, upper)
    else:
        val = int(value_str)
        return (val, val)

def parse_document(document):
    """Parse the document string into a dictionary of key-value pairs."""
    data = {}
    for line in document.splitlines():
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        for i in range(0, len(parts), 2):
            key = parts[i]
            value = parts[i+1] if i+1 < len(parts) else ''
            data[key] = value
    return data

def get_estimated_net_worth(data):
    """Get the effective EstimatedNetWorth, using EstimatedNetWorthOthers if EstimatedNetWorth is 'OTHER'."""
    estimated_str = data.get('EstimatedNetWorth', '')
    if estimated_str == 'OTHER':
        return data.get('EstimatedNetWorthOthers', '')
    else:
        return estimated_str

def check_count(document, key, data):
    """Check if a specific value appears 3 or more times in the document."""
    value = data.get(key, '')
    if not value:
        return False
    words = document.split()
    count = words.count(value)
    return count >= 3, count, value

def check_liquid_vs_estimated(data):
    """Check if LiquidNetWorth <= EstimatedNetWorth."""
    liquid_str = data.get('LiquidNetWorth', '')
    estimated_str = get_estimated_net_worth(data)
    if not liquid_str or not estimated_str:
        return False
    try:
        _, liquid_upper = parse_value(liquid_str)
        _, estimated_upper = parse_value(estimated_str)
        return liquid_upper <= estimated_upper
    except ValueError:
        return False

def check_income_times_years_ge_estimated(data):
    """Check if AnnualIncomeLevel * YearsOfService >= EstimatedNetWorth and provide calculation details."""
    income_str = data.get('AnnualIncomeLevel', '')
    years_str = data.get('YearsOfService', '')
    estimated_str = get_estimated_net_worth(data)
    if not income_str or not years_str or not estimated_str:
        return False, "Missing data"
    try:
        lower_income, upper_income = parse_value(income_str)
        years = int(years_str)
        lower_estimated, upper_estimated = parse_value(estimated_str)
        max_product = upper_income * years
        result = max_product >= lower_estimated
        calculation_string = f"{upper_income} * {years} = {max_product} >= {lower_estimated}"
        return result, calculation_string
    except ValueError:
        return False, "Invalid data"

def check_income_sources_if_needed(data):
    """If AnnualIncomeLevel * YearsOfService < EstimatedNetWorth, check income sources."""
    sources = [
        data.get('InvestmentEarning', '') == 'TRUE',
        data.get('PreviousJobs', '') == 'TRUE',
        data.get('ProvidedByFamilyMember', '') == 'TRUE',
        data.get('RentalIncome', '') == 'TRUE',
        data.get('OtherIncome', '') == 'TRUE'
    ]
    return any(sources)

def check_saving_from_salary_if_employed(data):
    """If EmploymentType is EMPLOYED, check if SavingFromSalary is TRUE."""
    employment_type = data.get('EmploymentType', '')
    saving_from_salary = data.get('Saving From Salary', '')
    if employment_type == 'EMPLOYED':
        return True, saving_from_salary == 'TRUE'
    else:
        return "NA"

def check_is_not_chinese(data):
    """Check if IsNotChinese is FALSE."""
    is_not_chinese = data.get('IsNotChinese', '')
    return is_not_chinese == 'FALSE'

def check_margin_false_count(document):
    """Check if 'FALSE -' appears exactly 4 times after 'Margin Question Declaration'."""
    count = document.count("FALSE -")
    return count == 4

def process_client_data(document):
    """Process client data and return results of all checks and required outcomes."""
    data = parse_document(document)
    
    # Perform checks
    income_ge_estimated, income_calculation = check_income_times_years_ge_estimated(data)
    results = {
        'surname_check': check_count(document, 'Surname', data),
        'clientname_check': check_count(document, 'ClientName', data),
        'passportno_check': check_count(document, 'NRICPassportNo', data),
        'liquid_vs_estimated': check_liquid_vs_estimated(data),
        'income_times_years_ge_estimated': income_ge_estimated,
        'income_calculation': income_calculation,
        'income_sources_check': check_income_sources_if_needed(data),
        'saving_from_salary_check': check_saving_from_salary_if_employed(data),
        'is_not_chinese_check': check_is_not_chinese(data),
        'margin_false_count_check': check_margin_false_count(document)
    }
    
    # Extract outcomes
    outcomes = {
        'surname': data.get('Surname', ''),
        'clientname': data.get('ClientName', ''),
        'dateofbirth': data.get('DateOfBirth', ''),
        'noneenglishname': data.get('NoneEnglishName', data.get('NonEnglishName', '')),
        'nationality': data.get('Nationality', ''),
        'occupation': data.get('Occupation', ''),
        'employment_type': data.get('EmploymentType', ''),
        'employment_industry': data.get('EmploymentIndustry', ''),
        'employer_name': data.get('EmployerName', ''),
        'employer_address': ' '.join([
            data.get('EmployerAddress1', ''),
            data.get('EmployerAddress2', ''),
            data.get('EmployerAddress3', '')
        ]).strip(),
        'residential_address': ' '.join([
            data.get('ResidentialAddress1', ''),
            data.get('ResidentialAddress2', ''),
            data.get('ResidentialAddress3', '')
        ]).strip(),
        'designated_bank_name': data.get('DesignatedBankName1', ''),
        'designated_bank_number': data.get('DesignatedBankAccountNo1', ''),
        'NRICPassportNo': data.get('NRICPassportNo', ''),
        'aml_remark': data.get('AML Remark', '')
    }
    
    return results, outcomes

def print_results(results, outcomes):
    """Print the results of checks and outcomes."""
    print(f"Surname appears 3 times or more: {Fore.GREEN if results['surname_check'][0] else Fore.RED}{results['surname_check']}{Style.RESET_ALL}")
    print(f"Client name appears 3 times or more: {Fore.GREEN if results['clientname_check'][0] else Fore.RED}{results['clientname_check']}{Style.RESET_ALL}")
    print(f"Passport number appears 3 times or more: {Fore.GREEN if results['passportno_check'][0] else Fore.RED}{results['passportno_check']}{Style.RESET_ALL}")
    print(f"LiquidNetWorth <= EstimatedNetWorth: {Fore.GREEN if results['liquid_vs_estimated'] else Fore.RED}{results['liquid_vs_estimated']}{Style.RESET_ALL}")
    print(f"AnnualIncomeLevel * YearsOfService >= EstimatedNetWorth: ({results['income_calculation']}) {Fore.GREEN if results['income_times_years_ge_estimated'] else Fore.RED}{results['income_times_years_ge_estimated']}{Style.RESET_ALL}")
    print(f"check income sources: {Fore.GREEN if results['income_sources_check'] else Fore.RED}{results['income_sources_check']}{Style.RESET_ALL}")
    print(f"If EmploymentType = EMPLOYED, SavingFromSalary = TRUE: {Fore.RED if results['saving_from_salary_check']=='NA' else Fore.GREEN}{results['saving_from_salary_check']}{Style.RESET_ALL}")
    print(f"IsNotChinese = FALSE: {Fore.GREEN if results['is_not_chinese_check'] else Fore.RED}{results['is_not_chinese_check']}{Style.RESET_ALL}")
    print(f"Count of FALSE after 'Margin Question Declaration' is 4: {Fore.GREEN if results['margin_false_count_check'] else Fore.RED}{results['margin_false_count_check']}{Style.RESET_ALL}")
    
    # Build a single string with all the output
    output = f"\nName: {outcomes['surname']} {outcomes['clientname']}\n"
    output += f"Non-English Name: {outcomes['noneenglishname']}\n"
    output += f"Nationality: {outcomes['nationality']}\n"
    output += f"Date of Birth: {outcomes['dateofbirth']}\n"
    output += f"Occupation: {outcomes['occupation']}\n"
    output += f"Employment Type: {outcomes['employment_type']}\n"
    output += f"Employment Industry: {outcomes['employment_industry']}\n"
    output += f"Employer Name: {outcomes['employer_name']}\n"
    
    # Print the output in yellow using ANSI escape codes
    print("\033[33m" + output + "\033[0m")
    
    print(f"Residential Address: {outcomes['residential_address']}")
    are_same = outcomes['employer_address'] != outcomes['residential_address']
    print(f"Employer Address: {outcomes['employer_address']}, check same address: {Fore.GREEN if are_same else Fore.RED}{are_same}{Style.RESET_ALL}")
    print(f"Designated Bank Name: {outcomes['designated_bank_name']}")
    print(f"Designated Bank Number: {outcomes['designated_bank_number']}")
    print(f"NRICPassportNo: {outcomes['NRICPassportNo']}")
    
    # Construct the sentence
    parts = ["\nGood Fund (Auto FPS)"]
    
    # AML phrase
    aml_remark = outcomes.get('aml_remark', '')
    if "MED" in aml_remark:
        parts.append("AML med")
    elif "HIGH" in aml_remark:
        if "INDUSTRIES" in aml_remark:
            parts.append("AML high, industry")
        else:
            parts.append("AML high, DJ hit")
    
    # EmploymentType phrase
    employment_type = outcomes.get('employment_type', '')
    employment_phrases = {
        'UNEMPLOYED': 'no job',
        'HOMEMAKER': 'homemaker',
        'RETIRED': 'retired',
        'SELF-EMPLOYED': 'self-employed',
        'STUDENT': 'student',
        'INVESTOR': 'investor'
    }
    if employment_type in employment_phrases:
        parts.append(employment_phrases[employment_type])
    
    # Mainland if Nationality is CHINA
    if outcomes.get('nationality', '') == "CHINA":
        parts.append("mainland")
    
    # Fixed phrases and date
    parts.append("non-F2F")
    parts.append("martin")
    today = datetime.today()
    date_str = f"{today.day}/{today.month}"
    parts.append(date_str)
    
    # Join and print
    print(Fore.YELLOW + parts[0] + Style.RESET_ALL + ", " + (Fore.GREEN if 'MED' in aml_remark else Fore.RED) + ", ".join(parts[1:]) + Style.RESET_ALL)
    
    # Handle clipboard copying
    text = outcomes['NRICPassportNo']
    pyperclip.copy(text)