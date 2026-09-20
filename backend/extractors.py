
import re
from typing import Optional, Dict, Any, Tuple


# ============================================================
# PROPERTY TYPES
# ============================================================

PROPERTY_TYPES = {
    "house": "House",
    "home": "House",
    "apartment": "Apartment",
    "flat": "Apartment",
    "duplex": "Duplex",
    "bungalow": "Bungalow",
    "terrace": "Terrace",
    "terraced": "Terrace",
    "semi detached": "Semi-Detached",
    "semi-detached": "Semi-Detached",
    "detached": "Detached",
    "land": "Land",
    "plot": "Land",
    "commercial": "Commercial Property",
    "office": "Office",
    "shop": "Shop",
    "warehouse": "Warehouse",
    "hotel": "Hotel",
}


# ============================================================
# NIGERIAN STATES
# ============================================================

NIGERIAN_STATES = [
    "Abia",
    "Adamawa",
    "Akwa Ibom",
    "Anambra",
    "Bauchi",
    "Bayelsa",
    "Benue",
    "Borno",
    "Cross River",
    "Delta",
    "Ebonyi",
    "Edo",
    "Ekiti",
    "Enugu",
    "Gombe",
    "Imo",
    "Jigawa",
    "Kaduna",
    "Kano",
    "Katsina",
    "Kebbi",
    "Kogi",
    "Kwara",
    "Lagos",
    "Nasarawa",
    "Niger",
    "Ogun",
    "Ondo",
    "Osun",
    "Oyo",
    "Plateau",
    "Rivers",
    "Sokoto",
    "Taraba",
    "Yobe",
    "Zamfara",
    "Federal Capital Territory",
]


# ============================================================
# NIGERIAN CITIES
# ============================================================

NIGERIAN_CITIES = [
    "Uyo",
    "Eket",
    "Ikot Ekpene",
    "Oron",
    "Abak",
    "Lagos",
    "Ikeja",
    "Lekki",
    "Ajah",
    "Victoria Island",
    "Ikoyi",
    "Yaba",
    "Surulere",
    "Abuja",
    "Gwarinpa",
    "Maitama",
    "Wuse",
    "Asokoro",
    "Kaduna",
    "Kano",
    "Ibadan",
    "Port Harcourt",
    "Benin City",
    "Enugu",
    "Owerri",
    "Calabar",
    "Warri",
    "Asaba",
    "Aba",
    "Umuahia",
    "Onitsha",
    "Awka",
    "Jos",
    "Ilorin",
    "Abeokuta",
    "Akure",
    "Osogbo",
    "Ado Ekiti",
    "Bauchi",
    "Maiduguri",
    "Sokoto",
    "Gombe",
    "Yola",
    "Makurdi",
    "Minna",
    "Lokoja",
    "Katsina",
    "Damaturu",
    "Jalingo",
    "Birnin Kebbi",
    "Gusau",
]


ALL_LOCATIONS = NIGERIAN_STATES + NIGERIAN_CITIES


# ============================================================
# NUMBER WORDS
# ============================================================

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


# ============================================================
# CONVERSATION QUESTIONS
# ============================================================

QUESTIONS = [
    ("purpose", "Are you looking to buy, rent, or invest?"),
    ("location", "Which location are you interested in?"),
    ("property_type", "What type of property are you looking for?"),
    ("budget", "What is your budget?"),
    (
        "timeline",
        "When are you looking to move or complete the purchase?",
    ),
    ("name", "May I have your name?"),
    ("phone", "What is the best phone number to reach you?"),
    ("email", "What is your email address?"),
]


# ============================================================
# CLEAN TEXT
# ============================================================

