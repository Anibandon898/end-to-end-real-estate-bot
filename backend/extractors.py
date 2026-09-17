import re
import uuid
from typing import Optional, Dict, Any, Tuple


# =========================================================
# BASIC HELPERS
# =========================================================

def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _low(value: Any) -> str:
    return clean(value).lower()


def _boundary(text: str, phrase: str) -> bool:
    return bool(
        re.search(
            rf"(?<!\w){re.escape(phrase)}(?!\w)",
            text,
            re.IGNORECASE
        )
    )


# =========================================================
# NIGERIAN STATES + MAJOR CITIES / AREAS
# =========================================================

STATE_AREAS = {
    "Abia": [
        "Umuahia", "Aba", "Ohafia", "Arochukwu"
    ],
    "Adamawa": [
        "Yola", "Mubi", "Jimeta", "Numan"
    ],
    "Akwa Ibom": [
        "Uyo", "Eket", "Ikot Ekpene", "Oron",
        "Abak", "Ikot Abasi", "Etinan"
    ],
    "Anambra": [
        "Awka", "Onitsha", "Nnewi", "Ekwulobia"
    ],
    "Bauchi": [
        "Bauchi", "Azare", "Misau"
    ],
    "Bayelsa": [
        "Yenagoa", "Brass", "Ogbia"
    ],
    "Benue": [
        "Makurdi", "Gboko", "Otukpo", "Katsina-Ala"
    ],
    "Borno": [
        "Maiduguri", "Bama", "Biu"
    ],
    "Cross River": [
        "Calabar", "Ikom", "Ogoja"
    ],
    "Delta": [
        "Asaba", "Warri", "Sapele", "Ughelli",
        "Abraka", "Agbor"
    ],
    "Ebonyi": [
        "Abakaliki", "Afikpo", "Onueke"
    ],
    "Edo": [
        "Benin City", "Auchi", "Ekpoma", "Uromi"
    ],
    "Ekiti": [
        "Ado-Ekiti", "Ikere", "Ilawe"
    ],
    "Enugu": [
        "Enugu", "Nsukka", "Oji River", "Awgu"
    ],
    "Gombe": [
        "Gombe", "Kumo", "Billiri"
    ],
    "Imo": [
        "Owerri", "Orlu", "Okigwe"
    ],
    "Jigawa": [
        "Dutse", "Hadejia", "Gumel"
    ],
    "Kaduna": [
        "Kaduna", "Zaria", "Kafanchan", "Saminaka"
    ],
    "Kano": [
        "Kano", "Wudil", "Bichi", "Gwarzo"
    ],
    "Katsina": [
        "Katsina", "Funtua", "Daura"
    ],
    "Kebbi": [
        "Birnin Kebbi", "Argungu", "Yauri"
    ],
    "Kogi": [
        "Lokoja", "Okene", "Idah", "Kabba"
    ],
    "Kwara": [
        "Ilorin", "Offa", "Jebba"
    ],
    "Lagos": [
        "Lagos", "Ikeja", "Lekki", "Victoria Island",
        "Ikoyi", "Ajah", "Yaba", "Surulere",
        "Maryland", "Magodo", "Gbagada", "Ojodu",
        "Festac", "Chevron", "Banana Island",
        "Badagry", "Epe"
    ],
    "Nasarawa": [
        "Lafia", "Keffi", "Karu", "Mararaba"
    ],
    "Niger": [
        "Minna", "Suleja", "Bida", "Kontagora"
    ],
    "Ogun": [
        "Abeokuta", "Ijebu Ode", "Sagamu",
        "Ota", "Ifo", "Agbara"
    ],
    "Ondo": [
        "Akure", "Ondo", "Owo", "Ikare"
    ],
    "Osun": [
        "Osogbo", "Ile-Ife", "Ilesa", "Ede"
    ],
    "Oyo": [
        "Ibadan", "Ogbomosho", "Oyo", "Iseyin"
    ],
    "Plateau": [
        "Jos", "Bukuru", "Barkin Ladi", "Pankshin"
    ],
    "Rivers": [
        "Port Harcourt", "Bonny", "Eleme",
        "Obio-Akpor", "Oyigbo", "Omoku"
    ],
    "Sokoto": [
        "Sokoto", "Tambuwal", "Wurno"
    ],
    "Taraba": [
        "Jalingo", "Wukari", "Bali"
    ],
    "Yobe": [
        "Damaturu", "Potiskum", "Gashua"
    ],
    "Zamfara": [
        "Gusau", "Kaura Namoda", "Talata Mafara"
    ],
    "FCT": [
        "Abuja", "Garki", "Wuse", "Maitama",
        "Asokoro", "Gwarinpa", "Jabi", "Life Camp",
        "Kubwa", "Lokogoma", "Katampe", "Guzape",
        "Utako", "Apo", "Nyanya", "Karu"
    ],
}


