"""Business types to hunt, grouped the way the outreach plan targets them.

Each type has:
  google  the words sent to Google Places text search
  osm     OpenStreetMap filters (Overpass QL). A name pattern on its own is restricted to things tagged as a business.
  markets where this type is a good prospect (NG, UK, US) - used to suggest types, never to block a search
"""
import re

BIZ = '[~"^(shop|craft|office|amenity|healthcare|tourism|leisure|club)$"~"."]'


def t(k, v):
    return f'["{k}"="{v}"]'


NOT_FOOD = '["amenity"!~"^(bar|pub|restaurant|cafe|fast_food|nightclub|biergarten|food_court)$"]'


def name(rx, food_ok=False):
    """Match a word in the business name. Bars and restaurants are left out unless the type is food,
    so 'roof' finds roofers, not rooftop bars."""
    return f'["name"~"{rx}",i]' + BIZ + ("" if food_ok else NOT_FOOD)


TRADES, HEALTH, BEAUTY, FOOD, STAY, EDU, PRO, SHOPS, AUTO, DIASPORA = (
    "Trades & home services", "Health", "Beauty & fitness", "Food & drink", "Property, stays & events",
    "Schools & childcare", "Professional services", "Shops", "Auto", "African & Caribbean diaspora")

AFRO = "african|nigerian|naija|ghana|jollof|suya|caribbean|jamaican|ethiopian|eritrean|somali|senegal|cameroon|congo|kenyan|afro|west indian"

