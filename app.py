import gradio as gr
import base64
import json
import requests
import os

N8N_WEBHOOK_URL = "https://aravind5.app.n8n.cloud/webhook/job-outreach-v2"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

CSS = """
body, .gradio-container { background: #0a0d14 !important; }
.gr-button-primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important; color: white !important;
    font-weight: 700 !important; font-size: 1.05em !important;
    padding: 14px 32px !important; border-radius: 10px !important;
}
.gr-button-primary:hover { background: linear-gradient(135deg, #4f46e5, #7c3aed) !important; }
footer { display: none !important; }
"""

def result_card(contacts):
    html = f"""
    <div style='background:rgba(99,102,241,0.08);border:1px solid #6366f1;border-radius:14px;padding:22px;'>
        <h3 style='color:#a5b4fc;margin:0 0 18px 0;font-size:1.1em;'>
            ✅ {len(contacts)} outreach email{"s" if len(contacts)!=1 else ""} sent from analukur@asu.edu
        </h3>"""
    for c in contacts:
        html += f"""
        <div style='background:rgba(255,255,255,0.04);border-radius:10px;padding:14px;margin-bottom:10px;border-left:3px solid #8b5cf6;'>
            <div style='color:#e2e8f0;font-weight:600;font-size:0.95em;'>👤 {c.get("name","")}</div>
            <div style='color:#94a3b8;font-size:0.82em;margin:3px 0;'>{c.get("title","")} &nbsp;·&nbsp; {c.get("email","")}</div>
            <div style='color:#6366f1;font-size:0.8em;margin-top:4px;'>📧 {c.get("subject","")}</div>
        </div>"""
    html += "</div>"
    return html

def no_contacts_card(msg):
    return f"<div style='background:rgba(234,179,8,0.08);border:1px solid #eab308;border-radius:12px;padding:20px;color:#fde047;'>⚠️ {msg}<br/><br/><span style='color:#94a3b8;font-size:0.85em;'>Try checking the company domain is correct (e.g. <b>stripe.com</b> not <b>careers.stripe.com</b>). Also ensure your Apollo key has credits remaining.</span></div>"

def error_card(msg):
    return f"<div style='background:rgba(239,68,68,0.08);border:1px solid #ef4444;border-radius:12px;padding:20px;color:#fca5a5;'>❌ {msg}</div>"

def processing_card():
    return "<div style='background:rgba(99,102,241,0.08);border:1px solid #6366f1;border-radius:12px;padding:20px;color:#a5b4fc;'>⏳ Finding contacts and sending emails... this takes 1-3 minutes.</div>"


def send_outreach(jd_text, resume_file, apollo_key, openai_key):
    if not jd_text or not jd_text.strip():
        return error_card("Please paste the job description.")
    if resume_file is None:
        return error_card("Please upload your resume PDF.")
    if not apollo_key:
        return error_card("Apollo API key is required. Get one free at apollo.io")
    if not openai_key:
        return error_card("OpenAI API key is required.")

    try:
        with open(resume_file, "rb") as f:
            resume_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return error_card(f"Could not read resume file: {e}")

    payload = {
        "jd_text": jd_text.strip(),
        "resume_base64": resume_b64,
        "apollo_api_key": apollo_key.strip(),
        "openai_api_key": openai_key.strip(),
    }

    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return error_card("Timed out after 5 min. The workflow may still be running — check your ASU email Sent folder.")
    except Exception as e:
        return error_card(f"Request failed: {e}")

    if data.get("status") == "success":
        return result_card(data.get("contacts_reached", []))
    elif data.get("status") == "no_contacts":
        return no_contacts_card(data.get("message", "No contacts found."))
    else:
        return error_card(f"Unexpected response: {json.dumps(data)[:400]}")


