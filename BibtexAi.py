import streamlit as st
import google.generativeai as genai
import os
from PyPDF2 import PdfReader
from docx import Document

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Configure the API key for Google Generative AI
genai.configure(api_key=api_key)
# Streamlit App Title
st.title("BibTeXAI")

# Function to generate BibTeX using the Gemini model
# Function to generate BibTeX using the Gemini model
def generate_bibtex(reference):
    try:
        # Create a GenerativeModel instance
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate content using the model
        response = model.generate_content(f"Generate a BibTeX entry for this reference: {reference}")
        
        # Extract and return the text (BibTeX entry) from the response
        bibtex_text = response.text.strip()  # Ensure we return only the text part and remove any leading/trailing spaces
        
        return bibtex_text
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract references from PDF file
def extract_references_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        # Extract references based on a heuristic approach
        references = []
        current_reference = []
        reference_start = False
        for line in text.split("\n"):
            if any(keyword in line.lower() for keyword in ["references", "bibliography"]):
                reference_start = True
            if reference_start:
                # Handle multi-line references
                if line.strip() and not line.strip().isdigit():
                    current_reference.append(line.strip())
                elif current_reference:
                    references.append(" ".join(current_reference))
                    current_reference = []
        
        # Append the last reference if any
        if current_reference:
            references.append(" ".join(current_reference))

        if not references:
            return "No references found in the document."
        
        return references
    except Exception as e:
        return f"Error: {str(e)}"
    

  # Function to extract references from DOCX file
def extract_references_from_docx(file):
    try:
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        
        # Extract references based on a heuristic approach
        references = []
        current_reference = []
        reference_start = False
        for line in text.split("\n"):
            if any(keyword in line.lower() for keyword in ["references", "bibliography"]):
                reference_start = True
            if reference_start:
                # Handle multi-line references
                if line.strip() and not line.strip().isdigit():
                    current_reference.append(line.strip())
                elif current_reference:
                    references.append(" ".join(current_reference))
                    current_reference = []
        
        # Append the last reference if any
        if current_reference:
            references.append(" ".join(current_reference))

        return references
    except Exception as e:
        return f"Error: {str(e)}"
  # Input method selection
input_method = st.radio("Choose input method:", ("Enter reference manually", "Upload a document"))

# Placeholder for the BibTeX content
bibtex_entries = []

if input_method == "Enter reference manually":
    reference_input = st.text_area("Enter the reference you want to convert to BibTeX format:")
    
    if st.button("Generate BibTeX"):
        if reference_input:
            with st.spinner("Generating BibTeX format..."):
                bibtex_output = generate_bibtex(reference_input)
            if "Error" in bibtex_output:
                st.error(bibtex_output)
            else:
                st.success("Generated BibTeX:")
                st.code(bibtex_output, language='bibtex')
                bibtex_entries.append(bibtex_output)
        else:
            st.error("Please enter a reference to generate the BibTeX format.")

elif input_method == "Upload a document":
    uploaded_file = st.file_uploader("Upload a PDF or DOCX file", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        with st.spinner("Extracting references..."):
            if uploaded_file.type == "application/pdf":
                references = extract_references_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                references = extract_references_from_docx(uploaded_file)
            else:
                references = "Unsupported file type."
        
        if "Error" in references or isinstance(references, str):
            st.error(references)
        else:
            st.success("References extracted:")
            st.write(references)
            
            # Generating BibTeX for each extracted reference
            if st.button("Generate BibTeX for all references"):
                for ref in references:
                    with st.spinner(f"Generating BibTeX for: {ref[:30]}..."):
                        bibtex_output = generate_bibtex(ref)
                    if "Error" in bibtex_output:
                        st.error(f"Error generating BibTeX for: {ref[:30]}")
                    else:
                        st.code(bibtex_output, language='bibtex')
                        bibtex_entries.append(bibtex_output)

# Function to save BibTeX entries to a .bib file
def save_bibtex_file(bibtex_entries, filename="references.bib"):
    try:
        with open(filename, "w", encoding='utf-8') as bibfile:
            for entry in bibtex_entries:
                bibfile.write(entry + "\n\n")
        return filename
    except Exception as e:
        return f"Error: {str(e)}"

# Show download button if there are any BibTeX entries
if bibtex_entries:
    bib_filename = save_bibtex_file(bibtex_entries)
    
    if isinstance(bib_filename, str) and not bib_filename.startswith("Error"):
        try:
            # Open the saved .bib file in read mode (text mode)
            with open(bib_filename, "r",  encoding='utf-8') as bibfile:
                st.download_button(
                    label="Download BibTeX file",
                    data=bibfile.read(),
                    file_name=bib_filename,
                    mime="application/x-bibtex"
                )
        except Exception as e:
            st.error(f"Error opening the .bib file: {str(e)}")
    else:
        st.error(bib_filename)  # If saving the file failed