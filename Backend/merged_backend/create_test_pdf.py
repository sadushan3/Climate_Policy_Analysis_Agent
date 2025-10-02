from fpdf import FPDF

def create_pdf(text, output_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split text into lines and write to PDF
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, txt=line)
    
    pdf.output(output_file)

if __name__ == "__main__":
    sample_text = """Climate Policy Document

Policy Section 1: Coastal Protection Strategy
The coastal regions of Colombo and Galle face increasing risks due to climate change. This policy aims to implement protective measures against rising sea levels and extreme weather events. We project a temperature increase of 2°C by 2030 in these coastal areas, with increased humidity levels during monsoon seasons. The policy recommends strengthening coastal infrastructure to withstand stronger winds and more frequent storms.

Key measures include:
- Building sea walls in Colombo harbor
- Implementing early warning systems for extreme weather
- Reducing thermal pollution in coastal waters
- Monitoring humidity levels in affected areas
- Installing wind barriers in high-risk zones

Policy Section 2: Urban Climate Resilience Plan
Kandy and Trincomalee require adaptive measures to address changing weather patterns. This framework focuses on reducing urban heat islands and managing increased precipitation. We expect more variable temperature conditions, with humidity fluctuations affecting both cities. Wind patterns are projected to become more erratic, especially during the northeast monsoon.

Implementation strategies:
- Installing green roofs to reduce temperature impacts
- Improving drainage systems for higher rainfall
- Developing wind-resistant building standards
- Creating urban forests to regulate local temperature
- Monitoring air moisture levels in city centers"""

    create_pdf(sample_text, "test_data/sample_policy.pdf")