# =========================================================
# LOCATION LOOKUPS
# =========================================================

AREA_DISPLAY = {}
AREA_TO_STATE = {}

for state, areas in STATE_AREAS.items():

    AREA_DISPLAY[state.lower()] = state
    AREA_TO_STATE[state.lower()] = state

    for area in areas:
        AREA_DISPLAY[area.lower()] = area
        AREA_TO_STATE[area.lower()] = state


# =========================================================
# EMAIL
# =========================================================

def extract_email(text: str) -> Optional[str]:
    text = clean(text)

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )

    if match:
        return match.group(0).lower()

    return None


# =========================================================
# PHONE
# =========================================================

def extract_phone(text: str) -> Optional[str]:
    text = clean(text)

    patterns = [
        r"(?<!\d)(\+\d{1,3}[\s.-]?\d{3,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})(?!\d)",
        r"(?<!\d)(0\d{10})(?!\d)",
        r"(?<!\d)(\d{10,15})(?!\d)",
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if not match:
            continue

        phone = re.sub(
            r"[^\d+]",
            "",
            match.group(1)
        )

        if phone.startswith("+"):
            return phone

        if phone.startswith("0") and len(phone) == 11:
            return "+234" + phone[1:]

        if len(phone) >= 10:
            return "+" + phone

    return None


# =========================================================
# LOCATION
# =========================================================

def extract_location(
    text: str
) -> Tuple[Optional[str], Optional[str]]:

    text = clean(text)
    low = text.lower()

    matches = []

    for area_lower, display in AREA_DISPLAY.items():

        if _boundary(low, area_lower):

            matches.append(
                (
                    len(area_lower),
                    display,
                    AREA_TO_STATE[area_lower]
                )
            )

    if matches:

        # Longest match wins.
        matches.sort(reverse=True)

        _, location, state = matches[0]

        return location, state

    return None, None


def state_for(location: str) -> Optional[str]:

    if not location:
        return None

    low = clean(location).lower()

    if low in AREA_TO_STATE:
        return AREA_TO_STATE[low]

    for state in STATE_AREAS:

        if _boundary(low, state.lower()):
            return state

    return None


# =========================================================
# NAME
# =========================================================

BAD_NAME_WORDS = {
    "yes",
    "no",
    "okay",
    "ok",
    "sure",
    "buy",
    "buying",
    "rent",
    "renting",
    "rental",
    "investment",
    "invest",
    "house",
    "home",
    "land",
    "apartment",
    "flat",
    "duplex",
    "bungalow",
    "property",
    "commercial",
    "bedroom",
    "bedrooms",
    "budget",
    "hello",
    "hi",
    "hey",
    "thanks",
    "thank",
}


def _looks_like_name(value: str) -> bool:

    value = clean(value)

    if not value:
        return False

    words = value.split()

    if len(words) > 5:
        return False

    if any(
        word.lower() in BAD_NAME_WORDS
        for word in words
    ):
        return False

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z' -]{1,60}",
        value
    ):
        return False

    return True


def extract_name(text: str) -> Optional[str]:

    text = clean(text)

    patterns = [
        r"\bmy name is\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\bmy name's\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\bname\s*:\s*([A-Za-z][A-Za-z' -]{1,60})",
        r"\bi am\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\bi'm\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\bthis is\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\byou can call me\s+([A-Za-z][A-Za-z' -]{1,60})",
        r"\bi go by\s+([A-Za-z][A-Za-z' -]{1,60})",
    ]

    stop_words = {
        "and",
        "but",
        "my",
        "i",
        "im",
        "i'm",
        "is",
        "am",
        "looking",
        "for",
        "need",
        "want",
        "buy",
        "rent",
        "house",
        "apartment",
        "land",
        "property",
        "in",
        "with",
        "budget",
        "phone",
        "email",
    }

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        candidate = clean(match.group(1))

        words = candidate.split()
        trimmed = []

        for word in words:

            if word.lower() in stop_words:
                break

            trimmed.append(word)

        candidate = " ".join(trimmed)

        if _looks_like_name(candidate):
            return candidate.title()

    # Standalone:
    # David
    # David Okoro
    if _looks_like_name(text):

        words = text.split()

        if 1 <= len(words) <= 4:
            return text.title()

    return None


