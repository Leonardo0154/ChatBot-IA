import json
import random

def generate_data():
    """
    Generates a synthetic dataset for fine-tuning a small language model.
    The dataset is based on the keywords from the ARASAAC pictograms.
    """
    pictograms_file = 'data/raw/arasaac_pictograms_es.json'
    output_file = 'data/processed/finetuning_data.jsonl'

    try:
        with open(pictograms_file, 'r', encoding='utf-8') as f:
            pictograms = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {pictograms_file} was not found.")
        return

    keywords = []
    for pictogram in pictograms:
        for keyword_obj in pictogram.get('keywords', []):
            keywords.append(keyword_obj['keyword'])
    
    keywords = list(set(keywords)) # Get unique keywords

    question_templates = [
        "What is a {keyword}?",
        "Can you tell me about {keyword}?",
        "I want to know more about {keyword}.",
        "Explain {keyword} to me."
    ]

    sentence_templates = [
        "I see a {keyword}.",
        "This is a {keyword}.",
        "Let's play with the {keyword}.",
        "The {keyword} is big.",
        "The {keyword} is small."
    ]

    dataset = []
    for i in range(500): # Generate 500 examples
        keyword = random.choice(keywords)
        
        if i % 2 == 0: # 50% questions, 50% sentences
            template = random.choice(question_templates)
            text = template.format(keyword=keyword)
            # For now, the answer is just a simple sentence.
            # In the future, this could be a more detailed explanation.
            answer = f"A {keyword} is a {keyword}." 
            dataset.append({"text": f"<s>[INST] {text} [/INST] {answer} </s>"})
        else:
            template = random.choice(sentence_templates)
            text = template.format(keyword=keyword)
            dataset.append({"text": f"<s>[INST] {text} [/INST] {text} </s>"})

    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in dataset:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully generated {len(dataset)} examples in {output_file}")

if __name__ == '__main__':
    generate_data()
