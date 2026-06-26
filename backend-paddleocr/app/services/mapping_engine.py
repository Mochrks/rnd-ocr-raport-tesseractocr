from thefuzz import process
from typing import List, Optional, Dict
import re

def get_best_match(raw_name: str, master_subjects: List[Dict], threshold: int = 65) -> Optional[Dict]:
    """
    Find the best matching MasterSubject for a given raw string.
    Checks for exact substring/word matches first, then falls back to fuzzy matching.
    Threshold lowered to 65 for PaddleOCR since handwritten text may have more variation.
    """
    if not master_subjects:
        return None
        
    raw_lower = raw_name.lower().strip()
    raw_words = set(re.findall(r'\w+', raw_lower))
    
    # Skip very short or garbage strings
    if len(raw_lower) < 2:
        return None
    
    # 1. Exact Word / Substring Matches Priority
    for ms in master_subjects:
        subj_name = ms["subject_name"].lower()
        if subj_name in raw_lower:
            return ms
            
        for alias in ms.get("aliases", []):
            alias_lower = alias.lower()
            # For short acronyms (like PKN, IPA, IPS, TIK), require an exact word match
            if len(alias_lower) <= 4:
                if alias_lower in raw_words:
                    return ms
            else:
                if alias_lower in raw_lower:
                    return ms
                    
    # 2. Fuzzy Match Fallback
    choices = {}
    for ms in master_subjects:
        choices[ms["subject_name"].lower()] = ms
        for alias in ms.get("aliases", []):
            choices[alias.lower()] = ms
            
    result = process.extractOne(raw_lower, list(choices.keys()))
    
    if result:
        match_str, score = result
        if score >= threshold:
            return choices[match_str]
            
    return None
