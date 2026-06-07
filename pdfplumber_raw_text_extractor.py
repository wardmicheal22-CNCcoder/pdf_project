import pdfplumber

with pdfplumber.open("AMS WO#75278.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and "Job Number:" in text and "Customer:" in text:
            print(f"\n── Page {i+1} Raw Text ──")
            print(text)