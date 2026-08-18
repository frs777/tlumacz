import os
import sys
import openai

# Ustawienia API
client = openai.OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="ollama"
)
MODEL_NAME = "qwen2.5-coder-7b-instruct-q5_k_m"

def translate_text(text):
    prompt = f"Przetłumacz poniższą treść na język polski, zachowując formatowanie markdown:\n\n{text}"
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

def process_file(input_path, output_path, chunk_size=5000):
    if not os.path.exists(input_path):
        print(f"Plik wejściowy nie istnieje: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Prosty podział na fragmenty
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    print(f"Przetwarzanie {len(chunks)} fragmentów...")

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            print(f"Tłumaczenie fragmentu {i+1}/{len(chunks)}...")
            try:
                translated = translate_text(chunk)
                f.write(translated)
                f.write("\n\n")
            except Exception as e:
                print(f"Błąd przy fragmencie {i+1}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Użycie: python3 script.py <input> <output>")
    else:
        process_file(sys.argv[1], sys.argv[2])
