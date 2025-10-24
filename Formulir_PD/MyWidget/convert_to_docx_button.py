from docxtpl import DocxTemplate
import os

template_path = r"D:\Kerja Praktik\Project\Formulir PD (PySide6)\Document\Form Pengujian PD Kabel Power dan Incoming 20KV.docx"
if not os.path.exists(template_path):
    raise FileNotFoundError(f"Template not found: {template_path}")

doc = DocxTemplate(template_path)
context = {"name": "Rafid"}
doc.render(context)
doc.save(r"D:\Kerja Praktik\Project\Formulir PD (PySide6)\Document\Output_Form Pengujian PD Kabel Power dan Incoming 20KV.docx")