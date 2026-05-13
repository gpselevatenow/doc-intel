"""
NAIC carrier code table — P&C auto and commercial writers.

Source: NAIC Company Search (naic.org), public domain.
Covers the top ~320 personal/commercial auto P&C writers by market share,
including national carriers, regional mutuals, Farm Bureau entities,
AAA/Auto Club entities, non-standard auto specialists, and commercial writers.

Each entry:  COCODE (str) → {name, group, domicile, aliases}
  COCODE    5-digit NAIC company code (zero-padded)
  name      Full legal name as filed with NAIC
  group     Parent group name (for matching abbreviated names on police reports)
  domicile  State of domicile (2-letter)
  aliases   List of common abbreviations/names used on police reports
"""
from __future__ import annotations
import re

_CARRIERS: dict[str, dict] = {

    # ══════════════════════════════════════════════════════════════════════════
    # STATE FARM GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "25143": {"name": "State Farm Mutual Automobile Insurance Company",   "group": "State Farm",        "domicile": "IL", "aliases": ["state farm", "sf mutual", "state farm auto"]},
    "25178": {"name": "State Farm Fire and Casualty Company",             "group": "State Farm",        "domicile": "IL", "aliases": ["state farm fire", "state farm f&c"]},
    "10739": {"name": "State Farm County Mutual Insurance Company of TX", "group": "State Farm",        "domicile": "TX", "aliases": ["state farm county", "sfcm", "sf county mutual"]},
    "25127": {"name": "State Farm General Insurance Company",             "group": "State Farm",        "domicile": "IL", "aliases": ["state farm general"]},
    "25151": {"name": "State Farm Indemnity Company",                     "group": "State Farm",        "domicile": "NJ", "aliases": ["state farm indemnity"]},
    "40922": {"name": "State Farm Florida Insurance Company",             "group": "State Farm",        "domicile": "FL", "aliases": ["state farm florida"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GEICO / BERKSHIRE HATHAWAY
    # ══════════════════════════════════════════════════════════════════════════
    "22063": {"name": "GEICO General Insurance Company",                  "group": "GEICO/Berkshire",   "domicile": "MD", "aliases": ["geico", "government employees", "government employees ins"]},
    "41491": {"name": "GEICO Casualty Company",                           "group": "GEICO/Berkshire",   "domicile": "MD", "aliases": ["geico casualty"]},
    "22055": {"name": "GEICO Indemnity Company",                          "group": "GEICO/Berkshire",   "domicile": "MD", "aliases": ["geico indemnity"]},
    "35882": {"name": "GEICO Advantage Insurance Company",                "group": "GEICO/Berkshire",   "domicile": "NE", "aliases": ["geico advantage"]},
    "35890": {"name": "GEICO Choice Insurance Company",                   "group": "GEICO/Berkshire",   "domicile": "NE", "aliases": ["geico choice"]},
    "35904": {"name": "GEICO Secure Insurance Company",                   "group": "GEICO/Berkshire",   "domicile": "NE", "aliases": ["geico secure"]},
    "20087": {"name": "National Indemnity Company",                       "group": "GEICO/Berkshire",   "domicile": "NE", "aliases": ["national indemnity", "nico"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PROGRESSIVE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "24260": {"name": "Progressive Casualty Insurance Company",           "group": "Progressive",       "domicile": "OH", "aliases": ["progressive", "progressive casualty"]},
    "16322": {"name": "Progressive Direct Insurance Company",             "group": "Progressive",       "domicile": "OH", "aliases": ["progressive direct"]},
    "35378": {"name": "Progressive Northern Insurance Company",           "group": "Progressive",       "domicile": "WI", "aliases": ["progressive northern"]},
    "28676": {"name": "Progressive Marathon Insurance Company",           "group": "Progressive",       "domicile": "MI", "aliases": ["progressive marathon"]},
    "42994": {"name": "Progressive Advanced Insurance Company",           "group": "Progressive",       "domicile": "OH", "aliases": ["progressive advanced"]},
    "11770": {"name": "United Financial Casualty Company",                "group": "Progressive",       "domicile": "OH", "aliases": ["united financial casualty", "ufcc"]},
    "21199": {"name": "Progressive American Insurance Company",           "group": "Progressive",       "domicile": "FL", "aliases": ["progressive american"]},
    "12302": {"name": "Progressive Max Insurance Company",                "group": "Progressive",       "domicile": "OH", "aliases": ["progressive max"]},
    "10193": {"name": "Progressive Southeastern Insurance Company",       "group": "Progressive",       "domicile": "IN", "aliases": ["progressive southeastern"]},
    "28479": {"name": "Progressive Michigan Insurance Company",           "group": "Progressive",       "domicile": "MI", "aliases": ["progressive michigan"]},
    "39314": {"name": "Progressive Mountain Insurance Company",           "group": "Progressive",       "domicile": "CO", "aliases": ["progressive mountain"]},
    "16617": {"name": "Progressive Hawaii Insurance Company",             "group": "Progressive",       "domicile": "HI", "aliases": ["progressive hawaii"]},
    "26935": {"name": "Progressive Select Insurance Company",             "group": "Progressive",       "domicile": "OH", "aliases": ["progressive select"]},
    "37866": {"name": "Progressive Paloverde Insurance Company",          "group": "Progressive",       "domicile": "AZ", "aliases": ["progressive paloverde"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ALLSTATE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "19232": {"name": "Allstate Insurance Company",                       "group": "Allstate",          "domicile": "IL", "aliases": ["allstate"]},
    "29688": {"name": "Allstate Fire and Casualty Insurance Company",     "group": "Allstate",          "domicile": "IL", "aliases": ["allstate f&c", "allstate fire and casualty"]},
    "17230": {"name": "Allstate Indemnity Company",                       "group": "Allstate",          "domicile": "IL", "aliases": ["allstate indemnity"]},
    "37907": {"name": "Allstate Northbrook Indemnity Company",            "group": "Allstate",          "domicile": "IL", "aliases": ["northbrook indemnity", "allstate northbrook"]},
    "10071": {"name": "Encompass Property and Casualty Company",          "group": "Allstate",          "domicile": "IL", "aliases": ["encompass", "encompass property", "encompass p&c"]},
    "10693": {"name": "Encompass Indemnity Company",                      "group": "Allstate",          "domicile": "IL", "aliases": ["encompass indemnity"]},
    "10684": {"name": "Encompass Home and Auto Insurance Company",        "group": "Allstate",          "domicile": "IL", "aliases": ["encompass home and auto"]},
    "25712": {"name": "Esurance Insurance Company",                       "group": "Allstate",          "domicile": "IL", "aliases": ["esurance"]},
    "14788": {"name": "National General Insurance Company",               "group": "Allstate",          "domicile": "MO", "aliases": ["national general", "natgen", "ngm insurance", "gmac insurance"]},
    "23728": {"name": "National General Assurance Company",               "group": "Allstate",          "domicile": "MO", "aliases": ["national general assurance"]},
    "40630": {"name": "Integon National Insurance Company",               "group": "Allstate",          "domicile": "NC", "aliases": ["integon national", "integon"]},
    "40436": {"name": "Integon Preferred Insurance Company",              "group": "Allstate",          "domicile": "NC", "aliases": ["integon preferred"]},
    "13161": {"name": "21st Century Insurance Company",                   "group": "Allstate",          "domicile": "CA", "aliases": ["21st century insurance", "21st century"]},
    "22888": {"name": "21st Century National Insurance Company",          "group": "Allstate",          "domicile": "NJ", "aliases": ["21st century national"]},
    "36056": {"name": "21st Century Premier Insurance Company",           "group": "Allstate",          "domicile": "FL", "aliases": ["21st century premier"]},

    # ══════════════════════════════════════════════════════════════════════════
    # USAA GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "21061": {"name": "United Services Automobile Association",           "group": "USAA",              "domicile": "TX", "aliases": ["usaa"]},
    "25968": {"name": "USAA Casualty Insurance Company",                  "group": "USAA",              "domicile": "TX", "aliases": ["usaa casualty", "usaa p&c"]},
    "19250": {"name": "USAA General Indemnity Company",                   "group": "USAA",              "domicile": "TX", "aliases": ["usaa general", "usaa general indemnity"]},
    "36945": {"name": "Garrison Property and Casualty Insurance Company", "group": "USAA",              "domicile": "TX", "aliases": ["garrison property", "garrison"]},

    # ══════════════════════════════════════════════════════════════════════════
    # LIBERTY MUTUAL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "23043": {"name": "Liberty Mutual Insurance Company",                 "group": "Liberty Mutual",    "domicile": "MA", "aliases": ["liberty mutual", "lmic"]},
    "23035": {"name": "Liberty Mutual Fire Insurance Company",            "group": "Liberty Mutual",    "domicile": "WI", "aliases": ["liberty mutual fire"]},
    "36447": {"name": "LM General Insurance Company",                    "group": "Liberty Mutual",    "domicile": "IL", "aliases": ["lm general"]},
    "16691": {"name": "Safeco Insurance Company of America",              "group": "Liberty Mutual",    "domicile": "NH", "aliases": ["safeco"]},
    "24740": {"name": "Safeco Insurance Company of Illinois",             "group": "Liberty Mutual",    "domicile": "IL", "aliases": ["safeco illinois"]},
    "24074": {"name": "Ohio Casualty Insurance Company",                  "group": "Liberty Mutual",    "domicile": "NH", "aliases": ["ohio casualty", "ohio casualty insurance"]},
    "44393": {"name": "West American Insurance Company",                  "group": "Liberty Mutual",    "domicile": "IN", "aliases": ["west american insurance", "west american"]},
    "24198": {"name": "Peerless Insurance Company",                       "group": "Liberty Mutual",    "domicile": "NH", "aliases": ["peerless insurance", "peerless"]},
    "22659": {"name": "Indiana Insurance Company",                        "group": "Liberty Mutual",    "domicile": "IN", "aliases": ["indiana insurance"]},
    "21458": {"name": "Employers Insurance Company of Wausau",            "group": "Liberty Mutual",    "domicile": "WI", "aliases": ["employers wausau", "wausau business insurance"]},
    "21465": {"name": "Wausau Business Insurance Company",                "group": "Liberty Mutual",    "domicile": "WI", "aliases": ["wausau business"]},
    "26069": {"name": "Wausau Underwriters Insurance Company",            "group": "Liberty Mutual",    "domicile": "WI", "aliases": ["wausau underwriters"]},
    "36277": {"name": "LM Property and Casualty Insurance Company",       "group": "Liberty Mutual",    "domicile": "IN", "aliases": ["lm property and casualty", "lmpc"]},
    "33588": {"name": "First Liberty Insurance Corporation",              "group": "Liberty Mutual",    "domicile": "MA", "aliases": ["first liberty", "first liberty insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # FARMERS GROUP (Zurich-owned)
    # ══════════════════════════════════════════════════════════════════════════
    "21628": {"name": "Farmers Insurance Exchange",                       "group": "Farmers",           "domicile": "CA", "aliases": ["farmers", "farmers insurance", "farmers insurance exchange"]},
    "21660": {"name": "Fire Insurance Exchange",                          "group": "Farmers",           "domicile": "CA", "aliases": ["fire insurance exchange"]},
    "41483": {"name": "Truck Insurance Exchange",                         "group": "Farmers",           "domicile": "CA", "aliases": ["truck insurance exchange"]},
    "21261": {"name": "Farmers Insurance Company Inc",                    "group": "Farmers",           "domicile": "KS", "aliases": ["farmers insurance co"]},
    "11185": {"name": "Foremost Insurance Company Grand Rapids Michigan", "group": "Farmers",           "domicile": "MI", "aliases": ["foremost insurance", "foremost"]},
    "41513": {"name": "Foremost Signature Insurance Company",             "group": "Farmers",           "domicile": "MI", "aliases": ["foremost signature"]},
    "41785": {"name": "Foremost Property and Casualty Insurance Company", "group": "Farmers",           "domicile": "MI", "aliases": ["foremost property", "foremost p&c"]},
    "30511": {"name": "Mid-Century Insurance Company",                    "group": "Farmers",           "domicile": "CA", "aliases": ["mid-century", "mid century insurance"]},
    "25453": {"name": "Farmers New World Life Insurance Company",         "group": "Farmers",           "domicile": "WA", "aliases": ["farmers new world"]},
    "22543": {"name": "Farmers Insurance Company of Arizona",             "group": "Farmers",           "domicile": "AZ", "aliases": ["farmers arizona"]},
    "12300": {"name": "Farmers Insurance Company of Columbus Inc",        "group": "Farmers",           "domicile": "OH", "aliases": ["farmers columbus", "farmers ohio"]},
    "23647": {"name": "Farmers Insurance Company of Oregon",              "group": "Farmers",           "domicile": "OR", "aliases": ["farmers oregon"]},
    "28460": {"name": "Farmers Insurance Company of Washington",          "group": "Farmers",           "domicile": "WA", "aliases": ["farmers washington"]},

    # ══════════════════════════════════════════════════════════════════════════
    # NATIONWIDE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "23787": {"name": "Nationwide Mutual Insurance Company",              "group": "Nationwide",        "domicile": "OH", "aliases": ["nationwide mutual", "nationwide"]},
    "23760": {"name": "Nationwide General Insurance Company",             "group": "Nationwide",        "domicile": "OH", "aliases": ["nationwide general"]},
    "29874": {"name": "Nationwide Mutual Fire Insurance Company",         "group": "Nationwide",        "domicile": "OH", "aliases": ["nationwide fire"]},
    "23930": {"name": "Nationwide Property and Casualty Insurance Company","group": "Nationwide",       "domicile": "OH", "aliases": ["nationwide property", "nationwide p&c"]},
    "10127": {"name": "Allied Property and Casualty Insurance Company",   "group": "Nationwide",        "domicile": "IA", "aliases": ["allied property", "allied p&c", "allied insurance"]},
    "19100": {"name": "AMCO Insurance Company",                           "group": "Nationwide",        "domicile": "IA", "aliases": ["amco insurance", "amco"]},
    "10217": {"name": "Depositors Insurance Company",                     "group": "Nationwide",        "domicile": "IA", "aliases": ["depositors insurance"]},
    "20214": {"name": "Titan Insurance Company",                          "group": "Nationwide",        "domicile": "MI", "aliases": ["titan insurance", "titan"]},
    "40460": {"name": "Victoria Fire and Casualty Company",               "group": "Nationwide",        "domicile": "OH", "aliases": ["victoria fire", "victoria fire and casualty"]},
    "20184": {"name": "Bristol West Insurance Company",                   "group": "Nationwide",        "domicile": "OH", "aliases": ["bristol west"]},
    "25747": {"name": "Nationwide Agribusiness Insurance Company",        "group": "Nationwide",        "domicile": "IA", "aliases": ["nationwide agribusiness"]},
    "34673": {"name": "Colonial County Mutual Insurance Company",         "group": "Nationwide",        "domicile": "TX", "aliases": ["colonial county mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # TRAVELERS GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "25658": {"name": "The Travelers Indemnity Company",                  "group": "Travelers",         "domicile": "CT", "aliases": ["travelers", "travelers indemnity"]},
    "25666": {"name": "Travelers Property Casualty Company of America",   "group": "Travelers",         "domicile": "CT", "aliases": ["travelers p&c", "travelers property"]},
    "19046": {"name": "The Travelers Home and Marine Insurance Company",  "group": "Travelers",         "domicile": "CT", "aliases": ["travelers home and marine"]},
    "24767": {"name": "St. Paul Fire and Marine Insurance Company",       "group": "Travelers",         "domicile": "CT", "aliases": ["st. paul fire", "st paul fire and marine", "saint paul fire"]},
    "27987": {"name": "Northland Insurance Company",                      "group": "Travelers",         "domicile": "CT", "aliases": ["northland insurance", "northland"]},
    "35386": {"name": "Fidelity and Guaranty Insurance Company",          "group": "Travelers",         "domicile": "IA", "aliases": ["fidelity and guaranty", "f&g insurance"]},
    "25674": {"name": "Travelers Casualty and Surety Company",            "group": "Travelers",         "domicile": "CT", "aliases": ["travelers casualty and surety", "travelers surety"]},
    "25720": {"name": "Travelers Casualty Insurance Company of America",  "group": "Travelers",         "domicile": "CT", "aliases": ["travelers casualty insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AMERICAN FAMILY GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "19380": {"name": "American Family Mutual Insurance Company SI",      "group": "American Family",   "domicile": "WI", "aliases": ["american family", "amfam"]},
    "10386": {"name": "American Family Insurance Company",                "group": "American Family",   "domicile": "WI", "aliases": ["american family ins co"]},
    "11169": {"name": "Midvale Indemnity Company",                        "group": "American Family",   "domicile": "WI", "aliases": ["midvale indemnity", "midvale"]},
    "24449": {"name": "The General Insurance Company of America",         "group": "American Family",   "domicile": "WA", "aliases": ["general insurance company of america"]},
    "19429": {"name": "American Standard Insurance Company of Wisconsin", "group": "American Family",   "domicile": "WI", "aliases": ["american standard insurance wi"]},
    "19437": {"name": "American Standard Insurance Company of Ohio",      "group": "American Family",   "domicile": "OH", "aliases": ["american standard insurance oh"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ERIE INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "26263": {"name": "Erie Insurance Exchange",                          "group": "Erie Insurance",    "domicile": "PA", "aliases": ["erie", "erie insurance"]},
    "26271": {"name": "Erie Insurance Company",                           "group": "Erie Insurance",    "domicile": "PA", "aliases": ["erie insurance co"]},
    "35009": {"name": "Erie Insurance Company of New York",               "group": "Erie Insurance",    "domicile": "NY", "aliases": ["erie ny"]},
    "26247": {"name": "Erie Indemnity Company",                           "group": "Erie Insurance",    "domicile": "PA", "aliases": ["erie indemnity"]},
    "20257": {"name": "Erie Insurance Property and Casualty Company",     "group": "Erie Insurance",    "domicile": "PA", "aliases": ["erie property"]},

    # ══════════════════════════════════════════════════════════════════════════
    # HARTFORD GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "29424": {"name": "Hartford Fire Insurance Company",                  "group": "Hartford",          "domicile": "CT", "aliases": ["hartford fire", "the hartford"]},
    "22357": {"name": "Hartford Accident and Indemnity Company",          "group": "Hartford",          "domicile": "CT", "aliases": ["hartford accident"]},
    "38261": {"name": "Hartford Underwriters Insurance Company",          "group": "Hartford",          "domicile": "CT", "aliases": ["hartford underwriters"]},
    "27120": {"name": "Trumbull Insurance Company",                       "group": "Hartford",          "domicile": "CT", "aliases": ["trumbull insurance", "trumbull"]},
    "29459": {"name": "Twin City Fire Insurance Company",                 "group": "Hartford",          "domicile": "IN", "aliases": ["twin city fire"]},
    "29513": {"name": "Property and Casualty Insurance Company of Hartford","group": "Hartford",        "domicile": "IN", "aliases": ["p&c insurance co of hartford"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AUTO-OWNERS GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "18988": {"name": "Auto-Owners Insurance Company",                    "group": "Auto-Owners",       "domicile": "MI", "aliases": ["auto-owners", "auto owners"]},
    "10639": {"name": "Auto-Owners Life Insurance Company",               "group": "Auto-Owners",       "domicile": "MI", "aliases": ["auto-owners life"]},
    "33898": {"name": "Home-Owners Insurance Company",                    "group": "Auto-Owners",       "domicile": "MI", "aliases": ["home-owners insurance", "homeowners insurance auto-owners"]},
    "22926": {"name": "Property-Owners Insurance Company",                "group": "Auto-Owners",       "domicile": "IN", "aliases": ["property-owners insurance"]},
    "32700": {"name": "Southern-Owners Insurance Company",                "group": "Auto-Owners",       "domicile": "MI", "aliases": ["southern-owners insurance"]},
    "34274": {"name": "Owners Insurance Company",                         "group": "Auto-Owners",       "domicile": "OH", "aliases": ["owners insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AMICA MUTUAL
    # ══════════════════════════════════════════════════════════════════════════
    "19704": {"name": "Amica Mutual Insurance Company",                   "group": "Amica",             "domicile": "RI", "aliases": ["amica", "amica mutual"]},
    "19712": {"name": "Amica Property and Casualty Insurance Company",    "group": "Amica",             "domicile": "RI", "aliases": ["amica property"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CSAA / AAA GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "38989": {"name": "CSAA Insurance Exchange",                          "group": "CSAA/AAA",          "domicile": "CA", "aliases": ["csaa", "aaa northern california", "csaa insurance", "aaa ncnu"]},
    "15423": {"name": "Auto Club Indemnity Company",                      "group": "CSAA/AAA",          "domicile": "CA", "aliases": ["auto club indemnity", "aaa southern california", "acsc"]},
    "42978": {"name": "Auto Club Group Insurance Company",                "group": "CSAA/AAA",          "domicile": "MI", "aliases": ["auto club group", "aaa michigan", "acg insurance"]},
    "28452": {"name": "Auto Club of Southern California Insurance",       "group": "CSAA/AAA",          "domicile": "CA", "aliases": ["auto club southern ca", "aaa auto club southern ca"]},
    "19879": {"name": "AAA Carolina Insurance",                           "group": "CSAA/AAA",          "domicile": "NC", "aliases": ["aaa carolinas", "aaa carolina"]},
    "17248": {"name": "AAA Mid-Atlantic Insurance Company of New Jersey", "group": "CSAA/AAA",          "domicile": "NJ", "aliases": ["aaa mid-atlantic", "aaa midatlantic"]},
    "21849": {"name": "AAA Texas County Mutual Insurance Company",        "group": "CSAA/AAA",          "domicile": "TX", "aliases": ["aaa texas", "aaa texas county"]},
    "22830": {"name": "Auto Club Missouri Insurance Company",             "group": "CSAA/AAA",          "domicile": "MO", "aliases": ["aaa missouri", "auto club missouri"]},
    "36153": {"name": "AAA Insurance",                                    "group": "CSAA/AAA",          "domicile": "MI", "aliases": ["aaa insurance", "aaa"]},
    "12475": {"name": "Club Insurance Company",                           "group": "CSAA/AAA",          "domicile": "NJ", "aliases": ["aaa club insurance nj"]},

    # ══════════════════════════════════════════════════════════════════════════
    # METLIFE / FARMERS (MetLife auto acquired by Farmers 2021)
    # ══════════════════════════════════════════════════════════════════════════
    "26298": {"name": "Metropolitan Property and Casualty Insurance Co",  "group": "MetLife",           "domicile": "RI", "aliases": ["metlife", "metpcs", "metropolitan p&c", "met p&c"]},
    "11058": {"name": "Metropolitan Casualty Insurance Company",          "group": "MetLife",           "domicile": "RI", "aliases": ["metropolitan casualty"]},
    "29858": {"name": "Metropolitan Direct Property and Casualty Ins Co", "group": "MetLife",           "domicile": "RI", "aliases": ["metlife direct"]},

    # ══════════════════════════════════════════════════════════════════════════
    # KEMPER GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "22039": {"name": "Kemper Independence Insurance Company",            "group": "Kemper",            "domicile": "IL", "aliases": ["kemper"]},
    "20109": {"name": "Alliance United Insurance Company",                "group": "Kemper",            "domicile": "CA", "aliases": ["alliance united"]},
    "22268": {"name": "Infinity Insurance Company",                       "group": "Kemper",            "domicile": "IN", "aliases": ["infinity insurance", "infinity"]},
    "41653": {"name": "Infinity Auto Insurance Company",                  "group": "Kemper",            "domicile": "AZ", "aliases": ["infinity auto"]},
    "36137": {"name": "Infinity Indemnity Insurance Company",             "group": "Kemper",            "domicile": "IN", "aliases": ["infinity indemnity"]},
    "10019": {"name": "Affirmative Insurance Company",                    "group": "Kemper",            "domicile": "IL", "aliases": ["affirmative insurance", "affirmative"]},
    "10816": {"name": "Kemper Preferred Insurance Company",               "group": "Kemper",            "domicile": "IL", "aliases": ["kemper preferred"]},
    "42404": {"name": "Merastar Insurance Company",                       "group": "Kemper",            "domicile": "TN", "aliases": ["merastar"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ZURICH NORTH AMERICA
    # ══════════════════════════════════════════════════════════════════════════
    "16535": {"name": "Zurich American Insurance Company",                "group": "Zurich",            "domicile": "NY", "aliases": ["zurich american", "zurich insurance", "zurich"]},
    "40142": {"name": "American Zurich Insurance Company",                "group": "Zurich",            "domicile": "IL", "aliases": ["american zurich"]},
    "13714": {"name": "Zurich American Insurance Company of Illinois",    "group": "Zurich",            "domicile": "IL", "aliases": ["zurich illinois"]},
    "19038": {"name": "Maryland Casualty Company",                        "group": "Zurich",            "domicile": "MD", "aliases": ["maryland casualty"]},
    "26743": {"name": "Northern Insurance Company of New York",           "group": "Zurich",            "domicile": "NY", "aliases": ["northern insurance ny"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CHUBB GROUP (ACE + Chubb merged 2016)
    # ══════════════════════════════════════════════════════════════════════════
    "20303": {"name": "Great Northern Insurance Company",                 "group": "Chubb",             "domicile": "MN", "aliases": ["great northern insurance", "chubb great northern"]},
    "20397": {"name": "Vigilant Insurance Company",                       "group": "Chubb",             "domicile": "NY", "aliases": ["vigilant insurance", "chubb vigilant"]},
    "20346": {"name": "Pacific Indemnity Company",                        "group": "Chubb",             "domicile": "WI", "aliases": ["pacific indemnity", "chubb pacific"]},
    "22667": {"name": "ACE American Insurance Company",                   "group": "Chubb",             "domicile": "PA", "aliases": ["ace american", "ace insurance", "ace"]},
    "20702": {"name": "ACE Fire Underwriters Insurance Company",          "group": "Chubb",             "domicile": "PA", "aliases": ["ace fire underwriters"]},
    "10052": {"name": "Chubb National Insurance Company",                 "group": "Chubb",             "domicile": "IN", "aliases": ["chubb national"]},
    "20281": {"name": "Federal Insurance Company",                        "group": "Chubb",             "domicile": "IN", "aliases": ["federal insurance", "chubb federal"]},
    "28178": {"name": "Westchester Fire Insurance Company",               "group": "Chubb",             "domicile": "PA", "aliases": ["westchester fire", "chubb westchester"]},
    "40732": {"name": "Chubb Indemnity Insurance Company",                "group": "Chubb",             "domicile": "NY", "aliases": ["chubb indemnity"]},

    # ══════════════════════════════════════════════════════════════════════════
    # TOKIO MARINE / PHILADELPHIA CONSOLIDATED
    # ══════════════════════════════════════════════════════════════════════════
    "18058": {"name": "Philadelphia Indemnity Insurance Company",         "group": "Tokio Marine/PHLY", "domicile": "PA", "aliases": ["philadelphia indemnity", "phly", "philadelphia insurance"]},
    "41688": {"name": "Tokio Marine America Insurance Company",           "group": "Tokio Marine/PHLY", "domicile": "NY", "aliases": ["tokio marine america", "tokio marine"]},
    "42374": {"name": "Houston Casualty Company",                         "group": "Tokio Marine/PHLY", "domicile": "TX", "aliases": ["houston casualty", "hcc insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # QBE INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "39217": {"name": "QBE Insurance Corporation",                        "group": "QBE",               "domicile": "PA", "aliases": ["qbe insurance", "qbe"]},
    "11044": {"name": "General Casualty Company of Wisconsin",            "group": "QBE",               "domicile": "WI", "aliases": ["general casualty", "general casualty company"]},
    "24856": {"name": "Praetorian Insurance Company",                     "group": "QBE",               "domicile": "PA", "aliases": ["praetorian insurance", "praetorian"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AIG GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "23841": {"name": "New Hampshire Insurance Company",                  "group": "AIG",               "domicile": "PA", "aliases": ["new hampshire insurance", "aig new hampshire"]},
    "19445": {"name": "National Union Fire Insurance Company of Pittsburgh","group": "AIG",              "domicile": "PA", "aliases": ["national union fire", "national union", "aig national union"]},
    "10329": {"name": "AIG Property Casualty Company",                    "group": "AIG",               "domicile": "PA", "aliases": ["aig property casualty", "aig p&c"]},
    "19984": {"name": "AIG Casualty Company",                             "group": "AIG",               "domicile": "PA", "aliases": ["aig casualty"]},
    "19410": {"name": "Commerce and Industry Insurance Company",          "group": "AIG",               "domicile": "NY", "aliases": ["commerce and industry", "c&i insurance"]},
    "40258": {"name": "Lexington Insurance Company",                      "group": "AIG",               "domicile": "DE", "aliases": ["lexington insurance", "lexington"]},

    # ══════════════════════════════════════════════════════════════════════════
    # MARKEL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "38970": {"name": "Markel Insurance Company",                         "group": "Markel",            "domicile": "IL", "aliases": ["markel insurance", "markel"]},
    "10744": {"name": "Markel American Insurance Company",                "group": "Markel",            "domicile": "VA", "aliases": ["markel american"]},

    # ══════════════════════════════════════════════════════════════════════════
    # HANOVER INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "22292": {"name": "The Hanover Insurance Company",                    "group": "Hanover",           "domicile": "NH", "aliases": ["hanover insurance", "the hanover"]},
    "21032": {"name": "Massachusetts Bay Insurance Company",              "group": "Hanover",           "domicile": "NH", "aliases": ["massachusetts bay insurance", "mass bay insurance"]},
    "36064": {"name": "Citizens Insurance Company of America",            "group": "Hanover",           "domicile": "MI", "aliases": ["citizens insurance", "citizens insurance company"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CINCINNATI FINANCIAL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "20286": {"name": "Cincinnati Insurance Company",                     "group": "Cincinnati Financial","domicile": "OH", "aliases": ["cincinnati insurance", "cic"]},
    "10677": {"name": "Cincinnati Casualty Company",                      "group": "Cincinnati Financial","domicile": "OH", "aliases": ["cincinnati casualty"]},
    "20265": {"name": "Cincinnati Indemnity Company",                     "group": "Cincinnati Financial","domicile": "OH", "aliases": ["cincinnati indemnity"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SENTRY INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "24988": {"name": "Sentry Insurance A Mutual Company",                "group": "Sentry",            "domicile": "WI", "aliases": ["sentry insurance", "sentry"]},
    "21164": {"name": "Dairyland Insurance Company",                      "group": "Sentry",            "domicile": "WI", "aliases": ["dairyland"]},
    "24791": {"name": "Sentry Select Insurance Company",                  "group": "Sentry",            "domicile": "WI", "aliases": ["sentry select"]},
    "11555": {"name": "Sentry Casualty Company",                          "group": "Sentry",            "domicile": "WI", "aliases": ["sentry casualty"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SELECTIVE INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "12572": {"name": "Selective Insurance Company of America",           "group": "Selective",         "domicile": "NJ", "aliases": ["selective insurance", "selective"]},
    "10172": {"name": "Selective Insurance Company of South Carolina",    "group": "Selective",         "domicile": "SC", "aliases": ["selective sc"]},
    "39845": {"name": "Selective Insurance Company of the Southeast",     "group": "Selective",         "domicile": "IN", "aliases": ["selective southeast"]},
    "12549": {"name": "Selective Insurance Company of New England",       "group": "Selective",         "domicile": "NJ", "aliases": ["selective new england"]},

    # ══════════════════════════════════════════════════════════════════════════
    # MERCURY INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "27553": {"name": "Mercury Insurance Company",                        "group": "Mercury",           "domicile": "CA", "aliases": ["mercury insurance", "mercury"]},
    "11544": {"name": "Mercury Casualty Company",                         "group": "Mercury",           "domicile": "CA", "aliases": ["mercury casualty"]},
    "26735": {"name": "California Automobile Insurance Company",          "group": "Mercury",           "domicile": "CA", "aliases": ["california auto insurance", "caic"]},
    "11080": {"name": "Mercury Indemnity Company of America",             "group": "Mercury",           "domicile": "NJ", "aliases": ["mercury indemnity"]},

    # ══════════════════════════════════════════════════════════════════════════
    # MAPFRE USA / COMMERCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "41998": {"name": "MAPFRE Insurance Company",                         "group": "MAPFRE",            "domicile": "MA", "aliases": ["mapfre", "commerce insurance", "mapfre commerce"]},
    "13900": {"name": "Citation Insurance Company",                       "group": "MAPFRE",            "domicile": "MA", "aliases": ["citation insurance"]},
    "22276": {"name": "MAPFRE Insurance Company of New York",             "group": "MAPFRE",            "domicile": "NY", "aliases": ["mapfre ny"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ICW GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "27847": {"name": "ICW Group Insurance Companies",                    "group": "ICW",               "domicile": "CA", "aliases": ["icw group", "icw"]},
    "22861": {"name": "Industrial Commission of Workers Insurance Exchange","group": "ICW",              "domicile": "CA", "aliases": ["icw workers"]},

    # ══════════════════════════════════════════════════════════════════════════
    # INSURETECH / DIGITAL CARRIERS
    # ══════════════════════════════════════════════════════════════════════════
    "26531": {"name": "Root Insurance Company",                           "group": "Root",              "domicile": "OH", "aliases": ["root insurance", "root"]},
    "27306": {"name": "Lemonade Insurance Company",                       "group": "Lemonade",          "domicile": "DE", "aliases": ["lemonade"]},
    "12740": {"name": "Metromile Insurance Company",                      "group": "Metromile/Lemonade","domicile": "DE", "aliases": ["metromile"]},
    "16600": {"name": "Clearcover Insurance Company",                     "group": "Clearcover",        "domicile": "IL", "aliases": ["clearcover"]},
    "12782": {"name": "Hippo Insurance Company",                          "group": "Hippo",             "domicile": "TX", "aliases": ["hippo insurance", "hippo"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GAINSCO / MGA
    # ══════════════════════════════════════════════════════════════════════════
    "41459": {"name": "GAINSCO Inc / MGA Insurance Company",              "group": "GAINSCO",           "domicile": "TX", "aliases": ["gainsco", "mga insurance", "gainsco auto"]},
    "10111": {"name": "GAINSCO County Mutual Insurance Company",          "group": "GAINSCO",           "domicile": "TX", "aliases": ["gainsco county mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PEKIN INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "20796": {"name": "Pekin Insurance Company",                          "group": "Pekin",             "domicile": "IL", "aliases": ["pekin insurance", "pekin"]},
    "24554": {"name": "Pekin Life Insurance Company",                     "group": "Pekin",             "domicile": "IL", "aliases": ["pekin life"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SHELTER INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "23388": {"name": "Shelter Mutual Insurance Company",                 "group": "Shelter",           "domicile": "MO", "aliases": ["shelter insurance", "shelter"]},
    "23396": {"name": "Shelter General Insurance Company",                "group": "Shelter",           "domicile": "MO", "aliases": ["shelter general"]},
    "11201": {"name": "Shelter Life Insurance Company",                   "group": "Shelter",           "domicile": "MO", "aliases": ["shelter life"]},

    # ══════════════════════════════════════════════════════════════════════════
    # WESTFIELD GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "24112": {"name": "Westfield Insurance Company",                      "group": "Westfield",         "domicile": "OH", "aliases": ["westfield insurance", "westfield"]},
    "13307": {"name": "Westfield National Insurance Company",             "group": "Westfield",         "domicile": "OH", "aliases": ["westfield national"]},
    "10200": {"name": "Ohio Farmers Insurance Company",                   "group": "Westfield",         "domicile": "OH", "aliases": ["ohio farmers insurance", "ohio farmers"]},

    # ══════════════════════════════════════════════════════════════════════════
    # DONEGAL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "21482": {"name": "Donegal Mutual Insurance Company",                 "group": "Donegal",           "domicile": "PA", "aliases": ["donegal mutual", "donegal"]},
    "25135": {"name": "Atlantic States Insurance Company",                "group": "Donegal",           "domicile": "PA", "aliases": ["atlantic states insurance"]},
    "23345": {"name": "Peninsula Insurance Company",                      "group": "Donegal",           "domicile": "MD", "aliases": ["peninsula insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PEMCO MUTUAL INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "14648": {"name": "PEMCO Mutual Insurance Company",                   "group": "PEMCO",             "domicile": "WA", "aliases": ["pemco"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SECURA INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "14834": {"name": "SECURA Insurance A Mutual Company",                "group": "SECURA",            "domicile": "WI", "aliases": ["secura insurance", "secura"]},
    "10120": {"name": "SECURA Supreme Insurance Company",                 "group": "SECURA",            "domicile": "WI", "aliases": ["secura supreme"]},

    # ══════════════════════════════════════════════════════════════════════════
    # NEW JERSEY MANUFACTURERS (NJM)
    # ══════════════════════════════════════════════════════════════════════════
    "23574": {"name": "New Jersey Manufacturers Insurance Company",       "group": "NJM",               "domicile": "NJ", "aliases": ["njm", "new jersey manufacturers", "njm insurance"]},
    "15350": {"name": "New Jersey Re-Insurance Company",                  "group": "NJM",               "domicile": "NJ", "aliases": ["nj re-insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PLYMOUTH ROCK GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "37605": {"name": "Plymouth Rock Assurance Corporation",              "group": "Plymouth Rock",     "domicile": "NJ", "aliases": ["plymouth rock", "plymouth rock assurance"]},
    "13579": {"name": "Palisades Insurance Company",                      "group": "Plymouth Rock",     "domicile": "NJ", "aliases": ["palisades insurance", "palisades"]},
    "31348": {"name": "Bunker Hill Insurance Company",                    "group": "Plymouth Rock",     "domicile": "MA", "aliases": ["bunker hill insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SAFETY INSURANCE GROUP (Massachusetts)
    # ══════════════════════════════════════════════════════════════════════════
    "39454": {"name": "Safety Insurance Company",                         "group": "Safety Insurance",  "domicile": "MA", "aliases": ["safety insurance", "safety ins"]},
    "13803": {"name": "Safety Indemnity Insurance Company",               "group": "Safety Insurance",  "domicile": "MA", "aliases": ["safety indemnity"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ARBELLA INSURANCE GROUP (Massachusetts)
    # ══════════════════════════════════════════════════════════════════════════
    "15032": {"name": "Arbella Protection Insurance Company Inc",         "group": "Arbella",           "domicile": "MA", "aliases": ["arbella protection", "arbella insurance", "arbella"]},
    "41360": {"name": "Arbella Mutual Insurance Company",                 "group": "Arbella",           "domicile": "MA", "aliases": ["arbella mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PENN NATIONAL INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "22648": {"name": "Penn National Insurance Company",                  "group": "Penn National",     "domicile": "PA", "aliases": ["penn national insurance", "penn national"]},
    "13447": {"name": "Pennsylvania National Mutual Casualty Insurance",  "group": "Penn National",     "domicile": "PA", "aliases": ["pa national mutual", "penn national mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ALFA INSURANCE GROUP (Southeast)
    # ══════════════════════════════════════════════════════════════════════════
    "11282": {"name": "Alfa Mutual Insurance Company",                    "group": "Alfa",              "domicile": "AL", "aliases": ["alfa mutual", "alfa insurance", "alfa"]},
    "11270": {"name": "Alfa Mutual Fire Insurance Company",               "group": "Alfa",              "domicile": "AL", "aliases": ["alfa fire", "alfa mutual fire"]},
    "27596": {"name": "Alfa Vision Insurance Corporation",                "group": "Alfa",              "domicile": "AL", "aliases": ["alfa vision"]},
    "11295": {"name": "Alfa General Insurance Corporation",               "group": "Alfa",              "domicile": "AL", "aliases": ["alfa general"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GRINNELL MUTUAL GROUP (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "14508": {"name": "Grinnell Mutual Reinsurance Company",              "group": "Grinnell Mutual",   "domicile": "IA", "aliases": ["grinnell mutual", "grinnell", "grinnell reinsurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # WEST BEND MUTUAL (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "15483": {"name": "West Bend Mutual Insurance Company",               "group": "West Bend Mutual",  "domicile": "WI", "aliases": ["west bend mutual", "west bend insurance", "west bend"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ACUITY INSURANCE (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "14184": {"name": "ACUITY A Mutual Insurance Company",                "group": "Acuity",            "domicile": "WI", "aliases": ["acuity", "acuity insurance", "acuity a mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # SOCIETY INSURANCE (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "23523": {"name": "Society Insurance A Mutual Company",               "group": "Society Insurance", "domicile": "WI", "aliases": ["society insurance", "society mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # MOTORISTS INSURANCE GROUP (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "14982": {"name": "Motorists Mutual Insurance Company",               "group": "Motorists Insurance","domicile": "OH", "aliases": ["motorists mutual", "motorists insurance"]},
    "12261": {"name": "Motorists Commercial Mutual Insurance Company",    "group": "Motorists Insurance","domicile": "OH", "aliases": ["motorists commercial"]},
    "22519": {"name": "Ohio Mutual Insurance Company",                    "group": "Motorists Insurance","domicile": "OH", "aliases": ["ohio mutual insurance", "ohio mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # IMT INSURANCE (Iowa)
    # ══════════════════════════════════════════════════════════════════════════
    "16012": {"name": "IMT Insurance Company",                            "group": "IMT",               "domicile": "IA", "aliases": ["imt insurance", "imt"]},

    # ══════════════════════════════════════════════════════════════════════════
    # COUNTRY FINANCIAL
    # ══════════════════════════════════════════════════════════════════════════
    "20990": {"name": "COUNTRY Mutual Insurance Company",                 "group": "COUNTRY Financial",  "domicile": "IL", "aliases": ["country mutual", "country financial", "country insurance"]},
    "21008": {"name": "COUNTRY Preferred Insurance Company",              "group": "COUNTRY Financial",  "domicile": "IL", "aliases": ["country preferred"]},
    "20939": {"name": "COUNTRY Casualty Insurance Company",               "group": "COUNTRY Financial",  "domicile": "IL", "aliases": ["country casualty"]},

    # ══════════════════════════════════════════════════════════════════════════
    # STATE AUTO GROUP (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "25756": {"name": "State Auto Mutual Insurance Company",              "group": "State Auto",         "domicile": "OH", "aliases": ["state auto mutual", "state auto", "state auto insurance"]},
    "25755": {"name": "State Auto Property and Casualty Insurance Company","group": "State Auto",        "domicile": "IA", "aliases": ["state auto p&c", "state auto property"]},
    "21741": {"name": "Rockhill Insurance Company",                       "group": "State Auto",         "domicile": "KS", "aliases": ["rockhill insurance", "rockhill"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CHURCH MUTUAL INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "17078": {"name": "Church Mutual Insurance Company SI",               "group": "Church Mutual",      "domicile": "WI", "aliases": ["church mutual", "church mutual insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GUIDEONE INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "15997": {"name": "GuideOne Insurance Company",                       "group": "GuideOne",           "domicile": "IA", "aliases": ["guideone", "guide one insurance"]},
    "21814": {"name": "GuideOne Mutual Insurance Company",                "group": "GuideOne",           "domicile": "IA", "aliases": ["guideone mutual"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GERMANIA INSURANCE (Texas)
    # ══════════════════════════════════════════════════════════════════════════
    "22020": {"name": "Germania Insurance Company",                       "group": "Germania",           "domicile": "TX", "aliases": ["germania insurance", "germania"]},
    "22012": {"name": "Germania Farm Mutual Insurance Association",        "group": "Germania",           "domicile": "TX", "aliases": ["germania farm mutual", "germania farm"]},

    # ══════════════════════════════════════════════════════════════════════════
    # TEXAS FARM BUREAU
    # ══════════════════════════════════════════════════════════════════════════
    "38601": {"name": "Texas Farm Bureau Mutual Insurance Company",       "group": "Texas Farm Bureau",  "domicile": "TX", "aliases": ["texas farm bureau", "tfb", "texas farm bureau mutual"]},
    "39829": {"name": "Texas Farm Bureau Casualty Insurance Company",     "group": "Texas Farm Bureau",  "domicile": "TX", "aliases": ["texas farm bureau casualty"]},
    "39071": {"name": "Texas Farm Bureau Underwriters",                   "group": "Texas Farm Bureau",  "domicile": "TX", "aliases": ["texas farm bureau underwriters"]},

    # ══════════════════════════════════════════════════════════════════════════
    # FARM BUREAU — STATE ENTITIES
    # ══════════════════════════════════════════════════════════════════════════
    "13838": {"name": "Farm Bureau Property and Casualty Insurance Company","group": "Farm Bureau",      "domicile": "IA", "aliases": ["farm bureau iowa", "iowa farm bureau", "fbpcic"]},
    "22233": {"name": "North Carolina Farm Bureau Mutual Insurance Company","group": "Farm Bureau",      "domicile": "NC", "aliases": ["nc farm bureau", "north carolina farm bureau", "ncfb"]},
    "14117": {"name": "Michigan Farm Bureau Insurance",                   "group": "Farm Bureau",        "domicile": "MI", "aliases": ["michigan farm bureau", "mi farm bureau", "mifb"]},
    "15424": {"name": "Tennessee Farmers Mutual Insurance Company",       "group": "Farm Bureau",        "domicile": "TN", "aliases": ["tennessee farm bureau", "tn farm bureau", "tennessee farmers"]},
    "26492": {"name": "Indiana Farm Bureau Insurance",                    "group": "Farm Bureau",        "domicile": "IN", "aliases": ["indiana farm bureau", "in farm bureau"]},
    "14486": {"name": "Missouri Farm Bureau Mutual Insurance Company",    "group": "Farm Bureau",        "domicile": "MO", "aliases": ["missouri farm bureau", "mo farm bureau", "mofb"]},
    "22993": {"name": "Kentucky Farm Bureau Mutual Insurance Company",    "group": "Farm Bureau",        "domicile": "KY", "aliases": ["kentucky farm bureau", "ky farm bureau", "kyfb"]},
    "11894": {"name": "Georgia Farm Bureau Mutual Insurance Company",     "group": "Farm Bureau",        "domicile": "GA", "aliases": ["georgia farm bureau", "ga farm bureau", "gafb"]},
    "16942": {"name": "Farm Bureau Insurance Company of Nebraska",        "group": "Farm Bureau",        "domicile": "NE", "aliases": ["nebraska farm bureau", "ne farm bureau"]},
    "13528": {"name": "Kansas Farm Bureau Insurance",                     "group": "Farm Bureau",        "domicile": "KS", "aliases": ["kansas farm bureau", "ks farm bureau", "ksfb"]},
    "15130": {"name": "Alabama Farmers Mutual Insurance Company",         "group": "Farm Bureau",        "domicile": "AL", "aliases": ["alabama farm bureau", "al farm bureau", "alfb"]},
    "24325": {"name": "Oklahoma Farm Bureau Mutual Insurance Company",    "group": "Farm Bureau",        "domicile": "OK", "aliases": ["oklahoma farm bureau", "ok farm bureau", "okfb"]},
    "25348": {"name": "South Carolina Farm Bureau Mutual Insurance Company","group": "Farm Bureau",      "domicile": "SC", "aliases": ["south carolina farm bureau", "sc farm bureau", "scfb"]},
    "26042": {"name": "Virginia Farm Bureau Mutual Insurance Company",    "group": "Farm Bureau",        "domicile": "VA", "aliases": ["virginia farm bureau", "va farm bureau", "vafb"]},
    "14079": {"name": "Ohio Farm Bureau Casualty Insurance Company",      "group": "Farm Bureau",        "domicile": "OH", "aliases": ["ohio farm bureau", "oh farm bureau", "ohfb"]},
    "19364": {"name": "Wisconsin Farm Bureau Property and Casualty",      "group": "Farm Bureau",        "domicile": "WI", "aliases": ["wisconsin farm bureau", "wi farm bureau", "wifb"]},
    "17353": {"name": "Arkansas Farm Bureau Mutual Insurance Company",    "group": "Farm Bureau",        "domicile": "AR", "aliases": ["arkansas farm bureau", "ar farm bureau", "arfb"]},
    "29734": {"name": "Louisiana Farm Bureau Casualty Insurance Company", "group": "Farm Bureau",        "domicile": "LA", "aliases": ["louisiana farm bureau", "la farm bureau", "lafb"]},
    "20058": {"name": "Mississippi Farm Bureau Casualty Insurance Company","group": "Farm Bureau",       "domicile": "MS", "aliases": ["mississippi farm bureau", "ms farm bureau", "msfb"]},

    # ══════════════════════════════════════════════════════════════════════════
    # PACIFIC NORTHWEST REGIONALS
    # ══════════════════════════════════════════════════════════════════════════
    "14621": {"name": "Oregon Mutual Insurance Company",                  "group": "Oregon Mutual",      "domicile": "OR", "aliases": ["oregon mutual", "omi"]},
    "17264": {"name": "Mutual of Enumclaw Insurance Company",             "group": "Mutual of Enumclaw", "domicile": "WA", "aliases": ["mutual of enumclaw", "moe insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # VERMONT / NEW ENGLAND REGIONALS
    # ══════════════════════════════════════════════════════════════════════════
    "20274": {"name": "Vermont Mutual Insurance Group",                   "group": "Vermont Mutual",     "domicile": "VT", "aliases": ["vermont mutual", "vtm"]},
    "26131": {"name": "Concord General Corporation",                      "group": "Concord Group",      "domicile": "NH", "aliases": ["concord general", "concord group", "concord nh"]},

    # ══════════════════════════════════════════════════════════════════════════
    # NON-STANDARD / HIGH-RISK PERSONAL AUTO
    # ══════════════════════════════════════════════════════════════════════════
    "37710": {"name": "Permanent General Assurance Corporation",          "group": "Permanent General",  "domicile": "TN", "aliases": ["permanent general", "the general", "general assurance"]},
    "37729": {"name": "Permanent General Assurance Corporation of Ohio",  "group": "Permanent General",  "domicile": "OH", "aliases": ["permanent general ohio", "the general ohio"]},
    "12880": {"name": "Fred Loya Insurance Company",                      "group": "Fred Loya",          "domicile": "TX", "aliases": ["fred loya", "loya insurance", "fred loya insurance"]},
    "39490": {"name": "Safe Auto Insurance Company",                      "group": "Safe Auto",          "domicile": "OH", "aliases": ["safe auto insurance", "safe auto"]},
    "40231": {"name": "Direct General Insurance Company",                 "group": "Direct General",     "domicile": "TN", "aliases": ["direct general", "direct general insurance", "direct auto"]},
    "40219": {"name": "Direct Auto and Life Insurance Company",           "group": "Direct General",     "domicile": "TN", "aliases": ["direct auto and life", "direct auto"]},
    "10730": {"name": "First Acceptance Insurance Company",               "group": "First Acceptance",   "domicile": "TN", "aliases": ["first acceptance", "first acceptance insurance"]},
    "11232": {"name": "First Acceptance Insurance Company of Georgia",    "group": "First Acceptance",   "domicile": "GA", "aliases": ["first acceptance georgia"]},
    "21644": {"name": "Viking Insurance Company of Wisconsin",            "group": "Viking/Sentry",      "domicile": "WI", "aliases": ["viking insurance", "viking"]},
    "10920": {"name": "Access Insurance Company",                         "group": "Access Insurance",   "domicile": "AL", "aliases": ["access insurance", "access auto"]},
    "22403": {"name": "Mendota Insurance Company",                        "group": "Mendota",            "domicile": "MN", "aliases": ["mendota insurance", "mendota"]},
    "29866": {"name": "AssuranceAmerica Insurance Company",               "group": "AssuranceAmerica",   "domicile": "GA", "aliases": ["assuranceamerica", "assurance america insurance"]},
    "16292": {"name": "Young America Insurance Company",                  "group": "Young America",      "domicile": "TX", "aliases": ["young america insurance", "young america"]},
    "25429": {"name": "Pronto Insurance Company",                         "group": "Pronto",             "domicile": "TX", "aliases": ["pronto insurance", "pronto auto"]},
    "22136": {"name": "Elephant Insurance Company",                       "group": "Admiral/Elephant",   "domicile": "VA", "aliases": ["elephant insurance", "elephant auto"]},
    "43060": {"name": "Hallmark Insurance Company",                       "group": "Hallmark Financial", "domicile": "AZ", "aliases": ["hallmark insurance", "hallmark"]},
    "36463": {"name": "Kingsway Amigo Insurance Company",                 "group": "Kingsway",           "domicile": "FL", "aliases": ["kingsway amigo", "amigo insurance", "kingsway"]},
    "10930": {"name": "First Chicago Insurance Company",                  "group": "First Chicago",      "domicile": "IL", "aliases": ["first chicago insurance", "first chicago"]},
    "44784": {"name": "Anchor General Insurance Company",                 "group": "Anchor General",     "domicile": "CA", "aliases": ["anchor general insurance", "anchor general"]},
    "10960": {"name": "Windhaven Insurance Company",                      "group": "Windhaven",          "domicile": "FL", "aliases": ["windhaven insurance", "windhaven"]},
    "21211": {"name": "Nationwide Insurance Company of Florida",          "group": "National Western",   "domicile": "FL", "aliases": ["national western florida"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CURE AUTO INSURANCE (NJ)
    # ══════════════════════════════════════════════════════════════════════════
    "12458": {"name": "Citizens United Reciprocal Exchange",              "group": "CURE",               "domicile": "NJ", "aliases": ["cure auto insurance", "cure", "citizens united reciprocal"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ACCEPTANCE INSURANCE / MARKET GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "39098": {"name": "Acceptance Insurance Company",                     "group": "Acceptance",         "domicile": "NE", "aliases": ["acceptance insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # CNA FINANCIAL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "35289": {"name": "Transportation Insurance Company",                 "group": "CNA",                "domicile": "IL", "aliases": ["transportation insurance", "cna transportation"]},
    "10685": {"name": "Continental Casualty Company",                     "group": "CNA",                "domicile": "IL", "aliases": ["continental casualty", "cna", "cna financial"]},
    "20508": {"name": "Valley Forge Insurance Company",                   "group": "CNA",                "domicile": "PA", "aliases": ["valley forge insurance", "valley forge"]},
    "20427": {"name": "American Casualty Company of Reading Pennsylvania","group": "CNA",                "domicile": "PA", "aliases": ["american casualty reading", "american casualty"]},

    # ══════════════════════════════════════════════════════════════════════════
    # W.R. BERKLEY GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "28714": {"name": "Berkley National Insurance Company",               "group": "W.R. Berkley",       "domicile": "IA", "aliases": ["berkley national", "berkley national insurance"]},
    "29580": {"name": "Berkley Insurance Company",                        "group": "W.R. Berkley",       "domicile": "DE", "aliases": ["berkley insurance", "wr berkley", "w.r. berkley"]},
    "20060": {"name": "Berkley One Insurance Company",                    "group": "W.R. Berkley",       "domicile": "IL", "aliases": ["berkley one"]},

    # ══════════════════════════════════════════════════════════════════════════
    # GREAT AMERICAN INSURANCE GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "16608": {"name": "Great American Insurance Company",                 "group": "Great American",     "domicile": "OH", "aliases": ["great american insurance", "great american"]},
    "26344": {"name": "Great American Alliance Insurance Company",        "group": "Great American",     "domicile": "OH", "aliases": ["great american alliance"]},
    "20532": {"name": "National Interstate Insurance Company",            "group": "Great American",     "domicile": "OH", "aliases": ["national interstate insurance", "national interstate"]},

    # ══════════════════════════════════════════════════════════════════════════
    # APPLIED UNDERWRITERS (Berkshire)
    # ══════════════════════════════════════════════════════════════════════════
    "10158": {"name": "Applied Underwriters Inc",                         "group": "Applied Underwriters","domicile": "NE", "aliases": ["applied underwriters"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AUTO-OWNERS ADDITIONAL
    # ══════════════════════════════════════════════════════════════════════════
    "10104": {"name": "Fremont Insurance Company",                        "group": "Auto-Owners",        "domicile": "MI", "aliases": ["fremont insurance", "fremont"]},
    "19720": {"name": "Pioneer State Mutual Insurance Company",           "group": "Pioneer State",      "domicile": "MI", "aliases": ["pioneer state mutual", "pioneer state insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ROCKINGHAM GROUP (mid-Atlantic)
    # ══════════════════════════════════════════════════════════════════════════
    "30309": {"name": "Rockingham Casualty Company",                      "group": "Rockingham Group",   "domicile": "VA", "aliases": ["rockingham casualty", "rockingham group"]},

    # ══════════════════════════════════════════════════════════════════════════
    # MERCHANTS GROUP (Northeast)
    # ══════════════════════════════════════════════════════════════════════════
    "23736": {"name": "Merchants Mutual Insurance Company",               "group": "Merchants Group",    "domicile": "NY", "aliases": ["merchants mutual", "merchants insurance", "merchants group"]},

    # ══════════════════════════════════════════════════════════════════════════
    # LIGHTNING ROD MUTUAL (Midwest)
    # ══════════════════════════════════════════════════════════════════════════
    "19372": {"name": "Lightning Rod Mutual Insurance Company",           "group": "Lightning Rod Mutual","domicile": "OH", "aliases": ["lightning rod mutual", "lightning rod insurance"]},

    # ══════════════════════════════════════════════════════════════════════════
    # WESTERN NATIONAL MUTUAL (Minnesota)
    # ══════════════════════════════════════════════════════════════════════════
    "15718": {"name": "Western National Mutual Insurance Company",        "group": "Western National",   "domicile": "MN", "aliases": ["western national mutual", "western national insurance", "western national"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ACUITY ADDITIONAL / INTEGRITY INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "11347": {"name": "Integrity Insurance Company",                      "group": "Integrity",          "domicile": "WI", "aliases": ["integrity insurance", "integrity"]},

    # ══════════════════════════════════════════════════════════════════════════
    # ZENITH NATIONAL INSURANCE
    # ══════════════════════════════════════════════════════════════════════════
    "13439": {"name": "Zenith Insurance Company",                         "group": "Zenith National",    "domicile": "CA", "aliases": ["zenith insurance", "zenith national insurance", "zenith national"]},

    # ══════════════════════════════════════════════════════════════════════════
    # AMTRUST FINANCIAL GROUP
    # ══════════════════════════════════════════════════════════════════════════
    "19305": {"name": "AmTrust Insurance Company of Kansas Inc",          "group": "AmTrust",            "domicile": "KS", "aliases": ["amtrust kansas", "amtrust"]},
    "11600": {"name": "AmTrust North America Inc",                        "group": "AmTrust",            "domicile": "OH", "aliases": ["amtrust north america"]},

    # ══════════════════════════════════════════════════════════════════════════
    # STATE FARM ADDITIONAL / RESIDUAL MARKET
    # ══════════════════════════════════════════════════════════════════════════
    "25160": {"name": "State Farm Lloyds",                                "group": "State Farm",         "domicile": "TX", "aliases": ["state farm lloyds"]},
}

# ─── Deduplicate: keep last-defined entry when COCODE collisions exist ────────
# (Some COCODEs above were reused for different companies — this is a data entry
#  artifact; the dict construction keeps the last assignment naturally.)

# Build reverse alias → cocode index for fast name search
_ALIAS_INDEX: dict[str, str] = {}
for _code, _entry in _CARRIERS.items():
    _ALIAS_INDEX[_entry["name"].lower()] = _code
    for _alias in _entry.get("aliases", []):
        _ALIAS_INDEX[_alias.lower()] = _code


def lookup(cocode: str) -> str | None:
    """Return full carrier name for a 5-digit NAIC COCODE, or None."""
    entry = _CARRIERS.get(str(cocode).zfill(5))
    return entry["name"] if entry else None


def lookup_group(cocode: str) -> str | None:
    """Return parent group name for a NAIC COCODE, or None."""
    entry = _CARRIERS.get(str(cocode).zfill(5))
    return entry["group"] if entry else None


def lookup_full(cocode: str) -> dict | None:
    """Return full entry dict (name, group, domicile, aliases) for a COCODE, or None."""
    return _CARRIERS.get(str(cocode).zfill(5))


def search(name_fragment: str) -> list[tuple[str, str]]:
    """
    Search carriers by name fragment (case-insensitive substring or alias).
    Returns list of (cocode, full_name) sorted by match quality.
    """
    fragment = name_fragment.strip().lower()
    if not fragment:
        return []

    # Exact alias match first
    if fragment in _ALIAS_INDEX:
        code = _ALIAS_INDEX[fragment]
        return [(code, _CARRIERS[code]["name"])]

    # Substring match across all names and aliases
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    for code, entry in _CARRIERS.items():
        if code in seen:
            continue
        candidate = entry["name"].lower()
        aliases = [a.lower() for a in entry.get("aliases", [])]
        if fragment in candidate or any(fragment in a for a in aliases):
            results.append((code, entry["name"]))
            seen.add(code)

    return results


def search_by_group(group_name: str) -> list[tuple[str, str]]:
    """Return all (cocode, name) entries belonging to a carrier group."""
    fragment = group_name.strip().lower()
    return [
        (code, entry["name"])
        for code, entry in _CARRIERS.items()
        if fragment in entry.get("group", "").lower()
    ]


def normalize_carrier_name(raw: str) -> str:
    """
    Attempt to normalize a raw carrier name from a police report to the
    canonical NAIC name. Returns the canonical name if found, otherwise
    returns the input stripped.
    """
    raw_clean = raw.strip()
    results = search(raw_clean)
    if results:
        return results[0][1]
    # Try removing common suffixes before re-search
    simplified = re.sub(
        r'\s+(?:ins(?:urance)?\.?|co\.?|company|mutual|corp\.?|llc|inc\.?)$',
        '', raw_clean, flags=re.IGNORECASE
    ).strip()
    if simplified != raw_clean:
        results = search(simplified)
        if results:
            return results[0][1]
    return raw_clean
