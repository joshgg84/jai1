"""JAI - Advanced NLP
Dependency parsing, coreference resolution, and prepositional phrase understanding.
Requires: pip install spacy spacy-transformers
"""

import spacy
import re
from collections import defaultdict

# Load spaCy model (download first time)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class JAIAdvancedNLP:
    """Advanced language understanding for JAI"""
    
    # Preposition meanings
    PREPOSITION_MEANINGS = {
        "in": {"type": "location", "meaning": "inside or within"},
        "on": {"type": "location", "meaning": "on top of or surface"},
        "at": {"type": "location", "meaning": "specific point or location"},
        "for": {"type": "purpose", "meaning": "intended for or on behalf of"},
        "to": {"type": "direction", "meaning": "towards or indicating recipient"},
        "from": {"type": "source", "meaning": "originating from"},
        "with": {"type": "accompaniment", "meaning": "together with"},
        "by": {"type": "agent", "meaning": "through the action of"},
        "about": {"type": "topic", "meaning": "concerning or regarding"},
        "during": {"type": "time", "meaning": "throughout the duration of"},
        "before": {"type": "time", "meaning": "earlier than"},
        "after": {"type": "time", "meaning": "later than"},
        "under": {"type": "location", "meaning": "beneath or below"},
        "over": {"type": "location", "meaning": "above or covering"},
        "between": {"type": "location", "meaning": "in the space separating"},
        "among": {"type": "location", "meaning": "surrounded by"},
        "through": {"type": "movement", "meaning": "moving in one side and out the other"},
        "across": {"type": "movement", "meaning": "from one side to the other"},
        "around": {"type": "location", "meaning": "surrounding or approximately"},
        "near": {"type": "location", "meaning": "close to"},
        "beside": {"type": "location", "meaning": "next to"},
        "behind": {"type": "location", "meaning": "at the back of"},
        "in front of": {"type": "location", "meaning": "before or ahead of"}
    }
    
    @staticmethod
    def parse_dependencies(text):
        """Parse sentence dependencies (who did what to whom)"""
        doc = nlp(text)
        
        # Extract subject-verb-object relationships
        subjects = []
        objects = []
        verbs = []
        prepositions = []
        
        for token in doc:
            # Subjects (nsubj)
            if token.dep_ == "nsubj" or token.dep_ == "nsubjpass":
                subjects.append({
                    "word": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_
                })
            
            # Verbs (ROOT)
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                verbs.append({
                    "word": token.text,
                    "lemma": token.lemma_,
                    "tense": token.morph.get("Tense", ["unknown"])[0] if token.morph else "unknown"
                })
            
            # Objects (dobj, iobj)
            if token.dep_ == "dobj" or token.dep_ == "iobj":
                objects.append({
                    "word": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_
                })
            
            # Prepositions
            if token.pos_ == "ADP":
                prep_info = JAIAdvancedNLP.PREPOSITION_MEANINGS.get(token.text.lower(), 
                    {"type": "unknown", "meaning": "unknown"})
                prepositions.append({
                    "word": token.text,
                    "type": prep_info["type"],
                    "meaning": prep_info["meaning"],
                    "object": token.head.text if token.head else None
                })
        
        return {
            "subjects": subjects,
            "verbs": verbs,
            "objects": objects,
            "prepositions": prepositions,
            "has_subject": len(subjects) > 0,
            "has_verb": len(verbs) > 0,
            "has_object": len(objects) > 0,
            "sentence_structure": "subject-verb-object" if subjects and verbs and objects else "incomplete"
        }
    
    @staticmethod
    def resolve_coreference(text):
        """Resolve pronouns to their referents (he/she/it/they → actual nouns)"""
        doc = nlp(text)
        
        coref_map = {}
        pronouns = []
        
        # Simple coreference resolution (can be enhanced with neural coref)
        for token in doc:
            if token.pos_ == "PRON":
                # Try to find previous noun phrase
                prev_noun = None
                for prev_token in doc[:token.i]:
                    if prev_token.pos_ in ["NOUN", "PROPN"]:
                        prev_noun = prev_token.text
                        break
                
                pronouns.append({
                    "pronoun": token.text,
                    "lemma": token.lemma_,
                    "likely_referent": prev_noun,
                    "person": token.morph.get("Person", ["unknown"])[0] if token.morph else "unknown",
                    "number": token.morph.get("Number", ["unknown"])[0] if token.morph else "unknown"
                })
                
                if prev_noun:
                    coref_map[token.text] = prev_noun
        
        return {
            "pronouns": pronouns,
            "coreference_map": coref_map,
            "has_pronouns": len(pronouns) > 0
        }
    
    @staticmethod
    def understand_prepositional_phrases(text):
        """Extract and understand prepositional phrases (location, time, purpose)"""
        doc = nlp(text)
        
        phrases = []
        
        for token in doc:
            if token.pos_ == "ADP":
                # Get the prepositional phrase
                phrase_start = token.i
                phrase_end = token.i + 1
                
                # Find the object of preposition
                for child in token.children:
                    if child.dep_ == "pobj":
                        phrase_end = child.i + 1
                        # Also include any adjectives before the object
                        for adj in child.lefts:
                            if adj.dep_ == "amod":
                                phrase_start = min(phrase_start, adj.i)
                
                phrase_text = doc[phrase_start:phrase_end].text
                prep_info = JAIAdvancedNLP.PREPOSITION_MEANINGS.get(token.text.lower(), 
                    {"type": "unknown", "meaning": "unknown"})
                
                phrases.append({
                    "preposition": token.text,
                    "phrase": phrase_text,
                    "type": prep_info["type"],
                    "meaning": prep_info["meaning"],
                    "object": token.head.text if token.head else None
                })
        
        return {
            "phrases": phrases,
            "location_phrases": [p for p in phrases if p["type"] == "location"],
            "time_phrases": [p for p in phrases if p["type"] == "time"],
            "purpose_phrases": [p for p in phrases if p["type"] == "purpose"],
            "movement_phrases": [p for p in phrases if p["type"] == "movement"],
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
    
    @staticmethod
    def generate_smart_response(text, context=""):
        """Generate a response based on advanced understanding"""
        analysis = JAIAdvancedNLP.full_analysis(text)
        deps = analysis["dependencies"]
        coref = analysis["coreference"]
        prep = analysis["prepositions"]
        
        # If we detected a clear subject-verb-object structure
        if deps["has_subject"] and deps["has_verb"] and deps["has_object"]:
            subject = deps["subjects"][0]["word"] if deps["subjects"] else "someone"
            verb = deps["verbs"][0]["word"] if deps["verbs"] else "did"
            obj = deps["objects"][0]["word"] if deps["objects"] else "something"
            
            # Check if it's a question
            if text.strip().endswith("?"):
                return f"You're asking about {subject} {verb}ing {obj}. That's interesting. What makes you curious about that?"
            else:
                return f"So {subject} {verb} {obj}. Tell me more about that."
        
        # If we detected location
        if prep["has_location"]:
            location = prep["location_phrases"][0]["phrase"] if prep["location_phrases"] else "there"
            return f"I see you mentioned {location}. How is it there? Tell me about your experience."
        
        # If we detected time
        if prep["has_time"]:
            time_phrase = prep["time_phrases"][0]["phrase"] if prep["time_phrases"] else "then"
            return f"You mentioned {time_phrase}. What happens at that time?"
        
        # If pronouns detected, resolve them
        if coref["has_pronouns"]:
            for p in coref["pronouns"]:
                if p["likely_referent"]:
                    return f"When you said '{p['pronoun']}', were you referring to {p['likely_referent']}? Tell me more about {p['likely_referent']}."
        
        return None