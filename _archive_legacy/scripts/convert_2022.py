import os
import sys
import win32com.client as win32

def convert_to_docx(doc_path):
    print(f"Converting {doc_path}...")
    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(doc_path)
        
        docx_path = doc_path + "x"
        # 12 = wdFormatXMLDocument (docx)
        # 16 = wdFormatDocumentDefault
        doc.SaveAs2(docx_path, FileFormat=12) 
        doc.Close()
        word.Quit()
        print(f"Saved to {docx_path}")
    except Exception as e:
        print(f"Conversion failed: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(base_dir, "DOCX", "2022年考研英语一真题.doc")
    if os.path.exists(doc_path):
        convert_to_docx(doc_path)
    else:
        print("File not found")
