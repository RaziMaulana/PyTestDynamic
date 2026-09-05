from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Inisialisasi engine NLP
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def mask_sensitive_data(text: str) -> str:
    """Mendeteksi dan menyensor data pribadi (PII) sebelum dikirim ke LLM."""
    if not text.strip():
        return text
        
    results = analyzer.analyze(text=text, entities=[], language='en')
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    
    return anonymized_result.text