# THIS FILE CONTAINS CONFIGURATION PARAMETERS OF THE CALCULATION ENGINE.
# MUST LIVE IN "caleng" MODULE


# DICTIONARY OF CALCULATIONS
# USED TO WRITE THE CALCULATION TITLE
CALCULATION_NAMES = {
    "S001": "Beam to column with endplate",
    "S002": "Seismic bracing joint with cover plates",
    "S003": "Beam frontplate joint with arriving bracing",
    "S004": "Beam to column with end-plate and arriving bracings",
    "S005": "Beam to beam with endplate",
    "S006": "Beam to beam shear connection",
    "S007": "Endplates column splice",
    "S008": "Coverplates column splice",
    "S009": "Endplates beam splice",
    # "S010": "Coverplates beam splice",
    # "S011": "Hinge - Pinned connection",
    # "S012": "Column baseplate (to concrete)",
    "S099": "XXXXX",
    "P001": "Primitive: Cat-A/B/C Shear bolt group",
    "P002": "Primitive: Cat-D/E Tension/Moment bolt group",
    "P003": "Primitive: Cat-A/B/C FrontPlate",
    "P004": "Primitive: Cat-D/E FrontPlate T-Stub",
    # "P005": "Primitive: Simple H/U Stiffener",
}

# DICTIONARY OF CODES
# IT IS USED TO WRITE THE CALCULATION TITLE

CODE_NAMES = {
    "EC3": "Eurocode 3: EN1993-1-8",
    "AISC11": "Specification for Structural Steel Buildings",
    "NSR10": "Reglamento Colombiano de Construccion Sismo Resistente",
}


# DICTIONARY OF CALCULATION LINKS.
# THIS IS USED TO POPULATE DE ENGINESHEET NAVBAR
# ITS A LIST OF TUPLES BECAUSE OF THE ORDERING
# OF THE ITEMS WHEN DJANGO RENDERS THE LIST
CALCULATION_LINKS = [
    ("S001", "/engine/S001/EC3/"),
    ("S002", "/engine/S002/EC3/"),
    ("S003", "/engine/S003/EC3/"),
    ("S004", "/engine/S004/EC3/"),
    ("S005", "/engine/S005/EC3/"),
    ("S006", "/engine/S006/EC3/"),
    ("S007", "/engine/S007/EC3/"),
    ("S008", "/engine/S008/EC3/"),
    ("S009", "/engine/S009/EC3/"),
    # ("S010", "/engine/S010/EC3/"),
    # ("S011", "/engine/S011/EC3/"),
    # ("S012", "/engine/S012/EC3/"),
    ("P001", "/engine/P001/EC3/"),
    ("P002", "/engine/P002/EC3/"),
    ("P003", "/engine/P003/EC3/"),
    ("P004", "/engine/P004/EC3/"),
    # ("P005", "/engine/P005/EC3/"),
]

# LIST OF CALCULATIONS
CALCULATIONS = [i[0] for i in CALCULATION_LINKS]
# LIST OF CODES
CODES = list(CODE_NAMES.keys())
# ("P005", "/engine/P005/EC3/", "Beam to beam with endplate")
CALCULATION_LINKS_AND_NAMES_TUPLE_LIST = [
    (i[0], i[1], CALCULATION_NAMES[i[0]]) for i in CALCULATION_LINKS
]
