from datetime import datetime, timedelta
import copy
import calendar

vaccine_schedule = [
    # Birth
    {
        'id': 'VAC001',
        'name': 'BCG',
        'fullName': 'Bacillus Calmette-Guérin',
        'description': 'Protects against tuberculosis',
        'ageInMonths': 0,
        'ageLabel': 'At Birth',
        'category': 'Birth',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC002',
        'name': 'OPV 0',
        'fullName': 'Oral Polio Vaccine (Birth Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 0,
        'ageLabel': 'At Birth',
        'category': 'Birth',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC003',
        'name': 'Hepatitis B (Birth Dose)',
        'fullName': 'Hepatitis B Vaccine',
        'description': 'Protects against Hepatitis B infection',
        'ageInMonths': 0,
        'ageLabel': 'At Birth',
        'category': 'Birth',
        'mandatory': True,
        'icon': '💉',
    },

    # 6 Weeks
    {
        'id': 'VAC004',
        'name': 'DTwP 1 / DTaP 1',
        'fullName': 'Diphtheria, Tetanus, Pertussis (1st Dose)',
        'description': 'Protects against diphtheria, tetanus, and whooping cough',
        'ageInMonths': 1.5,
        'ageLabel': '6 Weeks',
        'category': '6 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC005',
        'name': 'IPV 1',
        'fullName': 'Inactivated Polio Vaccine (1st Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 1.5,
        'ageLabel:': '6 Weeks',
        'category': '6 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC006',
        'name': 'Hib 1',
        'fullName': 'Haemophilus Influenzae Type B (1st Dose)',
        'description': 'Protects against Haemophilus influenzae type B',
        'ageInMonths': 1.5,
        'ageLabel': '6 Weeks',
        'category': '6 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC007',
        'name': 'Rotavirus 1',
        'fullName': 'Rotavirus Vaccine (1st Dose)',
        'description': 'Protects against rotavirus infection',
        'ageInMonths': 1.5,
        'ageLabel': '6 Weeks',
        'category': '6 Weeks',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC008',
        'name': 'PCV 1',
        'fullName': 'Pneumococcal Conjugate Vaccine (1st Dose)',
        'description': 'Protects against pneumococcal disease',
        'ageInMonths': 1.5,
        'ageLabel': '6 Weeks',
        'category': '6 Weeks',
        'mandatory': True,
        'icon': '💉',
    },

    # 10 Weeks
    {
        'id': 'VAC009',
        'name': 'DTwP 2 / DTaP 2',
        'fullName': 'Diphtheria, Tetanus, Pertussis (2nd Dose)',
        'description': 'Protects against diphtheria, tetanus, and whooping cough',
        'ageInMonths': 2.5,
        'ageLabel': '10 Weeks',
        'category': '10 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC010',
        'name': 'IPV 2',
        'fullName': 'Inactivated Polio Vaccine (2nd Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 2.5,
        'ageLabel': '10 Weeks',
        'category': '10 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC011',
        'name': 'Hib 2',
        'fullName': 'Haemophilus Influenzae Type B (2nd Dose)',
        'description': 'Protects against Haemophilus influenzae type B',
        'ageInMonths': 2.5,
        'ageLabel': '10 Weeks',
        'category': '10 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC012',
        'name': 'Rotavirus 2',
        'fullName': 'Rotavirus Vaccine (2nd Dose)',
        'description': 'Protects against rotavirus infection',
        'ageInMonths': 2.5,
        'ageLabel': '10 Weeks',
        'category': '10 Weeks',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC013',
        'name': 'PCV 2',
        'fullName': 'Pneumococcal Conjugate Vaccine (2nd Dose)',
        'description': 'Protects against pneumococcal disease',
        'ageInMonths': 2.5,
        'ageLabel': '10 Weeks',
        'category': '10 Weeks',
        'mandatory': True,
        'icon': '💉',
    },

    # 14 Weeks
    {
        'id': 'VAC014',
        'name': 'DTwP 3 / DTaP 3',
        'fullName': 'Diphtheria, Tetanus, Pertussis (3rd Dose)',
        'description': 'Protects against diphtheria, tetanus, and whooping cough',
        'ageInMonths': 3.5,
        'ageLabel': '14 Weeks',
        'category': '14 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC015',
        'name': 'IPV 3',
        'fullName': 'Inactivated Polio Vaccine (3rd Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 3.5,
        'ageLabel': '14 Weeks',
        'category': '14 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC016',
        'name': 'Hib 3',
        'fullName': 'Haemophilus Influenzae Type B (3rd Dose)',
        'description': 'Protects against Haemophilus influenzae type B',
        'ageInMonths': 3.5,
        'ageLabel': '14 Weeks',
        'category': '14 Weeks',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC017',
        'name': 'Rotavirus 3',
        'fullName': 'Rotavirus Vaccine (3rd Dose)',
        'description': 'Protects against rotavirus infection',
        'ageInMonths': 3.5,
        'ageLabel': '14 Weeks',
        'category': '14 Weeks',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC018',
        'name': 'PCV 3',
        'fullName': 'Pneumococcal Conjugate Vaccine (3rd Dose)',
        'description': 'Protects against pneumococcal disease',
        'ageInMonths': 3.5,
        'ageLabel': '14 Weeks',
        'category': '14 Weeks',
        'mandatory': True,
        'icon': '💉',
    },

    # 6 Months
    {
        'id': 'VAC019',
        'name': 'OPV 1',
        'fullName': 'Oral Polio Vaccine (1st Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 6,
        'ageLabel': '6 Months',
        'category': '6 Months',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC020',
        'name': 'Hepatitis B 1',
        'fullName': 'Hepatitis B Vaccine (1st Dose)',
        'description': 'Protects against Hepatitis B infection',
        'ageInMonths': 6,
        'ageLabel': '6 Months',
        'category': '6 Months',
        'mandatory': True,
        'icon': '💉',
    },

    # 9 Months
    {
        'id': 'VAC021',
        'name': 'OPV 2',
        'fullName': 'Oral Polio Vaccine (2nd Dose)',
        'description': 'Protects against polio',
        'ageInMonths': 9,
        'ageLabel': '9 Months',
        'category': '9 Months',
        'mandatory': True,
        'icon': '💧',
    },
    {
        'id': 'VAC022',
        'name': 'MMR 1',
        'fullName': 'Measles, Mumps, Rubella (1st Dose)',
        'description': 'Protects against measles, mumps, and rubella',
        'ageInMonths': 9,
        'ageLabel': '9 Months',
        'category': '9 Months',
        'mandatory': True,
        'icon': '💉',
    },

    # 12 Months
    {
        'id': 'VAC023',
        'name': 'Hepatitis A 1',
        'fullName': 'Hepatitis A Vaccine (1st Dose)',
        'description': 'Protects against Hepatitis A infection',
        'ageInMonths': 12,
        'ageLabel': '12 Months',
        'category': '12 Months',
        'mandatory': False,
        'icon': '💉',
    },

    # 15 Months
    {
        'id': 'VAC024',
        'name': 'MMR 2',
        'fullName': 'Measles, Mumps, Rubella (2nd Dose)',
        'description': 'Protects against measles, mumps, and rubella',
        'ageInMonths': 15,
        'ageLabel': '15 Months',
        'category': '15 Months',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC025',
        'name': 'Varicella 1',
        'fullName': 'Varicella (Chickenpox) Vaccine (1st Dose)',
        'description': 'Protects against chickenpox',
        'ageInMonths': 15,
        'ageLabel': '15 Months',
        'category': '15 Months',
        'mandatory': False,
        'icon': '💉',
    },
    {
        'id': 'VAC026',
        'name': 'PCV Booster',
        'fullName': 'Pneumococcal Conjugate Vaccine (Booster)',
        'description': 'Booster dose for pneumococcal disease',
        'ageInMonths': 15,
        'ageLabel': '15 Months',
        'category': '15 Months',
        'mandatory': True,
        'icon': '💉',
    },

    # 16-18 Months
    {
        'id': 'VAC027',
        'name': 'DTwP B1 / DTaP B1',
        'fullName': 'Diphtheria, Tetanus, Pertussis (Booster 1)',
        'description': 'Booster dose for diphtheria, tetanus, and whooping cough',
        'ageInMonths': 18,
        'ageLabel': '16-18 Months',
        'category': '16-18 Months',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC028',
        'name': 'IPV B1',
        'fullName': 'Inactivated Polio Vaccine (Booster 1)',
        'description': 'Booster dose for polio',
        'ageInMonths': 18,
        'ageLabel': '16-18 Months',
        'category': '16-18 Months',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC029',
        'name': 'Hib B1',
        'fullName': 'Haemophilus Influenzae Type B (Booster 1)',
        'description': 'Booster dose for Haemophilus influenzae type B',
        'ageInMonths': 18,
        'ageLabel': '16-18 Months',
        'category': '16-18 Months',
        'mandatory': True,
        'icon': '💉',
    },
    {
        'id': 'VAC030',
        'name': 'Hepatitis A 2',
        'fullName': 'Hepatitis A Vaccine (2nd Dose)',
        'description': 'Second dose for Hepatitis A',
        'ageInMonths': 18,
        'ageLabel': '16-18 Months',
        'category': '16-18 Months',
        'mandatory': False,
        'icon': '💉',
    },

    # 24 Months (2 Years)
    {
        'id': 'VAC031',
        'name': 'Typhoid Conjugate',
        'fullName': 'Typhoid Conjugate Vaccine',
        'description': 'Protects against typhoid fever',
        'ageInMonths': 24,
        'ageLabel': '24 Months (2 Years)',
        'category': '24 Months',
        'mandatory': False,
        'icon': '💉',
    },
]

