import gradio as gr
import base64
import json
import requests
import os
from datetime import datetime

N8N_WEBHOOK_URL = "https://aravind5.app.n8n.cloud/webhook/job-outreach"

# Pre-filled personal details
DEFAULT_NAME = "Aravind Kumar"
DEFAULT_EMAIL = "rahulreddy12365@gmail.com"
DEFAULT_PORTFOLIO = "HuggingFace: https://huggingface.co/Darkweb007 | GitHub: https://github.com/data-geek-astronomy"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

CSS = """
body, .gradio-container { background: #0f1117 !important; }
.gr-button-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; border: none !important; color: white !important; font-weight: 600 !important; }
.gr-button-primary:hover { background: linear-gradient(135deg, #4f46e5, #7c3aed) !important; }
footer { display: none !important; }
"""

def result_card(contacts):
    if not contacts:
        return "<div style='background:rgba(239,68,68,0.1);border:1px solid #ef4444;border-radius:12px;padding:20px;color:#fca5a5;'>No contacts found. Try a different company domain or check your Apollo API key.</div>"
    html = f"<div style='background:rgba(99,102,241,0.1);border:1px solid #6366f1;border-radius:12px;padding:20px;'>"
    html += f"<h3 style='color:#a5b4fc;margin:0 0 16px 0;'>✅ {len(contacts)} outreach email(s) sent</h3>"
    for c in contacts:
        html += f"""
        <div style='background:rgba(255,255,255,0.05);border-radius:8px;padding:14px;margin-bottom:10px;border-left:3px solid #6366f1;'>
            <div style='color:#e2e8f0;font-weight:600;'>👤 {c.get('name','')}</div>
            <div style='color:#94a3b8;font-size:0.85em;margin:4px 0;'>{c.get('title','')} &nbsp;|&nbsp; {c.get('email','')}</div>
            <div style='color:#6366f1;font-size:0.8em;'>📧 Subject: {c.get('subject','')}</div>
        </div>"""
    html += "</div>"
    return html

def no_contacts_card(msg):
    return f"<div style='background:rgba(234,179,8,0.1);border:1px solid #eab308;border-radius:12px;padding:20px;color:#fde047;'>⚠️ {msg}</div>"

def error_card(msg):
    return f"<div style='background:rgba(239,68,68,0.1);border:1px solid #ef4444;border-radius:12px;padding:20px;color:#fca5a5;'>❌ {msg}</div>"