_C = [
    # ---- trades & home services
    ("plumbers", "Plumbers", TRADES, "UK US NG", "plumber", [t("craft", "plumber"), name("plumb")]),
    ("electricians", "Electricians", TRADES, "UK US NG", "electrician", [t("craft", "electrician"), name("electrician|electrical (contractor|services|engineer)")]),
    ("roofers", "Roofers", TRADES, "UK US", "roofing contractor", [t("craft", "roofer"), name("roof")]),
    ("builders", "Builders & contractors", TRADES, "UK US NG", "building contractor", [t("craft", "builder"), t("office", "construction_company"), name("builders|construction|contractors")]),
    ("hvac", "HVAC & air conditioning", TRADES, "US UK NG", "HVAC air conditioning repair", [t("craft", "hvac"), name("hvac|air condition|heating (and|&) (air|cooling)|refrigeration")]),
    ("gas", "Gas & boiler engineers", TRADES, "UK", "gas engineer boiler repair", [t("craft", "heating_engineer"), name("boiler|gas (engineer|services)|heating")]),
    ("locksmiths", "Locksmiths", TRADES, "UK US", "locksmith", [t("shop", "locksmith"), t("craft", "locksmith"), name("locksmith")]),
    ("painters", "Painters & decorators", TRADES, "UK US", "painter decorator", [t("craft", "painter"), name("painter|painting|decorators")]),
    ("carpenters", "Carpenters & joiners", TRADES, "UK US NG", "carpenter joiner", [t("craft", "carpenter"), t("craft", "joiner"), name("carpent|joiner")]),
    ("landscapers", "Landscapers & gardeners", TRADES, "UK US", "landscaping", [t("craft", "gardener"), t("craft", "landscaper"), name("landscap|gardening|lawn")]),
    ("tree", "Tree services", TRADES, "US UK", "tree service", [name("tree (service|surgeon|care|specialist)|arborist")]),
    ("pest", "Pest control", TRADES, "UK US NG", "pest control", [t("shop", "pest_control"), name("pest|termite|extermin|fumigat")]),
    ("cleaning", "Cleaning companies", TRADES, "UK US NG", "cleaning company", [t("office", "cleaning"), t("craft", "cleaning"), name("cleaning (services|company|solutions)|cleaners|janitorial|maid")]),
    ("removals", "Removals & movers", TRADES, "UK US", "removals moving company", [t("office", "moving_company"), t("shop", "removals"), name("removal|movers|moving (company|services)")]),
    ("pressure", "Pressure washing", TRADES, "US UK", "pressure washing", [name("pressure wash|power wash|jet wash|soft wash")]),
    ("pools", "Pool services", TRADES, "US", "pool cleaning service", [name("pool (service|clean|care|repair)|pools")]),
    ("junk", "Junk removal & clearance", TRADES, "US UK", "junk removal", [name("junk|rubbish (removal|clearance)|waste clearance|house clearance|skip hire")]),
    ("garagedoors", "Garage door companies", TRADES, "US", "garage door repair", [name("garage door")]),
    ("windows", "Window cleaners", TRADES, "UK US", "window cleaning", [name("window clean")]),
    ("solar", "Solar & inverter installers", TRADES, "NG UK US", "solar panel installer", [name("solar|inverter")]),
    ("interior", "Interior designers", TRADES, "NG UK US", "interior designer", [t("shop", "interior_decoration"), t("office", "interior_design"), name("interior")]),
    ("furniture", "Furniture makers & shops", TRADES, "NG UK", "furniture maker", [t("shop", "furniture"), t("craft", "cabinet_maker"), name("furniture")]),
    ("materials", "Building materials suppliers", TRADES, "NG", "building materials", [t("shop", "hardware"), t("shop", "doityourself"), t("shop", "trade"), name("building material|tiles|roofing sheet|cement")]),
    # ---- health
    ("dentists", "Dentists", HEALTH, "UK US NG", "dentist", [t("amenity", "dentist"), t("healthcare", "dentist")]),
    ("clinics", "Clinics & hospitals", HEALTH, "NG", "private hospital clinic", [t("amenity", "clinic"), t("amenity", "hospital"), t("healthcare", "clinic"), t("healthcare", "hospital")]),
    ("pharmacies", "Pharmacies", HEALTH, "NG UK", "pharmacy", [t("amenity", "pharmacy")]),
    ("labs", "Diagnostic labs", HEALTH, "NG", "diagnostic centre", [t("healthcare", "laboratory"), name("diagnostic|laborator|medical lab|scan cent")]),
    ("physio", "Physiotherapists", HEALTH, "UK US NG", "physiotherapist", [t("healthcare", "physiotherapist"), name("physio")]),
    ("chiro", "Chiropractors", HEALTH, "UK US", "chiropractor", [t("healthcare", "chiropractor"), '["healthcare:speciality"="chiropractic"]', name("chiropract")]),
    ("opticians", "Opticians", HEALTH, "UK NG", "optician", [t("shop", "optician"), t("healthcare", "optometrist")]),
    ("vets", "Vets", HEALTH, "UK US NG", "veterinary clinic", [t("amenity", "veterinary")]),
    ("care", "Home care agencies", HEALTH, "UK US", "home care agency", [name("home ?care|care (agency|services|solutions)|domiciliary|senior care|nursing (agency|services)")]),
    # ---- beauty & fitness
    ("aesthetics", "Aesthetics clinics & med spas", BEAUTY, "UK US NG", "aesthetics clinic med spa", [name("aesthetic|med ?spa|botox|skin clinic|laser clinic|cosmetic clinic")]),
    ("salons", "Hair salons", BEAUTY, "UK US NG", "hair salon", [t("shop", "hairdresser")]),
    ("barbers", "Barbers", BEAUTY, "UK US NG", "barber shop", ['["shop"="hairdresser"]["hairdresser"="barber"]', '["shop"="hairdresser"]["name"~"barb",i]', t("shop", "barber")]),
    ("beauty", "Beauty, nails & lashes", BEAUTY, "UK US NG", "beauty salon nails lashes", [t("shop", "beauty"), name("nails|lash|brows|beauty")]),
    ("spas", "Spas & massage", BEAUTY, "UK US NG", "spa massage", [t("shop", "massage"), t("leisure", "spa"), t("amenity", "spa"), name("(^| )spa( |$)|massage")]),
    ("tattoo", "Tattoo studios", BEAUTY, "UK US", "tattoo studio", [t("shop", "tattoo")]),
    ("gyms", "Gyms & personal trainers", BEAUTY, "UK US NG", "gym personal trainer", [t("leisure", "fitness_centre"), name("(^| )gym|fitness|personal train|crossfit|bootcamp")]),
    ("martial", "Martial arts & dance studios", BEAUTY, "US UK", "martial arts school", ['["sport"~"karate|taekwondo|judo|martial_arts|boxing|kickboxing|mma|jiu"]["leisure"]', name("karate|martial|taekwondo|jiu|judo|kickbox|boxing|mma|dance (studio|school|academy)")]),
    ("groomers", "Dog groomers", BEAUTY, "UK US", "dog grooming", [t("shop", "pet_grooming"), name("grooming|groomer")]),
    # ---- food & drink
    ("restaurants", "Restaurants", FOOD, "NG UK US", "restaurant", [t("amenity", "restaurant")]),
    ("cafes", "Cafés", FOOD, "UK US NG", "cafe", [t("amenity", "cafe")]),
    ("takeaways", "Takeaways & fast food", FOOD, "UK US NG", "takeaway", [t("amenity", "fast_food")]),
    ("bakeries", "Bakeries & cake makers", FOOD, "NG UK US", "bakery cakes", [t("shop", "bakery"), t("shop", "pastry"), name("cake|bakery|bakes|pastr", True)]),
    ("caterers", "Caterers & small chops", FOOD, "NG UK US", "catering", [t("craft", "caterer"), name("cater|small chops", True)]),
    ("bars", "Bars & lounges", FOOD, "NG UK US", "lounge bar", [t("amenity", "bar"), name("lounge", True)]),
    # ---- property, stays & events
    ("shortlets", "Short-let apartments", STAY, "NG UK", "short let apartment", [t("tourism", "apartment"), name("short ?let|shortlet|serviced apartment|apartments")]),
    ("hotels", "Hotels & guest houses", STAY, "NG UK US", "hotel", [t("tourism", "hotel"), t("tourism", "guest_house"), t("tourism", "motel")]),
    ("bnb", "B&Bs", STAY, "UK US", "bed and breakfast", ['["tourism"="guest_house"]["guest_house"="bed_and_breakfast"]', name("b ?& ?b|bed (and|&) breakfast")]),
    ("realestate", "Estate agents & realtors", STAY, "NG UK US", "real estate agent", [t("office", "estate_agent"), t("shop", "estate_agent"), name("realt|real estate|estate agent|properties|property")]),
    ("letting", "Letting agents", STAY, "UK", "letting agent", ['["office"="estate_agent"]["name"~"letting|lets",i]', name("lettings|letting agent")]),
    ("venues", "Event centres & venues", STAY, "NG UK US", "event centre", [t("amenity", "events_venue"), t("amenity", "conference_centre"), name("event cent|events? hall|banquet|wedding venue|event space", True)]),
    ("planners", "Event planners & decorators", STAY, "NG UK", "event planner", [name("event (planner|planning|management|decor)|events|decor|wedding planner")]),
    ("photographers", "Photographers", STAY, "NG UK US", "photographer", [t("craft", "photographer"), t("shop", "photo"), name("photograph|photo studio")]),
    ("florists", "Florists", STAY, "UK US", "florist", [t("shop", "florist")]),
    # ---- schools & childcare
    ("schools", "Private schools", EDU, "NG", "private school", [t("amenity", "school"), name("academy|college|montessori|international school")]),
    ("nurseries", "Nurseries, crèches & daycare", EDU, "NG UK US", "nursery daycare", [t("amenity", "kindergarten"), t("amenity", "childcare"), name("nursery|creche|crèche|daycare|day care|preschool|pre-school")]),
    ("tutors", "Tutoring & lesson centres", EDU, "NG UK US", "tutoring centre", [t("amenity", "prep_school"), t("office", "tutoring"), name("tutor|tuition|lessons|coaching|learning cent|jamb|waec|exam prep")]),
    ("driving", "Driving schools", EDU, "UK US NG", "driving school", [t("amenity", "driving_school"), name("driving school|school of motoring|driving instructor")]),
    # ---- professional services
    ("lawyers", "Law firms & solicitors", PRO, "NG UK US", "law firm", [t("office", "lawyer"), name("solicitor|law firm|attorney|chambers|legal")]),
    ("immigration", "Immigration lawyers & visa agents", PRO, "US UK NG", "immigration lawyer", ['["office"="lawyer"]["name"~"immigration",i]', name("immigration|visa")]),
    ("accountants", "Accountants & bookkeepers", PRO, "NG UK US", "accountant", [t("office", "accountant"), name("accountant|accounting|bookkeep|chartered")]),
    ("tax", "Tax preparers", PRO, "US UK", "tax preparation", [t("office", "tax_advisor"), name("tax (service|prep|return|advis)|taxes")]),
    ("insurance", "Insurance agents", PRO, "US NG", "insurance agent", [t("office", "insurance")]),
    ("mortgage", "Mortgage brokers", PRO, "UK US", "mortgage broker", [name("mortgage")]),
    ("recruitment", "Recruitment agencies", PRO, "NG UK US", "recruitment agency", [t("office", "employment_agency"), name("recruit|staffing")]),
    ("travel", "Travel agents", PRO, "NG UK", "travel agency", [t("shop", "travel_agency"), t("office", "travel_agent"), name("travel|tours")]),
    ("printing", "Printing & branding", PRO, "NG UK", "printing press", [t("shop", "copyshop"), t("craft", "printer"), t("shop", "printing"), name("print|branding|signage")]),
    ("logistics", "Logistics & dispatch", PRO, "NG", "logistics dispatch delivery", [t("office", "logistics"), t("office", "courier"), name("logistic|dispatch|courier|delivery")]),
    ("laundry", "Laundry & dry cleaners", PRO, "NG UK US", "laundry dry cleaner", [t("shop", "laundry"), t("shop", "dry_cleaning")]),
    ("churches", "Churches", PRO, "NG UK US", "church", ['["amenity"="place_of_worship"]["religion"="christian"]']),
    # ---- shops
    ("fashion", "Fashion designers & tailors", SHOPS, "NG", "fashion designer", [t("craft", "tailor"), t("shop", "tailor"), t("shop", "fashion"), name("fashion|couture|tailor|stitches")]),
    ("boutiques", "Boutiques & clothing stores", SHOPS, "NG UK US", "boutique", [t("shop", "boutique"), t("shop", "clothes")]),
    ("phones", "Phone & gadget shops", SHOPS, "NG", "phone shop", [t("shop", "mobile_phone"), t("shop", "electronics")]),
    ("supermarkets", "Independent supermarkets", SHOPS, "NG", "supermarket", [t("shop", "supermarket")]),
    # ---- auto
    ("cardealers", "Car dealers", AUTO, "NG US UK", "car dealer", [t("shop", "car")]),
    ("mechanics", "Mechanics & auto repair", AUTO, "NG UK US", "auto repair mechanic", [t("shop", "car_repair")]),
    ("mot", "MOT garages", AUTO, "UK", "MOT test centre", ['["shop"="car_repair"]["name"~"(^| )MOTs?( |$)"]', '["shop"="car_repair"]["service:vehicle:mot"="yes"]']),
    ("bodyshops", "Body shops & collision repair", AUTO, "US UK", "auto body shop", ['["shop"="car_repair"]["name"~"body|collision|panel|smart repair",i]', name("collision|body ?shop|bodywork")]),
    ("towing", "Towing & recovery", AUTO, "US UK", "towing service", [name("towing|tow truck|breakdown recovery|vehicle recovery")]),
    ("carwash", "Car wash & detailing", AUTO, "NG UK US", "car detailing", [t("amenity", "car_wash"), name("detailing|valeting|car wash")]),
    ("carhire", "Car hire", AUTO, "NG UK US", "car rental", [t("amenity", "car_rental")]),
    # ---- African & Caribbean diaspora businesses abroad: you understand them better than most agencies do
    ("afrofood", "African & Caribbean restaurants", DIASPORA, "UK US", "African restaurant",
     ['["amenity"~"restaurant|fast_food|cafe"]["cuisine"~"african|nigerian|ghanaian|caribbean|jamaican|ethiopian|eritrean|somali|senegalese|cameroonian|congolese|kenyan",i]',
      f'["amenity"~"restaurant|fast_food|cafe"]["name"~"{AFRO}",i]']),
    ("afrostores", "African & Caribbean food stores", DIASPORA, "UK US", "African grocery store", [f'["shop"]["name"~"{AFRO}|tropical|world food|international food",i]']),
    ("braids", "Braiding & afro hair salons", DIASPORA, "UK US NG", "braiding salon", ['["shop"~"hairdresser|beauty"]["name"~"braid|afro|natural hair|locs|weave|wig",i]']),
    ("cargo", "Shipping & cargo to Africa", DIASPORA, "UK US", "shipping cargo to Nigeria",
     ['["name"~"africa|nigeria|ghana|lagos|abuja|naija|accra",i]["name"~"cargo|shipping|freight|courier|logistic|export",i]', '["office"="logistics"]["name"~"cargo",i]', name("cargo")]),
    ("afrochurch", "African churches", DIASPORA, "UK US", "RCCG church",
     ['["amenity"="place_of_worship"]["name"~"rccg|redeemed|winners|deeper life|mountain of fire|mfm|celestial|cherubim|christ apostolic|christ embassy|house on the rock|foursquare|living faith|dunamis|daystar",i]']),
    ("afrofashion", "African fashion & tailoring", DIASPORA, "UK US", "African fashion tailor",
     ['["shop"~"clothes|tailor|fashion|boutique"]["name"~"african|ankara|kente|afri|couture|aso",i]', name("ankara|kente|african fashion")]),
]