def get_vaccines_by_category(category: str):
    return [v for v in vaccine_schedule if v['category'] == category]

def get_vaccines_by_age(age_in_months: float):
    return [v for v in vaccine_schedule if v['ageInMonths'] == age_in_months]

def get_mandatory_vaccines():
    return [v for v in vaccine_schedule if v['mandatory']]

def get_child_vaccine_schedule(date_of_birth):
    if isinstance(date_of_birth, str):
        # Remove any Zulu time designator and milliseconds/times
        clean_dob = date_of_birth.replace("Z", "")
        if "T" in clean_dob:
            clean_dob = clean_dob.split("T")[0]
        dob = datetime.strptime(clean_dob, "%Y-%m-%d")
    elif isinstance(date_of_birth, datetime):
        dob = date_of_birth
    else:
        # Default or fallback
        dob = datetime.utcnow()

    today = datetime.utcnow()
    schedule = []
    
    for vaccine in vaccine_schedule:
        vac_copy = copy.deepcopy(vaccine)
        
        # Calculate new year and month
        months = int(vac_copy['ageInMonths'])
        # Handle fractional months (like 1.5, 2.5, 3.5)
        days = int((vac_copy['ageInMonths'] - months) * 30.437)
        
        new_year = dob.year + (dob.month + months - 1) // 12
        new_month = (dob.month + months - 1) % 12 + 1
        
        # Guard against invalid days in the new month (e.g. Feb 31)
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        target_day = min(dob.day, last_day_of_month)
        
        due_date = datetime(new_year, new_month, target_day)
        if days > 0:
            due_date += timedelta(days=days)
            
        # Standardize format
        due_date = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        vac_copy['dueDate'] = due_date.isoformat() + 'Z'
        vac_copy['isPast'] = due_date < today
        vac_copy['isUpcoming'] = due_date >= today
        vac_copy['status'] = 'Pending'
        
        schedule.append(vac_copy)
        
    return schedule
