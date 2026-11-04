"""
Countries for the phone field: ISO code, name, dialling code and the allowed length of the
national number (digits after the dialling code, without a leading trunk 0). Used by the field
template (country picker) and by layout.forms.PhoneField on the server, so both check the same rule.
"""

# (code, name, dial, min_digits, max_digits)
COUNTRIES = [
    ("NP", "Nepal", "977", 8, 10),
    ("IN", "India", "91", 10, 10),
    ("CN", "China", "86", 11, 11),
    ("BD", "Bangladesh", "880", 10, 10),
    ("BT", "Bhutan", "975", 7, 8),
    ("LK", "Sri Lanka", "94", 9, 9),
    ("PK", "Pakistan", "92", 10, 10),
    ("MV", "Maldives", "960", 7, 7),
    ("AF", "Afghanistan", "93", 9, 9),
    ("TH", "Thailand", "66", 8, 9),
    ("MY", "Malaysia", "60", 9, 10),
    ("SG", "Singapore", "65", 8, 8),
    ("ID", "Indonesia", "62", 9, 12),
    ("PH", "Philippines", "63", 10, 10),
    ("VN", "Vietnam", "84", 9, 10),
    ("KH", "Cambodia", "855", 8, 9),
    ("MM", "Myanmar", "95", 8, 10),
    ("JP", "Japan", "81", 9, 10),
    ("KR", "South Korea", "82", 9, 10),
    ("HK", "Hong Kong", "852", 8, 8),
    ("TW", "Taiwan", "886", 9, 9),
    ("AE", "United Arab Emirates", "971", 8, 9),
    ("SA", "Saudi Arabia", "966", 9, 9),
    ("QA", "Qatar", "974", 8, 8),
    ("KW", "Kuwait", "965", 8, 8),
    ("OM", "Oman", "968", 8, 8),
    ("BH", "Bahrain", "973", 8, 8),
    ("IL", "Israel", "972", 8, 9),
    ("TR", "Turkey", "90", 10, 10),
    ("EG", "Egypt", "20", 10, 10),
    ("ZA", "South Africa", "27", 9, 9),
    ("NG", "Nigeria", "234", 10, 10),
    ("KE", "Kenya", "254", 9, 9),
    ("GB", "United Kingdom", "44", 10, 10),
    ("IE", "Ireland", "353", 9, 9),
    ("FR", "France", "33", 9, 9),
    ("DE", "Germany", "49", 10, 11),
    ("NL", "Netherlands", "31", 9, 9),
    ("BE", "Belgium", "32", 8, 9),
    ("CH", "Switzerland", "41", 9, 9),
    ("AT", "Austria", "43", 10, 11),
    ("IT", "Italy", "39", 9, 10),
    ("ES", "Spain", "34", 9, 9),
    ("PT", "Portugal", "351", 9, 9),
    ("SE", "Sweden", "46", 9, 9),
    ("NO", "Norway", "47", 8, 8),
    ("DK", "Denmark", "45", 8, 8),
    ("FI", "Finland", "358", 9, 10),
    ("PL", "Poland", "48", 9, 9),
    ("CZ", "Czechia", "420", 9, 9),
    ("GR", "Greece", "30", 10, 10),
    ("RU", "Russia", "7", 10, 10),
    ("UA", "Ukraine", "380", 9, 9),
    ("US", "United States", "1", 10, 10),
    ("CA", "Canada", "1", 10, 10),
    ("MX", "Mexico", "52", 10, 10),
    ("BR", "Brazil", "55", 10, 11),
    ("AR", "Argentina", "54", 10, 10),
    ("CL", "Chile", "56", 9, 9),
    ("CO", "Colombia", "57", 10, 10),
    ("PE", "Peru", "51", 9, 9),
    ("AU", "Australia", "61", 9, 9),
    ("NZ", "New Zealand", "64", 8, 10),
]

BY_CODE = {c[0]: c for c in COUNTRIES}


def default_code():
    from django.conf import settings
    code = str(settings.LAYOUT.get("PHONE_DEFAULT_COUNTRY", "NP")).upper()
    return code if code in BY_CODE else "NP"


def get(code):
    """(code, name, dial, min_digits, max_digits) for an ISO code; the default country for anything unknown."""
    return BY_CODE.get((code or "").upper()) or BY_CODE[default_code()]
