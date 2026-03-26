"""JAI - Advanced NLP
Dependency parsing and prepositional phrase understanding.
Uses pre-downloaded spaCy model from requirements.txt.
"""

import spacy
import re

# Load spaCy model (pre-downloaded via requirements.txt)
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ Advanced NLP loaded")
except OSError:
    print("⚠️ spaCy model not found. Advanced NLP disabled.")
    nlp = None

class JAIAdvancedNLP:
    """Advanced language understanding for JAI"""
    
    PREPOSITION_MEANINGS = {
        "in": {"type": "location", "meaning": "inside or within"},
        "on": {"type": "location", "meaning": "on top of or surface"},
        "at": {"type": "location", "meaning": "specific point or location"},
        "for": {"type": "purpose", "meaning": "intended for or on behalf of"},
        "to": {"type": "direction", "meaning": "towards or indicating recipient"},
        "from": {"type": "source", "meaning": "originating from"},
        "with": {"type": "accompaniment", "meaning": "together with"},
        "about": {"type": "topic", "meaning": "concerning or regarding"},
        "during": {"type": "time", "meaning": "throughout the duration of"},
        "before": {"type": "time", "meaning": "earlier than"},
        "after": {"type": "time", "meaning": "later than"},
        "under": {"type": "location", "meaning": "beneath or below"},
        "over": {"type": "location", "meaning": "above or covering"},
        "near": {"type": "location", "meaning": "close to"},
        "beside": {"type": "location", "meaning": "next to"},
        "behind": {"type": "location", "meaning": "at the back of"}
    }
    
    @staticmethod
    def parse_dependencies(text):
        """Parse sentence dependencies (who did what to whom)"""
        if nlp is None:
            return {"subjects": [], "verbs": [], "objects": [], "prepositions": [], 
                    "has_subject": False, "has_verb": False, "has_object": False}
        
        doc = nlp(text)
        
        subjects = []
        objects = []
        verbs = []
        prepositions = []
        
        for token in doc:
            if token.dep_ in ["nsubj", "nsubjpass"]:
                subjects.append({"word": token.text, "lemma": token.lemma_, "pos": token.pos_})
            
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                verbs.append({"word": token.text, "lemma": token.lemma_})
            
            if token.dep_ in ["dobj", "iobj"]:
                objects.append({"word": token.text, "lemma": token.lemma_, "pos": token.pos_})
            
            if token.pos_ == "ADP":
                prep_info = JAIAdvancedNLP.PREPOSITION_MEANINGS.get(token.text.lower(), 
                    {"type": "unknown", "meaning": "unknown"})
                prepositions.append({
                    "word": token.text,
                    "type": prep_info["type"],
                    "meaning": prep_info["meaning"]
                })
        
        return {
            "subjects": subjects,
            "verbs": verbs,
            "objects": objects,
            "prepositions": prepositions,
            "has_subject": len(subjects) > 0,
            "has_verb": len(verbs) > 0,
            "has_object": len(objects) > 0
        }
    
    @staticmethod
    def resolve_coreference(text):
        """Resolve pronouns to their referents"""
        if nlp is None:
            return {"pronouns": [], "has_pronouns": False}
        
        doc = nlp(text)
        pronouns = []
        
        for token in doc:
            if token.pos_ == "PRON":
                prev_noun = None
                for prev_token in doc[:token.i]:
                    if prev_token.pos_ in ["NOUN", "PROPN"]:
                        prev_noun = prev_token.text
                        break
                pronouns.append({
                    "pronoun": token.text,
                    "likely_referent": prev_noun
                })
        
        return {"pronouns": pronouns, "has_pronouns": len(pronouns) > 0}
    
    @staticmethod
    def understand_prepositional_phrases(text):
        """Extract and understand prepositional phrases"""
        if nlp is None:
            return {"phrases": [], "location_phrases": [], "time_phrases": [], 
                    "has_location": False, "has_time": False}
        
        doc = nlp(text)
        phrases = []
        
        for token in doc:
            if token.pos_ == "ADP":
                phrase_end = token.i + 1
                for child in token.children:
                    if child.dep_ == "pobj":
                        phrase_end = child.i + 1
                        break
                phrase_text = doc[token.i:phrase_end].text
                prep_info = JAIAdvancedNLP.PREPOSITION_MEANINGS.get(token.text.lower(), 
                    {"type": "unknown", "meaning": "unknown"})
                phrases.append({
                    "preposition": token.text,
                    "phrase": phrase_text,
                    "type": prep_info["type"],
                    "meaning": prep_info["meaning"]
                })
        
        return {
            "phrases": phrases,
            "location_phrases": [p for p in phrases if p["type"] == "location"],
            "time_phrases": [p for p in phrases if p["type"] == "time"],
            "has_location": any(p["type"] == "location" for p in phrases),
            "has_time": any(p["type"] == "time" for p in phrases)
        }
    
    @staticmethod
    def full_analysis(text):
        """Complete language analysis"""
        return {
            "dependencies": JAIAdvancedNLP.parse_dependencies(text),
            "coreference": JAIAdvancedNLP.resolve_coreference(text),
            "prepositions": JAIAdvancedNLP.understand_prepositional_phrases(text)
        }