def send_outreach(job_title, company_name, company_domain, job_description,
                  resume_file, portfolio_url, applicant_name, applicant_email,
                  apollo_key, openai_key):

    if not all([job_title, company_name, company_domain, job_description]):
        return error_card("Please fill in all job fields before submitting.")
    if resume_file is None:
        return error_card("Please upload your resume PDF.")
    if not apollo_key:
        return error_card("Apollo API key is required. Get one free at apollo.io")
    if not openai_key:
        return error_card("OpenAI API key is required.")

    # Encode resume to base64
    try:
        with open(resume_file, 'rb') as f:
            resume_bytes = f.read()
        resume_b64 = base64.b64encode(resume_bytes).decode('utf-8')
    except Exception as e:
        return error_card(f"Failed to read resume file: {str(e)}")

    # Clean domain (strip https://, www., trailing slashes)
    domain = company_domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")

    payload = {
        "job_title": job_title.strip(),
        "company_name": company_name.strip(),
        "company_domain": domain,
        "job_description": job_description.strip(),
        "resume_base64": resume_b64,
        "portfolio_url": portfolio_url.strip(),
        "applicant_name": applicant_name.strip(),
        "applicant_email": applicant_email.strip(),
        "apollo_api_key": apollo_key.strip(),
        "openai_api_key": openai_key.strip()
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            return result_card(data.get("contacts_reached", []))
        elif data.get("status") == "no_contacts":
            return no_contacts_card(data.get("message", "No contacts found via Apollo."))
        else:
            return error_card(f"Unexpected response: {json.dumps(data, indent=2)[:500]}")

    except requests.exceptions.Timeout:
        return error_card("Request timed out (>3 min). The workflow may still be running — check your Gmail sent folder.")
    except Exception as e:
        return error_card(f"Request failed: {str(e)}")


HOW_IT_WORKS = """
<div style='color:#e2e8f0;line-height:1.8;padding:8px;'>

<h3 style='color:#a5b4fc;'>🔄 Workflow Steps</h3>

<div style='background:rgba(255,255,255,0.04);border-radius:10px;padding:16px;margin-bottom:12px;border-left:3px solid #6366f1;'>
<b style='color:#c4b5fd;'>Step 1 — Apollo.io Contact Search</b><br/>
Searches Apollo's database of 275M+ contacts for people at your target company by domain.
Prioritizes: Hiring Managers → Recruiters → VP/Head of Engineering → Engineering Managers → Tech Leads.
Returns up to 5 contacts with verified email addresses.
</div>

<div style='background:rgba(255,255,255,0.04);border-radius:10px;padding:16px;margin-bottom:12px;border-left:3px solid #8b5cf6;'>
<b style='color:#c4b5fd;'>Step 2 — GPT-4o-mini Email Generation</b><br/>
Generates a unique, personalized email for each contact based on:
their specific role, the job you applied for, and your background.
Each email is 150-200 words, warm and professional.
</div>

<div style='background:rgba(255,255,255,0.04);border-radius:10px;padding:16px;margin-bottom:12px;border-left:3px solid #ec4899;'>
<b style='color:#c4b5fd;'>Step 3 — Gmail Send with Resume</b><br/>
Sends each personalized email via your Gmail account with your resume
attached as a PDF and your portfolio link in the signature.
</div>

<h3 style='color:#a5b4fc;margin-top:20px;'>🔑 What You Need</h3>
<ul style='color:#94a3b8;'>
  <li><b style='color:#e2e8f0;'>Apollo API Key</b> — Free tier at <a href='https://apollo.io' style='color:#6366f1;'>apollo.io</a> (50 email credits/month)</li>
  <li><b style='color:#e2e8f0;'>OpenAI API Key</b> — sk-... from <a href='https://platform.openai.com' style='color:#6366f1;'>platform.openai.com</a></li>
  <li><b style='color:#e2e8f0;'>Resume PDF</b> — Uploaded each time you apply</li>
  <li><b style='color:#e2e8f0;'>Company Domain</b> — e.g. <code style='color:#a5b4fc;'>google.com</code>, <code style='color:#a5b4fc;'>stripe.com</code></li>
</ul>

<h3 style='color:#a5b4fc;margin-top:20px;'>💡 Tips</h3>
<ul style='color:#94a3b8;'>
  <li>Use the exact company domain (not a careers subdomain)</li>
  <li>Paste the full job description for better email personalization</li>
  <li>Apollo free tier: 50 verified emails/month — enough for active job searching</li>
  <li>Emails send from your own Gmail — replies come straight to you</li>
</ul>

</div>
"""

with gr.Blocks(css=CSS, theme=gr.themes.Soft(primary_hue="violet"), title="Job Application Outreach Agent") as demo:

    gr.HTML("""
    <div style='text-align:center;padding:28px 0 12px 0;'>
        <div style='font-size:2.8em;'>🎯</div>
        <h1 style='color:#e2e8f0;margin:8px 0 4px 0;font-size:1.8em;'>Job Application Outreach Agent</h1>
        <p style='color:#94a3b8;margin:0;font-size:1em;'>Find hiring managers via Apollo · Generate personalized emails · Send with resume attached</p>
        <a href='https://aravind5.app.n8n.cloud/workflow/sYlzBFqoLBAfGfVE' target='_blank'
           style='display:inline-block;margin-top:10px;padding:6px 16px;background:rgba(99,102,241,0.15);border:1px solid #6366f1;border-radius:20px;color:#a5b4fc;font-size:0.85em;text-decoration:none;'>
            🔗 Live n8n Workflow
        </a>
    </div>
    """)

    with gr.Tabs():

        with gr.Tab("🚀 Send Outreach"):

            gr.HTML("<div style='color:#94a3b8;font-size:0.88em;padding:4px 0 12px 0;'>Fill in the job details, upload your resume, and the agent will find the right people and send personalized emails automatically.</div>")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML("<h3 style='color:#a5b4fc;margin:0 0 10px 0;font-size:1em;'>📋 Job Details</h3>")
                    job_title = gr.Textbox(label="Job Title *", placeholder="Senior Software Engineer")
                    company_name = gr.Textbox(label="Company Name *", placeholder="Stripe")
                    company_domain = gr.Textbox(label="Company Domain *", placeholder="stripe.com")
                    job_description = gr.Textbox(
                        label="Job Description *",
                        placeholder="Paste the full job description here...",
                        lines=7,
                        max_lines=15
                    )

                with gr.Column(scale=1):
                    gr.HTML("<h3 style='color:#a5b4fc;margin:0 0 10px 0;font-size:1em;'>👤 Your Details</h3>")
                    applicant_name = gr.Textbox(label="Your Name", value=DEFAULT_NAME)
                    applicant_email = gr.Textbox(label="Your Email", value=DEFAULT_EMAIL)
                    portfolio_url = gr.Textbox(label="Portfolio / LinkedIn URL", value=DEFAULT_PORTFOLIO)
                    resume_file = gr.File(label="Resume PDF *", file_types=[".pdf"], type="filepath")

                    gr.HTML("<h3 style='color:#a5b4fc;margin:16px 0 10px 0;font-size:1em;'>🔑 API Keys</h3>")
                    apollo_key = gr.Textbox(
                        label="Apollo API Key *",
                        placeholder="apollo_xxxxxxxxxxxx",
                        value=APOLLO_API_KEY,
                        type="password"
                    )
                    openai_key = gr.Textbox(
                        label="OpenAI API Key *",
                        placeholder="sk-...",
                        value=OPENAI_API_KEY,
                        type="password"
                    )

            submit_btn = gr.Button("🚀 Find Contacts & Send Outreach Emails", variant="primary", size="lg")

            gr.HTML("<div style='color:#64748b;font-size:0.8em;margin:8px 0 4px 0;'>This will search Apollo for up to 5 hiring contacts at the company and send each a personalized email with your resume attached. Check your Gmail Sent folder after.</div>")

            result_html = gr.HTML(value="")

            submit_btn.click(
                fn=send_outreach,
                inputs=[job_title, company_name, company_domain, job_description,
                        resume_file, portfolio_url, applicant_name, applicant_email,
                        apollo_key, openai_key],
                outputs=result_html
            )

        with gr.Tab("⚙️ How It Works"):
            gr.HTML(HOW_IT_WORKS)

if __name__ == "__main__":
    demo.launch()
