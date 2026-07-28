import os
import re

def convert_md_to_html():
    report_md_path = os.path.join(os.path.dirname(__file__), "Final_Project_Report.md")
    report_html_path = os.path.join(os.path.dirname(__file__), "Final_Project_Report.html")
    
    if not os.path.exists(report_md_path):
        print(f"Error: {report_md_path} not found.")
        return
        
    with open(report_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    # Basic Markdown to HTML formatting
    html_content = md_text
    
    # Headers
    html_content = re.sub(r'^# (.*?)$', r'<h1 class="title">\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)
    
    # Bold & Italic
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
    
    # Horizontal rules
    html_content = re.sub(r'^---$', r'<hr>', html_content, flags=re.MULTILINE)
    
    # Code blocks
    html_content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html_content, flags=re.DOTALL)
    
    # Paragraph lines
    paragraphs = html_content.split('\n\n')
    formatted_p = []
    for p in paragraphs:
        p_strip = p.strip()
        if p_strip.startswith('<h') or p_strip.startswith('<pre') or p_strip.startswith('<hr') or p_strip.startswith('<table'):
            formatted_p.append(p_strip)
        else:
            formatted_p.append(f'<p>{p_strip}</p>')
            
    body_html = '\n'.join(formatted_p)
    
    full_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Final Project Report - AI Retail Intelligence Platform</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            line-height: 1.6;
            color: #1F2937;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px 40px;
            background-color: #F9FAFB;
        }}
        .title {{
            color: #4F46E5;
            font-size: 2.2rem;
            border-bottom: 3px solid #6366F1;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #1E1B4B;
            border-bottom: 1px solid #E5E7EB;
            padding-bottom: 6px;
            margin-top: 30px;
        }}
        h3 {{ color: #3730A3; margin-top: 20px; }}
        hr {{ border: 0; height: 1px; background: #E5E7EB; margin: 30px 0; }}
        pre {{
            background: #1E293B;
            color: #F8FAFC;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9rem;
        }}
        code {{ font-family: 'Fira Code', monospace; }}
        p {{ margin-bottom: 16px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #E5E7EB;
            padding: 10px 14px;
            text-align: left;
        }}
        th {{ background-color: #EEF2FF; color: #312E81; }}
        tr:nth-child(even) {{ background-color: #F3F4F6; }}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""
    with open(report_html_path, "w", encoding="utf-8") as f:
        f.write(full_document)
        
    print(f"HTML report successfully generated at: {report_html_path}")

if __name__ == "__main__":
    convert_md_to_html()
