def normalize_score(country: str, overall_rating: int | None = None, raw_rating_label: str | None = None) -> float | None:
    """Normalize hosp rating 0-100 scale for cross-border comparison"""
    if country == "US":
        if overall_rating is None:
            return None
        return round((overall_rating / 5) * 100, 1)
    
    elif country == "GB":
        if raw_rating_label is None:
            return None
        mapping = {
            "outstanding": 100.0,
            "good": 75.0,
            "requires improvement": 40.0,
            "inadequate": 10.0,
        }
        return mapping.get(raw_rating_label.lower())
    
    elif country == "FR":
        if raw_rating_label is None:
            return None
        mapping = {
            "certification": 100.0,
            "avec recommandations": 60.0,
            "non-certification": 10.0,
        }
        return mapping.get(raw_rating_label.lower())
    
    elif country == "BR":
        #DATASUS CNES has no single national rating
        return None
    
    elif country == "BE":
        if raw_rating_label is None:
            return None
        return 100.0 if raw_rating_label.lower() == "accredited" else 50.0
    
    elif country == "IT":
        #ISTAT data is by region, not by hospital
        return None
    
    return None

def get_rating_systems(country: str) -> str:
    systems = {
        "US": "CMS Star Rating (1-5 stars)",
        "GB": "CQC (Outstanding / Good / Requires Improvement / Inadequate)",
        "FR": "HAS Certification",
        "BR": "CNES — structural data only",
        "BE": "SPF Santé publique accreditation",
        "IT": "SSN / ISTAT regional data",
    }
    return systems.get(country, "Unknown")

COUNTRY_LABELS = {
    "US": {
        "flag": "🇺🇸",
        "name": "United States",
        "source": "CMS (Centers for Medicare & Medicaid Services)",
        "description": "5,419 hospitals · Public health data · Updated annually",
        "rating_info": "Rating: 1–5 stars based on 46 quality indicators. Higher = better quality care.",
    },
    "BR": {
        "flag": "🇧🇷",
        "name": "Brasil",
        "source": "DATASUS / Ministério da Saúde",
        "description": "7,000+ hospitais · Sistema Único de Saúde (SUS)",
        "rating_info": "Sem rating nacional único — dados estruturais: leitos, especialidades, equipamentos. Fonte: CNES.",
    },
    "GB": {
        "flag": "🇬🇧",
        "name": "United Kingdom",
        "source": "NHS / CQC (Care Quality Commission)",
        "description": "1,200+ hospitals · National Health Service",
        "rating_info": "Rating: Outstanding / Good / Requires Improvement / Inadequate. Assessed on: Safe · Effective · Caring · Responsive · Well-led.",
    },
    "FR": {
        "flag": "🇫🇷",
        "name": "France",
        "source": "HAS (Haute Autorité de Santé)",
        "description": "3,000+ hôpitaux · Système de santé français",
        "rating_info": "Certification / Avec recommandations / Non-certification. Données via data.gouv.fr.",
    },
    "IT": {
        "flag": "🇮🇹",
        "name": "Italia",
        "source": "SSN (Servizio Sanitario Nazionale) / ISTAT",
        "description": "1,000+ ospedali · Sistema sanitario regionale",
        "rating_info": "Dati aggregati per regione — dettaglio individuale limitato.",
    },
    "BE": {
        "flag": "🇧🇪",
        "name": "Belgique / België",
        "source": "SPF Santé publique / data.gov.be",
        "description": "160 hôpitaux · Service public fédéral",
        "rating_info": "101 hôpitaux généraux + 59 psychiatriques. Système d'accréditation fédérale.",
    },
}

def get_country_label(country: str) -> dict:
    return COUNTRY_LABELS.get(country, {"flag": "🌍", "name": country, "source": "Unknown", "description": "", "rating_info": ""})