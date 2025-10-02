import requests
import json
import os
from fpdf import FPDF
import io

BASE_URL = "http://localhost:8000/api"

def test_full_analysis():
    url = f"{BASE_URL}/policy/full-analysis"
    # Create PDF in memory
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
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
    
    for line in sample_text.split('\n'):
        pdf.multi_cell(0, 10, txt=line)
    
    # Save PDF to bytes buffer
    pdf_buffer = io.BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')  # Get PDF as bytes
    pdf_buffer = io.BytesIO(pdf_content)  # Create buffer with PDF content
    
    # Send request with PDF
    files = {'file': ('sample_policy.pdf', pdf_buffer, 'application/pdf')}
    try:
        response = requests.post(url, files=files)
        print("\n=== Full Analysis Test ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("\nDocument Analysis:")
            print(f"Document Name: {result['document_name']}")
            print(f"Word Count: {result['word_count']}")
            
            print("\nPolicy 1 Summary:")
            print(result['policies']['policy1']['summary'])
            
            print("\nPolicy 2 Summary:")
            print(result['policies']['policy2']['summary'])
            
            print("\nPolicy Comparison:")
            print(f"Similarity Score: {result['policies']['comparison']['similarity_score']:.2f}")
            
            print("\nWeather Recommendations:")
            for rec in result['weather_recommendations']:
                print(f"\nLocation: {rec['location']}")
                print(f"Predicted Condition: {rec['prediction']['predicted_condition']}")
                print("Policy Impacts:")
                for factor, value in rec['policy_impacts'].items():
                    print(f"  {factor}: {value}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error making request: {str(e)}")

if __name__ == "__main__":
    print("Starting API Tests...")
    test_full_analysis()