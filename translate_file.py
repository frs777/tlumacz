import os
import sys
import openai

# Ustawienia API (używając kompatybilnego endpointu OpenAI)
client = openai.OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="ollama"
)

MODEL_NAME = "qwen2.5-coder-7b-instruct-q5_k_m"

def translate_chunk(chunk):
    prompt = f"Przetłumacz poniższą treść na język polski, zachowując formatowanie markdown:\n\n{chunk}"
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

def split_file(file_path, chunk_size=8000):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Prosty podział na znaki (bardzo przybliżony, ale wystarczający dla uproszczenia)
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

def main():
    if len(sys.argv) < 3:
        print("Użycie: python3 translate_file.py <input_path> <output_path>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    chunks = split_file(input_path)
    print(f"Przetwarzanie {len(chunks)} fragmentów...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            print(f"Tłumaczenie fragmentu {i+1}/{len(chunks)}...")
            translated = translate_chunk(chunk)
            f.write(translated)
            f.write("\n\n")

if __name__ == "__main__":
    main()