def clean(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# EMAIL
# ============================================================

def extract_email(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(0).lower().strip()


# ============================================================
# PHONE
# ============================================================

def extract_phone(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    # International number.
    # Example: +44 7911 123456

    international = re.search(
        r"\+\d[\d\s().-]{7,20}\d",
        text,
    )

    if international:
        raw = international.group(0)
        digits = re.sub(r"\D", "", raw)

        if 8 <= len(digits) <= 15:
            return "+" + digits

    # Nigerian local number.
    # Example: 08012345678

    local_match = re.search(
        r"(?<!\d)(0[789]\d{9})(?!\d)",
        text,
    )

    if local_match:
        number = local_match.group(1)
        return "+234" + number[1:]

    # Nigerian international number without +.
    # Example: 2348012345678

    digits_only = re.sub(r"\D", "", text)

    international_ng = re.search(
        r"(?<!\d)(234[789]\d{9})(?!\d)",
        digits_only,
    )

    if international_ng:
        return "+" + international_ng.group(1)

    return None


# ============================================================
# LOCATION
# ============================================================

def extract_location(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    low = text.lower()
    matches = []

    for location in ALL_LOCATIONS:
        pattern = rf"\b{re.escape(location.lower())}\b"

        if re.search(pattern, low):
            matches.append(location)

    if not matches:
        return None

    # Longest match wins.
    return max(matches, key=len)


# ============================================================
# PURPOSE
# ============================================================

def extract_purpose(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    low = text.lower()

    investment_words = [
        "invest",
        "investing",
        "investment",
    ]

    renting_words = [
        "rent",
        "renting",
        "rental",
        "lease",
        "leasing",
    ]

    buying_words = [
        "buy",
        "buying",
        "purchase",
        "purchasing",
    ]

    for word in investment_words:
        if re.search(rf"\b{re.escape(word)}\b", low):
            return "Investment"

    for word in renting_words:
        if re.search(rf"\b{re.escape(word)}\b", low):
            return "Renting"

    for word in buying_words:
        if re.search(rf"\b{re.escape(word)}\b", low):
            return "Buying"

    return None


# ============================================================
# PROPERTY TYPE
# ============================================================

def extract_property_type(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    low = text.lower()
    matches = []

    for keyword, property_type in PROPERTY_TYPES.items():
        if re.search(
            rf"\b{re.escape(keyword)}\b",
            low,
        ):
            matches.append(
                (len(keyword), property_type)
            )

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: item[0],
    )[1]


# ============================================================
# BEDROOMS
# ============================================================

def extract_bedrooms(text: str) -> Optional[int]:
    text = clean(text)

    if not text:
        return None

    low = text.lower()

    numeric = re.search(
        r"\b(\d{1,2})\s*(?:bedrooms?|beds?)\b",
        low,
    )

    if numeric:
        value = int(numeric.group(1))

        if 1 <= value <= 20:
            return value

    for word, number in NUMBER_WORDS.items():
        if re.search(
            rf"\b{re.escape(word)}\s+(?:bedrooms?|beds?)\b",
            low,
        ):
            if 1 <= number <= 20:
                return number

    return None


# ============================================================
# TIMELINE
# ============================================================

def extract_timeline(text: str) -> Optional[str]:
    text = clean(text)

    if not text:
        return None

    low = text.lower().strip()

    immediate_words = {
        "now",
        "immediately",
        "as soon as possible",
        "asap",
        "right away",
        "urgent",
        "urgently",
    }

    if low in immediate_words:
        return text

    patterns = [
        r"\bwithin\s+\d+(?:\.\d+)?\s+"
        r"(?:day|days|week|weeks|month|months|year|years)\b",

        r"\bin\s+\d+(?:\.\d+)?\s+"
        r"(?:day|days|week|weeks|month|months|year|years)\b",

        r"\b\d+(?:\.\d+)?\s+"
        r"(?:day|days|week|weeks|month|months|year|years)\b",

        r"\bnext\s+(?:day|week|month|year)\b",

        r"\bthis\s+(?:week|month|year)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            low,
            re.IGNORECASE,
        )

        if match:
            return match.group(0).strip()

    for word in NUMBER_WORDS:
        pattern = (
            rf"\b(?:within|in)?\s*"
            rf"{re.escape(word)}\s+"
            rf"(?:day|days|week|weeks|month|months|year|years)\b"
        )

        match = re.search(
            pattern,
            low,
            re.IGNORECASE,
        )

        if match:
            return match.group(0).strip()

    return None


# ============================================================
# NAME
# ============================================================

def extract_name(text: str) -> Optional[str]:
    """
    Extract a person's name.

    Locations and property terms are explicitly blocked.
    """

    text = clean(text)

    if not text:
        return None

    low = text.lower().strip()

    blocked_words = {
        "hi",
        "hello",
        "hey",
        "hello there",
        "hi there",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "good day",
        "thanks",
        "thank you",
        "okay",
        "ok",
        "yes",
        "no",
        "sure",
        "buy",
        "buying",
        "purchase",
        "purchasing",
        "rent",
        "renting",
        "lease",
        "leasing",
        "invest",
        "investing",
        "investment",
        "house",
        "home",
        "apartment",
        "flat",
        "duplex",
        "bungalow",
        "terrace",
        "terraced",
        "land",
        "plot",
        "commercial",
        "office",
        "shop",
        "warehouse",
        "hotel",
        "estate",
    }

    if low in blocked_words:
        return None

    location_words = {
        location.lower()
        for location in ALL_LOCATIONS
    }

    if low in location_words:
        return None

    # --------------------------------------------------------
    # Explicit name declarations.
    # --------------------------------------------------------

    explicit_patterns = [
        r"\bmy\s+name\s+is\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bmy\s+name's\s+([A-Za-z][A-Za-z .'-]{1,80})",
        r"\bcall\s+me\s+([A-Za-z][A-Za-z .'-]{1,80})",
    ]

    for pattern in explicit_patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        name = clean(match.group(1))

        # Stop at additional lead information.
        name = re.split(
            r"\b(?:and|but|i want|i need|looking|from|in|at|"
            r"with|my|budget|phone|email|house|apartment|land|"
            r"location|timeline|bedroom|bedrooms|within|for)\b",
            name,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        name = name.strip(" .,!?;:")

        if not name:
            continue

        if name.lower() in location_words:
            continue

        if name.lower() in blocked_words:
            continue

        if not re.search(r"[A-Za-z]", name):
            continue

        return name.title()

    # --------------------------------------------------------
    # Standalone name.
    #
    # Only allowed after property information is complete.
    # --------------------------------------------------------

    if re.fullmatch(
        r"[A-Za-z]+(?:[ '-][A-Za-z]+){0,5}",
        text,
    ):
        candidate = text.strip(" .,!?;:")
        candidate_low = candidate.lower()

        if candidate_low in blocked_words:
            return None

        if candidate_low in location_words:
            return None

        if candidate_low in {
            key.lower()
            for key in PROPERTY_TYPES
        }:
            return None

        if re.search(
            r"\b(?:today|tomorrow|week|weeks|month|months|"
            r"year|years|day|days)\b",
            candidate_low,
        ):
            return None

        return candidate.title()

    return None


# ============================================================
# BUDGET HELPERS
# ============================================================

def _money_to_number(
    value: float,
    multiplier: int = 1,
) -> int:
    return int(round(value * multiplier))


def _format_naira(value: int) -> str:
    return f"₦{value:,.0f}"


# ============================================================
# BUDGET
# ============================================================

def extract_budget(
    text: str,
) -> Optional[Tuple[int, str]]:
    """
    Extract property budget safely.

    Examples supported:

        70 million
        70m
        ₦70 million
        ₦70m
        N70m
        NGN 70 million
        1.5 billion
        1.5bn
        500k
        500 thousand
        50,000,000
        50000000

    Timeline and bedroom numbers are ignored.
    """

    text = clean(text)

    if not text:
        return None

    low = text.lower()

    # ========================================================
    # STEP 1 — REMOVE TIMELINE EXPRESSIONS
    # ========================================================

    budget_text = re.sub(
        r"\b(?:within\s+|in\s+)?"
        r"\d+(?:\.\d+)?\s+"
        r"(?:day|days|week|weeks|month|months|year|years)\b",
        " ",
        low,
        flags=re.IGNORECASE,
    )

    # ========================================================
    # STEP 2 — REMOVE BEDROOM EXPRESSIONS
    # ========================================================

    budget_text = re.sub(
        r"\b\d{1,2}\s*(?:bedrooms?|beds?)\b",
        " ",
        budget_text,
        flags=re.IGNORECASE,
    )

    # ========================================================
    # STEP 3 — EXPLICIT SCALED MONEY
    # ========================================================
    #
    # This MUST be checked before plain numbers.
    #
    # 70 million -> 70,000,000
    # 70m       -> 70,000,000
    # 1.5bn     -> 1,500,000,000
    # 500k      -> 500,000
    #
    # ========================================================

    scaled_money_pattern = re.compile(
        r"""
        (?:
            (?:₦|NGN|N)\s*
        )?
        (\d+(?:[.,]\d+)?)
        \s*
        (billion|bn|million|m|thousand|k)
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    scaled_matches = list(
        scaled_money_pattern.finditer(budget_text)
    )

    if scaled_matches:
        match = scaled_matches[0]

        number_text = match.group(1)
        suffix = match.group(2).lower()

        number_text = number_text.replace(",", "")

        try:
            number = float(number_text)
        except ValueError:
            return None

        if suffix in {"billion", "bn"}:
            multiplier = 1_000_000_000

        elif suffix in {"million", "m"}:
            multiplier = 1_000_000

        elif suffix in {"thousand", "k"}:
            multiplier = 1_000

        else:
            multiplier = 1

        value = _money_to_number(
            number,
            multiplier,
        )

        if value <= 0:
            return None

        return (
            value,
            _format_naira(value),
        )

    # ========================================================
    # STEP 4 — CURRENCY + PLAIN NUMBER
    # ========================================================
    #
    # Examples:
    # ₦50,000,000
    # N50000000
    # NGN 50000000
    #
    # ========================================================

    currency_pattern = re.compile(
        r"(?:₦|NGN|N)\s*(\d[\d,]*(?:\.\d+)?)",
        re.IGNORECASE,
    )

    currency_match = currency_pattern.search(budget_text)

    if currency_match:
        number_text = currency_match.group(1)
        number_text = number_text.replace(",", "")

        try:
            value = int(float(number_text))
        except ValueError:
            return None

        if value <= 0:
            return None

        return (
            value,
            _format_naira(value),
        )

    # ========================================================
    # STEP 5 — COMMA-FORMATTED LARGE NUMBER
    # ========================================================

    comma_matches = re.findall(
        r"(?<![\d.])\d{1,3}(?:,\d{3})+(?![\d.])",
        budget_text,
    )

    for raw_number in comma_matches:
        digits = raw_number.replace(",", "")

        try:
            value = int(digits)
        except ValueError:
            continue

        if value <= 20:
            continue

        if len(digits) >= 10:
            continue

        return (
            value,
            _format_naira(value),
        )

    # ========================================================
    # STEP 6 — LARGE PLAIN NUMBER
    # ========================================================
    #
    # 50000000 -> ₦50,000,000
    #
    # Numbers such as 999 are deliberately NOT accepted here.
    # ========================================================

    plain_matches = re.findall(
        r"(?<![\d.])\d{5,12}(?![\d.])",
        budget_text,
    )

    for raw_number in plain_matches:
        digits = raw_number

        try:
            value = int(digits)
        except ValueError:
            continue

        # Do not interpret phone numbers as budgets.
        if len(digits) >= 10:
            if not re.search(
                r"(?:budget|naira|₦|NGN|\bN\b)",
                budget_text,
                re.IGNORECASE,
            ):
                continue

        if value <= 20:
            continue

        return (
            value,
            _format_naira(value),
        )

    return None


# ============================================================
# CREATE SESSION
# ============================================================

def create_session() -> Dict[str, Any]:
    return {
        "purpose": None,
        "location": None,
        "property_type": None,
        "budget": None,
        "budget_label": None,
        "bedrooms": None,
        "timeline": None,
        "name": None,
        "phone": None,
        "email": None,
        "message": "",
        "lead_quality": "COLD",
        "lead_complete": False,
        "n8n_sent": False,
        "supabase_saved": False,
        "property_images": [],
    }


# ============================================================
# UPDATE LEAD
# ============================================================

def update_lead(
    session: Dict[str, Any],
    message: str,
) -> Dict[str, Any]:

    message = clean(message)

    if not message:
        return session

    # ========================================================
    # STEP 1 — PROPERTY INFORMATION
    # ========================================================

    purpose = extract_purpose(message)

    if purpose:
        session["purpose"] = purpose

    location = extract_location(message)

    if location:
        session["location"] = location

    property_type = extract_property_type(message)

    if property_type:
        session["property_type"] = property_type

    bedrooms = extract_bedrooms(message)

    if bedrooms is not None:
        session["bedrooms"] = bedrooms

    budget_result = extract_budget(message)

    if budget_result:
        budget_value, budget_label = budget_result

        session["budget"] = budget_value
        session["budget_label"] = budget_label

    timeline = extract_timeline(message)

    if timeline:
        session["timeline"] = timeline

    # ========================================================
    # STEP 2 — PHONE AND EMAIL
    # ========================================================

    phone = extract_phone(message)

    if phone:
        session["phone"] = phone

    email = extract_email(message)

    if email:
        session["email"] = email

    # ========================================================
    # STEP 3 — NAME CONTROL
    # ========================================================

    property_fields_complete = all(
        session.get(field) not in (None, "")
        for field in [
            "purpose",
            "location",
            "property_type",
            "budget",
            "timeline",
        ]
    )

    # IMPORTANT:
    #
    # Do NOT use:
    #   "I am"
    #   "I'm"
    #   "This is"
    #
    # because those are commonly used in property requests.
    #
    # Only these phrases explicitly indicate a name:
    #
    #   My name is Anietie
    #   My name's Anietie
    #   Call me Anietie
    # ========================================================

    explicit_name = bool(
        re.search(
            r"\b(?:my\s+name\s+is|my\s+name's|call\s+me)\b",
            message,
            re.IGNORECASE,
        )
    )

    if explicit_name:
        name = extract_name(message)

        if name:
            session["name"] = name

    elif property_fields_complete:
        name = extract_name(message)

        if name:
            session["name"] = name

    # ========================================================
    # STEP 4 — SAVE MESSAGE
    # ========================================================

    session["message"] = message

    return session


# ============================================================
# NEXT MISSING FIELD
# ============================================================

def next_missing_field(
    session: Dict[str, Any],
) -> Optional[str]:

    for field, _question in QUESTIONS:

        value = session.get(field)

        if value is None:
            return field

        if isinstance(value, str) and not value.strip():
            return field

    return None


# ============================================================
# LEAD QUALITY
# ============================================================

def calculate_lead_quality(
    session: Dict[str, Any],
) -> str:

    required_property_fields = [
        "purpose",
        "location",
        "property_type",
        "budget",
        "timeline",
    ]

    completed = 0

    for field in required_property_fields:

        value = session.get(field)

        if value is None:
            continue

        if isinstance(value, str):

            if value.strip():
                completed += 1

        else:
            completed += 1

    if completed == len(required_property_fields):
        return "HOT"

    if completed >= 2:
        return "WARM"

    return "COLD"