with gr.Blocks(css=CSS, theme=gr.themes.Soft(primary_hue="violet"), title="Job Outreach Agent") as demo:

    gr.HTML("""
    <div style='text-align:center;padding:30px 0 16px;'>
        <div style='font-size:3em;'>🎯</div>
        <h1 style='color:#e2e8f0;margin:10px 0 6px;font-size:1.9em;font-weight:700;'>
            Job Application Outreach Agent
        </h1>
        <p style='color:#64748b;margin:0;font-size:0.95em;'>
            Paste a JD · AI extracts the company · Apollo finds hiring contacts · GPT writes personalized emails · Sends from your ASU email
        </p>
        <a href='https://aravind5.app.n8n.cloud/workflow/O6EBcekwsGCqY2z7' target='_blank'
           style='display:inline-block;margin-top:12px;padding:6px 18px;background:rgba(99,102,241,0.12);border:1px solid #6366f1;border-radius:20px;color:#a5b4fc;font-size:0.82em;text-decoration:none;'>
            🔗 Live n8n Workflow
        </a>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            jd_text = gr.Textbox(
                label="📋 Paste Job Description",
                placeholder="Paste the full job description here. The AI will automatically extract the company name, role, domain, and team — no manual fields needed.",
                lines=16,
                max_lines=30
            )
        with gr.Column(scale=2):
            resume_file = gr.File(
                label="📄 Upload Your Resume (PDF)",
                file_types=[".pdf"],
                type="filepath"
            )
            gr.HTML("<div style='color:#475569;font-size:0.8em;margin:4px 0 16px;'>Attached to every outreach email sent</div>")

            gr.HTML("<hr style='border-color:#1e293b;margin:8px 0 16px;'/>")
            gr.HTML("<div style='color:#64748b;font-size:0.82em;margin-bottom:8px;'>API Keys (stored as HF Secrets — never exposed)</div>")

            apollo_key = gr.Textbox(
                label="Apollo API Key",
                placeholder="apollo_xxxxxxxxxxxxxxxx",
                value=APOLLO_API_KEY,
                type="password"
            )
            openai_key = gr.Textbox(
                label="OpenAI API Key",
                placeholder="sk-...",
                value=OPENAI_API_KEY,
                type="password"
            )

    submit_btn = gr.Button("🚀 Find Contacts & Send Outreach Emails", variant="primary", size="lg")

    gr.HTML("""
    <div style='color:#334155;font-size:0.78em;text-align:center;margin:6px 0 12px;'>
        Emails send from <b style='color:#475569;'>analukur@asu.edu</b> via SMTP · Top 10 hiring contacts found via Apollo · Each email is uniquely personalized
    </div>
    """)

    result_html = gr.HTML()

    submit_btn.click(
        fn=send_outreach,
        inputs=[jd_text, resume_file, apollo_key, openai_key],
        outputs=result_html
    )

    gr.HTML("""
    <div style='margin-top:32px;padding:20px;background:rgba(255,255,255,0.02);border-radius:12px;border:1px solid #1e293b;'>
        <h3 style='color:#64748b;font-size:0.85em;font-weight:600;margin:0 0 12px;'>⚙️ HOW IT WORKS</h3>
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;'>
            <div style='color:#94a3b8;font-size:0.8em;'><span style='color:#6366f1;font-weight:600;'>① Extract</span><br/>GPT-4o-mini parses the JD and extracts company name, domain, role, and team automatically</div>
            <div style='color:#94a3b8;font-size:0.8em;'><span style='color:#6366f1;font-weight:600;'>② Find</span><br/>Apollo.io searches 275M+ contacts for hiring managers, recruiters, and eng leads at the company</div>
            <div style='color:#94a3b8;font-size:0.8em;'><span style='color:#6366f1;font-weight:600;'>③ Write</span><br/>GPT-4o-mini personalizes your email template for each contact, referencing their specific role</div>
            <div style='color:#94a3b8;font-size:0.8em;'><span style='color:#6366f1;font-weight:600;'>④ Send</span><br/>Emails go out from analukur@asu.edu via SMTP with your resume attached to every message</div>
        </div>
    </div>
    """)

if __name__ == "__main__":
    demo.launch()
