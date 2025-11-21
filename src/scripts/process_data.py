from src.model import nlp_utils
import spacy
import os

def process_sentences(sentences, pictograms, nlp_model):
    """Processes the sentences and maps words to pictograms."""
    processed_sentences = []
    for sentence in sentences:
        doc = nlp_model(sentence)
        processed_sentence = []
        for token in doc:
            pictogram = nlp_utils.find_pictogram(token.text, pictograms)
            processed_sentence.append({
                'word': token.text,
                'pictogram': pictogram
            })
        processed_sentences.append(processed_sentence)
    return processed_sentences

if __name__ == '__main__':
    # Load the spaCy model
    nlp = spacy.load("es_core_news_sm")
    
    # Construct the absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, '../../data/raw/arasaac_pictograms_es.json')
    images_dir = os.path.join(script_dir, '../../data/raw/ARASAAC_ES')
    
    # Load the pictograms
    pictograms = nlp_utils.load_pictograms(json_path, images_dir)

    # Create a dummy dataset of sentences
    dummy_sentences = [
        "El perro come la comida",
        "La niña juega con la pelota",
        "Yo quiero agua",
        "El sol es amarillo"
    ]

    # Process the sentences
    processed_sentences = process_sentences(dummy_sentences, pictograms, nlp)

    # Print the results
    for sentence in processed_sentences:
        for word_data in sentence:
            print(f"Word: {word_data['word']}")
            if word_data['pictogram']:
                print(f"  Pictogram Path: {word_data['pictogram']['path']}")
            else:
                print("  Pictogram not found")
        print("---")
