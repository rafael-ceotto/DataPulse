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
    
    elif country in ("BR", "BE", "CA", "AU", "DE", "MT", "PT", "ES", "IT"):
        return None
    
    return None


def get_rating_systems(country: str) -> str:
    systems = {
        "US": "CMS Star Rating (1-5 stars)",
        "GB": "CQC Rating System",
        "FR": "HAS Certification",
        "BR": "CNES — structural data only",
        "BE": "SPF Santé publique accreditation",
        "IT": "SSN / ISTAT regional data",
        "CA": "CIHI (Canadian Institute for Health Information)",
        "AU": "ACSQHC — structural data only",
        "DE": "Qualitätsbericht — structural data only",
        "MT": "Malta Health — structural data only",
        "PT": "SNS — structural data only",
        "ES": "SNS España — structural data only",
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
        "description": "7,680 hospitais · Sistema Único de Saúde (SUS)",
        "rating_info": "Sem rating nacional único — dados estruturais: leitos, especialidades, equipamentos. Fonte: CNES.",
    },
    "GB": {
        "flag": "🇬🇧",
        "name": "United Kingdom",
        "source": "NHS / CQC (Care Quality Commission)",
        "description": "247 NHS Trusts · National Health Service · England",
        "rating_info": "Rating: Outstanding / Good / Requires Improvement / Inadequate. Assessed on: Safe · Effective · Caring · Responsive · Well-led.",
    },
    "FR": {
        "flag": "🇫🇷",
        "name": "France",
        "source": "FINESS / Ministère de la Santé",
        "description": "3,360 hôpitaux · Système de santé français",
        "rating_info": "Certification HAS (Haute Autorité de Santé) — données structurelles FINESS.",
    },
    "BE": {
        "flag": "🇧🇪",
        "name": "Belgique / België",
        "source": "Wikidata / SPF Santé publique",
        "description": "111 hôpitaux · Royaume de Belgique",
        "rating_info": "Agrément SPF Santé publique — données structurelles Wikidata.",
    },
    "IT": {
        "flag": "🇮🇹",
        "name": "Italia",
        "source": "SSN (Servizio Sanitario Nazionale) / ISTAT",
        "description": "1,000+ ospedali · Sistema sanitario regionale",
        "rating_info": "Dati aggregati per regione — dettaglio individuale limitato.",
    },
    "CA": {
        "flag": "🇨🇦",
        "name": "Canada",
        "source": "Wikidata / CIHI",
        "description": "432 hospitals · Canadian health system",
        "rating_info": "No single national rating — structural data from Wikidata.",
    },
    "AU": {
        "flag": "🇦🇺",
        "name": "Australia",
        "source": "ACSQHC / MyHospitals",
        "description": "1,300+ hospitals · Australian health system",
        "rating_info": "Australian Commission on Safety and Quality in Health Care.",
    },
    "DE": {
        "flag": "🇩🇪",
        "name": "Deutschland",
        "source": "Qualitätsbericht / GBE-Bund",
        "description": "1,900+ Krankenhäuser · Deutsches Gesundheitssystem",
        "rating_info": "Qualitätsbericht — mandatory quality report per hospital.",
    },
    "MT": {
        "flag": "🇲🇹",
        "name": "Malta",
        "source": "Malta Health / Wikidata",
        "description": "10+ hospitals · Maltese health system",
        "rating_info": "Structural data only.",
    },
    "PT": {
        "flag": "🇵🇹",
        "name": "Portugal",
        "source": "SNS (Serviço Nacional de Saúde)",
        "description": "200+ hospitais · Sistema Nacional de Saúde",
        "rating_info": "Dados estruturais SNS — portal transparência.sns.gov.pt.",
    },
    "ES": {
        "flag": "🇪🇸",
        "name": "España",
        "source": "SNS (Sistema Nacional de Salud)",
        "description": "800+ hospitales · Sistema Nacional de Salud",
        "rating_info": "Datos estructurales — Ministerio de Sanidad.",
    },
}

def get_country_label(country: str) -> dict:
    return COUNTRY_LABELS.get(country, {"flag": "🌍", "name": country, "source": "Unknown", "description": "", "rating_info": ""})