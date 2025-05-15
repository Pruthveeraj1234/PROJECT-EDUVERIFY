from pdf2image import convert_from_path

# Replace with the path to a sample PDF file
pdf_path = "sample.pdf"
try:
    images = convert_from_path(pdf_path)
    print(f"Successfully converted PDF to {len(images)} image(s).")
except Exception as e:
    print(f"Error: {str(e)}")