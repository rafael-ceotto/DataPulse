function stripAccents(text){
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

// Keywords checked as whole words, case/accent-insensitive. Short countries(usa, uk) code-like words = safe due to \b word boundaries
// e.g. "usa" won't match inside words that follow this sequence, as well any other short countries code-like words

const COUNTRY_KEYWORDS = {
  US: ["united states", "usa", "eua", "estados unidos", "etats-unis", "stati uniti"],
  BR: ["brazil", "brasil"],
  CA: ["canada"],
  GB: ["united kingdom", "uk", "reino unido", "royaume-uni", "regno unito", "england", "inglaterra", "angleterre", "inghilterra", "great britain", "gra-bretanha"],
  FR: ["france", "franca", "francia"],
  BE: ["belgium", "belgica", "belgique", "belgio"],
  PT: ["portugal"],
  ES: ["spain", "espana", "espanha", "espagne", "spagna"],
  IT: ["italy", "italia", "italie"],
  MT: ["malta"],
};

// Return country code in text if it's different from currentCountry | Null if no other country is mentioned
export function detectMentionedCountry(text, currentCountry){
    const normalized = stripAccents(text.toLowerCase());
    for (const [code, keywords] of Object.entries(COUNTRY_KEYWORDS)){
        if (code === currentCountry) continue;
        for (const kw of keywords){
            const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            const pattern = new RegExp(`\\b${escaped}\\b`, "i");
            if (pattern.test(normalized)) return code;
        }
    }
    return null;
}

export const COUNTRY_LABELS = {
    US: "United States", BR: "Brasil", CA: "Canada", GB: "United Kingdom",
    FR: "France", BE: "Belgium", PT: "Portugal", ES: "España", IT: "Italia", MT: "Malta",
};