# =========================================================
# PROPERTY TYPE
# =========================================================

PROPERTY_TYPES = [
    "Self Contain",
    "Mini Flat",
    "Studio",
    "Semi Detached",
    "Detached",
    "Penthouse",
    "Maisonette",
    "Terrace",
    "Apartment",
    "Flat",
    "Duplex",
    "Bungalow",
    "House",
    "Land",
    "Commercial",
]


def extract_property_type(text: str) -> Optional[str]:

    low = _low(text)

    sorted_types = sorted(
        PROPERTY_TYPES,
        key=len,
        reverse=True
    )

    for property_type in sorted_types:

        if _boundary(
            low,
            property_type.lower()
        ):
            return property_type

    return None


# =========================================================
# PURPOSE
# =========================================================

def extract_purpose(text: str) -> Optional[str]:

    low = _low(text)

    if re.search(
        r"\b(investment|invest|investing)\b",
        low
    ):
        return "Investment"

    if re.search(
        r"\b(rent|rental|renting|lease|leasing)\b",
        low
    ):
        return "Renting"

    if re.search(
        r"\b(buy|buying|purchase|purchasing|own|owning)\b",
        low
    ):
        return "Buying"

    return None


# =========================================================
# BEDROOMS
# =========================================================

NUMBER_WORDS = {
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
}


def extract_bedrooms(text: str) -> Optional[int]:

    low = _low(text)

    patterns = [
        r"\b(\d+)\s*(?:bed|beds|bedroom|bedrooms)\b",
        r"\b(\d+)\s*br\b",
        r"\b(?:need|want|looking for|with)\s+(\d+)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            low
        )

        if not match:
            continue

        try:

            value = int(match.group(1))

            # IMPORTANT:
            # No artificial upper limit.
            # 1, 4, 12, 50, 250, etc. are accepted.
            if value > 0:
                return value

        except ValueError:
            pass

    for word, number in NUMBER_WORDS.items():

        if re.search(
            rf"\b{word}\s*(?:bed|beds|bedroom|bedrooms)\b",
            low
        ):
            return number

    return None


# =========================================================
# TIMELINE
# =========================================================

def extract_timeline(text: str) -> Optional[str]:
    """Extract a property timeline from natural language."""
    if not text:
        return None

    low = _low(text).strip()

    # Immediate / urgent
    if re.search(r'\b(immediately|right\s+away|asap|as\s+soon\s+as\s+possible|right\s+now|now)\b', low):
        return 'Immediately'

    # Flexible
    if re.search(r'\b(flexible|not\s+sure|no\s+rush|open\s+timeline|whenever)\b', low):
        return 'Flexible'

    # Within the month
    if re.search(r'\bwithin\s+the\s+month\b', low):
        return 'Within 1 month'

    # This month
    if re.search(r'\bthis\s+month\b', low):
        return 'Within 1 month'

    # Next month
    if re.search(r'\bnext\s+month\b', low):
        return 'Within 2 months'

    # A month / one month
    if re.search(r'\b(a|one|1)\s+month\b', low):
        return 'Within 1 month'

    # A few months
    if re.search(r'\ba\s+few\s+months\b', low):
        return 'Within 3 months'

    # Within X days/weeks/months/years
    match = re.search(r'\bwithin\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b', low)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        if number == 1:
            unit = unit.rstrip('s')
        elif unit in ('day', 'week', 'month', 'year'):
            unit += 's'
        return f'Within {number} {unit}'

    # In X days/weeks/months/years
    match = re.search(r'\bin\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)\b', low)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        if number == 1:
            unit = unit.rstrip('s')
        elif unit in ('day', 'week', 'month', 'year'):
            unit += 's'
        return f'Within {number} {unit}'

    # Plain X days/weeks/months/years
    # Handles: 3 month, 3 months, 2 weeks, 5 days, etc.
    match = re.search(r'\b(\d+)\s+(day|days|week|weeks|month|months|year|years)\b', low)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        if number == 1:
            unit = unit.rstrip('s')
        elif unit in ('day', 'week', 'month', 'year'):
            unit += 's'
        return f'Within {number} {unit}'

    # Word numbers
    word_numbers = {
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10,
        'eleven': 11,
        'twelve': 12,
    }

    for word, number in word_numbers.items():
        match = re.search(rf'\b{word}\s+(day|days|week|weeks|month|months|year|years)\b', low)
        if match:
            unit = match.group(1)
            if number == 1:
                unit = unit.rstrip('s')
            elif unit in ('day', 'week', 'month', 'year'):
                unit += 's'
            return f'Within {number} {unit}'

    return None

