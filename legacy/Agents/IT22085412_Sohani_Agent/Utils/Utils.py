import fitz  # PyMuPDF

def extract_text_from_pdf(file_obj):
    """
    Extracts text from PDF file object.
    """
    doc = fitz.open(stream=file_obj.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text