def build_job_extraction_prompt(text):
    return f"""
You are a job post cleaner processing messy OCR text from screenshots.

🔥 Absolute Rules:
1. Title:
   - Extract ONLY if clearly identifiable (e.g., "مهندس", "حسابات" ," Sales Agent")
   - Leave empty if uncertain
   - Never translate (keep original Kurdish/Arabic)

2. Category (REQUIRED):
   - Deduce from context (e.g., "مبيعات" → "Sales")

3. Other Fields:
   - Location: Normalize to English (e.g., "Erbil" not "ههولێر")
   - Salary: ONLY if numbers + currency (دينار, $)
   - Requirements: Condense to MAX 15 words
   - Image: Always ""

⚡ Output STRICT JSON (NO explanations):
{{
  "title": "",
  "category": "",
  "location": "",
  "salary": "",
  "requirements": "",
  "description": "",
  "image": ""
}}

OCR Text:
{text.strip()}
"""