def _convert_money(
    value: float,
    unit: Optional[str]
) -> float:

    if not unit:
        return value

    unit = unit.lower()

    if unit in ("b", "billion"):
        return value * 1_000_000_000

    if unit in ("m", "million"):
        return value * 1_000_000

    if unit in ("k", "thousand"):
        return value * 1_000

    return value


def extract_budget(
    text: str
) -> Tuple[Optional[float], Optional[str]]:
    """Extract a property budget without confusing time expressions for money."""

    text = clean(text)
    low = text.lower().strip()

    # -----------------------------------------------------
    # Ignore timeline expressions.
    # Examples:
    # 3 month
    # 3 months
    # within 3 months
    # in 3 months
    # 2 weeks
    # 5 days
    # -----------------------------------------------------
    if re.search(
        r'\b(?:within\s+|in\s+)?(?:\d+|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+'
        r'(?:day|days|week|weeks|month|months|year|years)\b',
        low
    ):
        # If the entire message is a timeline expression, it is definitely
        # not a budget.
        if re.fullmatch(
            r'\s*(?:within\s+|in\s+)?(?:\d+|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+'
            r'(?:day|days|week|weeks|month|months|year|years)\s*',
            low
        ):
            return None, None

    # Flexible budget
    if re.search(
        r'\b(flexible|open budget|negotiable)\b',
        low
    ):
        return None, 'Flexible'

    # -----------------------------------------------------
    # Budget ranges
    # Example:
    # 40m - 50m
    # 40 million to 50 million
    # ₦40m - ₦50m
    # -----------------------------------------------------
    range_match = re.search(
        r'(?:₦|ngn|n)?\s*'
        r'(\d+(?:\.\d+)?)\s*'
        r'(million|m|billion|b|thousand|k)?'
        r'\s*(?:-|to)\s*'
        r'(?:₦|ngn|n)?\s*'
        r'(\d+(?:\.\d+)?)\s*'
        r'(million|m|billion|b|thousand|k)?',
        low,
        re.IGNORECASE
    )

    if range_match:
        first = _convert_money(
            float(range_match.group(1)),
            range_match.group(2)
        )

        second = _convert_money(
            float(range_match.group(3)),
            range_match.group(4)
        )

        low_value = min(first, second)
        high_value = max(first, second)

        numeric_budget = (low_value + high_value) / 2

        text_value = (
            f'₦{low_value:,.0f} - '
            f'₦{high_value:,.0f}'
        )

        return numeric_budget, text_value

    # -----------------------------------------------------
    # Single budget
    # -----------------------------------------------------
    match = re.search(
        r'(?:₦|ngn|n)\s*'
        r'(\d+(?:\.\d+)?)\s*'
        r'(million|m|billion|b|thousand|k)?',
        low,
        re.IGNORECASE
    )

    if not match:
        match = re.search(
            r'\b(\d+(?:\.\d+)?)\s*'
            r'(million|m|billion|b|thousand|k)\b',
            low,
            re.IGNORECASE
        )

    if match:
        value = _convert_money(
            float(match.group(1)),
            match.group(2)
        )

        if value >= 100_000:
            return value, f'₦{value:,.0f}'

    # -----------------------------------------------------
    # Plain large numeric amounts.
    # Example:
    # 50000000
    # 50000000 naira
    # -----------------------------------------------------
    match = re.search(
        r'\b(\d{6,})\b\s*(?:naira|ngn|₦)?',
        low,
        re.IGNORECASE
    )

    if match:
        value = float(match.group(1))
        return value, f'₦{value:,.0f}'

    return None, None

def budget_text(value) -> str:

    if value is None:
        return ""

    # Already a readable string
    if isinstance(value, str):

        value = value.strip()

        if not value:
            return ""

        return value

    try:

        amount = float(value)

        return f"₦{amount:,.0f}"

    except (TypeError, ValueError):

        return str(value)


# =========================================================
# SESSION
# =========================================================

def create_session(
    session_id: Optional[str] = None
) -> Dict[str, Any]:

    if not session_id:
        session_id = str(uuid.uuid4())

    return {
        "session_id": session_id,

        "name": "",
        "email": "",
        "phone": "",

        "location": "",
        "state": "",

        "property_type": "",
        "purpose": "",

        "budget": None,
        "budget_text": "",

        "bedrooms": None,

        "timeline": "",

        "message": "",

        "lead_quality": "",
        "main_problem": "",
        "recommended_action": "",

        "last_asked": None,

        "n8n_sent": False,
        "supabase_saved": False,
    }


