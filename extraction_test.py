import pdfplumber

with pdfplumber.open("AMS WO#75278.pdf") as pdf:
    # Page 44 is 75278-06 which has both PROWATERJE and CNCMILL
    page = pdf.pages[43]
    text = page.extract_text()

    for line in text.split('\n'):
        if 'Setup' in line:
            print(repr(line))