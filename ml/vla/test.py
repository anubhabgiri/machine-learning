import torch
from transformers import pipeline, set_seed

def generate_response(prompt, max_length=100, num_return_sequences=1, seed=42):
    """
    Generates a response from DistilGPT-2 given a prompt.

    Args:
        prompt (str): The input prompt.
        max_length (int): The maximum length of the generated response.
        num_return_sequences (int): The number of response sequences to generate.
        seed (int): The random seed for reproducibility.

    Returns:
        list: A list of generated response strings.
    """
    try:
        generator = pipeline('text-generation', model='distilgpt2')
        set_seed(seed)  # for reproducibility
        generated_texts = generator(prompt, max_length=max_length, num_return_sequences=num_return_sequences)
        responses = [text['generated_text'] for text in generated_texts]
        return responses

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Example Usage
prompt = "send an email to Barb"
responses = generate_response(prompt, max_length=50, num_return_sequences=3)

if responses:
    for i, response in enumerate(responses):
        print(f"Response {i+1}: {response}")
else:
    print("No responses generated.")

#Example usage with different max length and sequences.
# prompt2 = "Write a short story about a cat who learns to fly."
# responses2 = generate_response(prompt2, max_length=200, num_return_sequences=1)

# if responses2:
#     for i, response in enumerate(responses2):
#         print(f"Response {i+1}: {response}")
# else:
#     print("No responses generated.")