# TomTom search words: its own category names where they exist (dentist, pharmacy, car wash...), otherwise
# trade words that its name search matches. Several words = several searches, merged.
TOMTOM = {
    "plumbers": ["plumber", "plumbing"], "electricians": ["electrician", "electrical contractor"], "roofers": ["roofing", "roofer"],
    "builders": ["builder", "construction company"], "hvac": ["air conditioning", "hvac"], "gas": ["heating engineer", "boiler"],
    "locksmiths": ["locksmith"], "painters": ["painter decorator", "painting"], "carpenters": ["carpenter", "joinery"],
    "landscapers": ["landscaping", "gardener"], "tree": ["tree surgeon", "tree service"], "pest": ["pest control"],
    "cleaning": ["cleaning services", "cleaners"], "removals": ["removals", "moving company"], "pressure": ["pressure washing"],
    "pools": ["pool service", "swimming pool contractor"], "junk": ["junk removal", "rubbish removal"], "garagedoors": ["garage door"],
    "windows": ["window cleaning"], "solar": ["solar", "inverter"], "interior": ["interior design", "interior decorator"],
    "furniture": ["furniture"], "materials": ["building materials", "hardware"],
    "dentists": ["dentist"], "clinics": ["hospital", "clinic"], "pharmacies": ["pharmacy"], "labs": ["laboratory", "diagnostic centre"],
    "physio": ["physiotherapist", "physiotherapy"], "chiro": ["chiropractor"], "opticians": ["optician"], "vets": ["veterinarian"],
    "care": ["home care", "care agency"], "aesthetics": ["aesthetics clinic", "med spa", "beauty clinic"],
    "salons": ["hairdresser", "hair salon"], "barbers": ["barber"], "beauty": ["beauty salon", "nail salon"], "spas": ["spa", "massage"],
    "tattoo": ["tattoo"], "gyms": ["gym", "fitness"], "martial": ["martial arts", "dance school"], "groomers": ["dog grooming", "pet grooming"],
    "restaurants": ["restaurant"], "cafes": ["cafe"], "takeaways": ["fast food", "takeaway"], "bakeries": ["bakery", "cakes"],
    "caterers": ["catering", "caterer"], "bars": ["bar", "lounge"],
    "shortlets": ["apartment rental", "serviced apartment", "short let"], "hotels": ["hotel"], "bnb": ["bed and breakfast", "guest house"],
    "realestate": ["real estate agent", "estate agent"], "letting": ["letting agent"], "venues": ["event venue", "event centre"],
    "planners": ["event planner", "wedding planner"], "photographers": ["photographer", "photo studio"], "florists": ["florist"],
    "schools": ["school"], "nurseries": ["nursery school", "child care", "creche"], "tutors": ["tutoring", "tuition"],
    "driving": ["driving school"], "lawyers": ["lawyer", "solicitor"], "immigration": ["immigration lawyer", "visa"],
    "accountants": ["accountant"], "tax": ["tax preparation", "tax advisor"], "insurance": ["insurance agent", "insurance"],
    "mortgage": ["mortgage broker"], "recruitment": ["recruitment agency", "employment agency"], "travel": ["travel agent"],
    "printing": ["printing", "printer"], "logistics": ["logistics", "courier"], "laundry": ["laundry", "dry cleaner"],
    "churches": ["church"], "fashion": ["tailor", "fashion designer"], "boutiques": ["clothing store", "boutique"],
    "phones": ["mobile phone shop", "electronics"], "supermarkets": ["supermarket"], "cardealers": ["car dealer"],
    "mechanics": ["car repair", "mechanic"], "mot": ["mot test", "mot centre"], "bodyshops": ["body shop", "collision repair"],
    "towing": ["towing", "vehicle recovery"], "carwash": ["car wash", "car detailing"], "carhire": ["rent-a-car facility", "car rental"],
    "afrofood": ["african restaurant", "caribbean restaurant", "nigerian restaurant"],
    "afrostores": ["african food store", "african shop", "caribbean food"], "braids": ["braiding", "afro hair"],
    "cargo": ["cargo to nigeria", "shipping to africa", "cargo"], "afrochurch": ["rccg", "redeemed christian church", "pentecostal church"],
    "afrofashion": ["african fashion", "ankara"],
}

ALL = {c[0]: {"id": c[0], "label": c[1], "group": c[2], "markets": c[3].split(), "google": c[4], "osm": c[5],
              "tomtom": TOMTOM.get(c[0], [c[4]])} for c in _C}
missing = [c[0] for c in _C if c[0] not in TOMTOM]
GROUPS = list(dict.fromkeys(c[2] for c in _C))


def get(cid):
    return ALL.get(cid)


def custom(keyword):
    """A free-text business type. 'braids, locs' becomes a name search for either word."""
    words = [re.sub(r"[^\w &'-]", "", w, flags=re.U).strip() for w in re.split(r"[,|/]", keyword)]
    words = [w for w in words if w]
    if not words:
        return None
    label = keyword.strip()[:60]
    return {"id": "custom", "label": label[:1].upper() + label[1:], "group": "Custom", "markets": [], "google": keyword.strip(),
            "osm": [name("|".join(words))], "tomtom": words[:3]}


def public():
    return [{k: c[k] for k in ("id", "label", "group", "markets")} for c in ALL.values()]
