"""JAI - Advanced NLP (Lightweight Version)
No spaCy required — returns empty results gracefully.
"""

class JAIAdvancedNLP:
    """Lightweight NLP placeholder — no external dependencies"""
    
    @staticmethod
    def full_analysis(text):
        """Return empty analysis (spaCy disabled)"""
        return {
            "dependencies": {
                "subjects": [],
                "verbs": [],
                "objects": [],
                "prepositions": [],
                "has_subject": False,
                "has_verb": False,
                "has_object": False
            },
            "coreference": {
                "pronouns": [],
                "has_pronouns": False
            },
            "prepositions": {
                "phrases": [],
                "location_phrases": [],
                "time_phrases": [],
                "has_location": False,
                "has_time": False
            }
        }