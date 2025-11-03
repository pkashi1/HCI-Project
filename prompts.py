from transformers import pipeline

# Load a summarization-capable model
pipe = pipeline("text2text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")

# Load transcript text
with open("Chicken Biryani - A step-by-step guide to the best rice dish ever_transcript.txt", "r", encoding="utf-8") as f:
    transcript = f.read()

# Prompt for structured cooking steps
prompt = f"""
You are a professional chef and voice assistant designer.
Read the following transcript and extract clear, numbered cooking steps.
Each step must be short, actionable, and in order.
Use imperative form ("Add", "Mix", "Wait 10 minutes").
Output as JSON with keys: step_number, instruction, estimated_time (if any).

Transcript:
{transcript}
"""

# Generate structured instructions
result = pipe(prompt, max_new_tokens=1024, temperature=0.3)
print(result[0]['generated_text'])
