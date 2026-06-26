from thefuzz import process, fuzz
from typing import List, Optional, Dict
import re

def get_best_match(raw_name: str, master_subjects: List[Dict], threshold: int = 80) -> Optional[Dict]:
    """
    Find the best matching MasterSubject for a given raw string.
    Checks for exact substring/word matches first, then falls back to fuzzy matching.
    """
    if not master_subjects:
        return None
        
    raw_lower = raw_name.lower()
    raw_words = set(re.findall(r'\w+', raw_lower))
    
    # 1. Exact Word Match Priority for Short Acronyms
    for ms in master_subjects:
        for alias in ms.get("aliases", []):
            alias_lower = alias.lower()
            if len(alias_lower) <= 4:
                if alias_lower in raw_words:
                    return ms
                    
    # 2. Fuzzy Match Fallback
    choices = {}
    for ms in master_subjects:
        choices[ms["subject_name"].lower()] = ms
        for alias in ms.get("aliases", []):
            choices[alias.lower()] = ms
            
    # Try token_sort_ratio first (handles out of order words like "Sejarah Islam Kebudayaan" -> "Sejarah Kebudayaan Islam")
    result_sort = process.extractOne(raw_lower, list(choices.keys()), scorer=fuzz.token_sort_ratio)
    if result_sort and result_sort[1] >= 85:
        return choices[result_sort[0]]
        
    # Try WRatio for cases where raw string has extra words (like "Pendidikan Agama Islam dan Budi Pekerti" -> "Pendidikan Agama Islam")
    result_w = process.extractOne(raw_lower, list(choices.keys()))
    if result_w and result_w[1] >= threshold:
        match_str = result_w[0]
        # Prevent WRatio from matching short acronyms inside other words (e.g. "praktik" matching "tik")
        if len(match_str) > 4:
            return choices[match_str]
            
    return None