# =========================================================
# UPDATE SESSION
# =========================================================

def update_lead(
    session: Dict[str, Any],
    message: str
) -> Dict[str, Any]:

    message = clean(message)

    # Email
    email = extract_email(message)

    if email:
        session["email"] = email

    # Phone
    phone = extract_phone(message)

    if phone:
        session["phone"] = phone

    # Name
    name = extract_name(message)

    if name:
        session["name"] = name

    # Location
    location, state = extract_location(message)

    if location:
        session["location"] = location

    if state:
        session["state"] = state

    # Property type
    property_type = extract_property_type(message)

    if property_type:
        session["property_type"] = property_type

    # Purpose
    purpose = extract_purpose(message)

    if purpose:
        session["purpose"] = purpose

    # Bedrooms
    bedrooms = extract_bedrooms(message)

    if bedrooms is not None:
        session["bedrooms"] = bedrooms

    # Timeline
    timeline = extract_timeline(message)

    if timeline:
        session["timeline"] = timeline

    # Budget
    budget, readable_budget = extract_budget(message)

    if budget is not None:
        session["budget"] = budget

    if readable_budget:
        session["budget_text"] = readable_budget

    # Keep latest user message
    session["message"] = message

    return session


# =========================================================
# QUESTIONS
# =========================================================

QUESTIONS = {
    "purpose": "Are you looking to buy, rent, or invest?",
    "location": "Which location are you interested in?",
    "property_type": "What type of property are you looking for?",
    "budget": "What is your budget?",
    "timeline": "When are you looking to move or complete the purchase?",
    "name": "May I have your name?",
    "phone": "What is the best phone number to reach you?",
    "email": "What is your email address?",
}


# =========================================================
# NEXT MISSING FIELD
# =========================================================

def next_missing_field(
    session: Dict[str, Any]
) -> Optional[str]:

    required_order = [
        "purpose",
        "location",
        "property_type",
        "budget",
        "timeline",
        "name",
        "phone",
        "email",
    ]

    for field in required_order:

        value = session.get(field)

        if value is None:
            return field

        if isinstance(value, str) and not value.strip():
            return field

    return None


# =========================================================
# LEAD QUALITY
# =========================================================

def calculate_lead_quality(
    session: Dict[str, Any]
) -> str:

    important_fields = [
        "location",
        "property_type",
        "purpose",
        "budget",
        "timeline",
    ]

    completed = 0

    for field in important_fields:

        value = session.get(field)

        if value is not None and value != "":
            completed += 1

    if completed == 5:
        return "HOT"

    if completed >= 3:
        return "WARM"

    return "COLD"


# =========================================================
# UPDATE LEAD QUALITY
# =========================================================

def update_lead_quality(
    session: Dict[str, Any]
) -> Dict[str, Any]:

    quality = calculate_lead_quality(session)

    session["lead_quality"] = quality

    if quality == "HOT":

        session["main_problem"] = (
            "Looking for a specific property "
            "with clear requirements and timeline"
        )

        session["recommended_action"] = (
            "Contact lead immediately"
        )

    elif quality == "WARM":

        session["main_problem"] = (
            "Potential property buyer/renter "
            "still researching options"
        )

        session["recommended_action"] = (
            "Follow up and provide suitable properties"
        )

    else:

        session["main_problem"] = (
            "Property requirements are not yet clear"
        )

        session["recommended_action"] = (
            "Continue qualification"
        )

    return session


# =========================================================
# BUILD LEAD PAYLOAD
# =========================================================

def build_lead_payload(
    session: Dict[str, Any]
) -> Dict[str, Any]:

    update_lead_quality(session)

    return {
        "name": session.get("name") or None,

        "email": session.get("email") or None,

        "phone": session.get("phone") or None,

        "location": session.get("location") or None,

        "property_type": (
            session.get("property_type") or None
        ),

        "purpose": session.get("purpose") or None,

        "budget": session.get("budget"),

        "bedrooms": session.get("bedrooms"),

        "timeline": session.get("timeline") or None,

        "message": session.get("message") or None,

        "lead_quality": (
            session.get("lead_quality") or "COLD"
        ),

        "main_problem": (
            session.get("main_problem") or None
        ),

        "recommended_action": (
            session.get("recommended_action") or None
        ),

        "source": "real-estate-chatbot",
    }