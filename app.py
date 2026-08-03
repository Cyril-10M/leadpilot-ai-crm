import streamlit as st
import sqlite3
import json
from datetime import datetime

st.set_page_config(page_title="LeadPilot AI", page_icon="🎯", layout="wide")

DB = "leads.db"

def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, company TEXT NOT NULL, email TEXT,
        job_title TEXT, industry TEXT, company_size INTEGER,
        deal_value REAL, pain_point TEXT, timeline TEXT, source TEXT,
        stage TEXT DEFAULT 'New', score INTEGER, priority TEXT,
        reasoning TEXT, next_action TEXT, followup TEXT,
        created_at TEXT
    )""")
    c.commit()
init_db()

def qualify(d):
    score = 15
    reasons = []
    title = (d["job_title"] or "").lower()
    if any(x in title for x in ["founder","ceo","cfo","cro","vp","director","head"]):
        score += 25; reasons.append("senior decision-maker")
    elif any(x in title for x in ["manager","lead"]):
        score += 15; reasons.append("relevant stakeholder")
    if d["company_size"] >= 500:
        score += 20; reasons.append("large company")
    elif d["company_size"] >= 100:
        score += 12; reasons.append("mid-market company")
    if d["deal_value"] >= 50000:
        score += 15; reasons.append("high potential deal value")
    elif d["deal_value"] >= 10000:
        score += 8; reasons.append("meaningful deal value")
    timeline = d["timeline"]
    if timeline == "Within 1 month":
        score += 20; reasons.append("immediate buying timeline")
    elif timeline == "1–3 months":
        score += 12; reasons.append("near-term buying intent")
    if d["pain_point"] and len(d["pain_point"].strip()) > 20:
        score += 5; reasons.append("clear business pain identified")
    score = min(score, 100)
    priority = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
    next_action = ("Book a discovery/demo call within 24 hours" if priority=="High"
                   else "Send a tailored value proposition and qualify further" if priority=="Medium"
                   else "Add to nurture sequence and revisit later")
    rs = ", ".join(reasons) if reasons else "limited buying signals currently available"
    reasoning = f"This lead scores {score}/100 because of {rs}. The combination indicates {priority.lower()} sales readiness."
    first = d["name"].split()[0]
    pain = d["pain_point"] or "your team's current sales workflow"
    follow = f"""Hi {first},

Thanks for connecting. I noticed that {pain.lower()}. Based on what you've shared, I think there may be a strong opportunity to simplify the process and help your team focus on higher-value outcomes.

Would you be open to a quick 15-minute conversation this week to see whether there is a fit?

Best,
Sales Team"""
    return score, priority, reasoning, next_action, follow

def rows():
    return conn().execute("SELECT * FROM leads ORDER BY id DESC").fetchall()

st.title("🎯 LeadPilot AI")
st.caption("AI-powered lead qualification CRM • Prioritize the right prospects. Know what to do next.")

data = rows()
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Leads", len(data))
c2.metric("High Priority", sum(1 for r in data if r["priority"]=="High"))
c3.metric("Qualified", sum(1 for r in data if r["stage"]=="Qualified"))
c4.metric("Pipeline Value", f"${sum((r['deal_value'] or 0) for r in data):,.0f}")

tab1, tab2 = st.tabs(["📊 Lead Pipeline", "➕ Add Lead"])

with tab2:
    st.subheader("Add & qualify a new lead")
    with st.form("add"):
        a,b = st.columns(2)
        name = a.text_input("Contact name *")
        company = b.text_input("Company *")
        email = a.text_input("Email")
        job = b.text_input("Job title", placeholder="e.g. CFO, Sales Director")
        industry = a.selectbox("Industry", ["Fintech","SaaS","E-commerce","Technology","Financial Services","Healthcare","Manufacturing","Other"])
        size = b.number_input("Company size (employees)", 1, 100000, 100)
        value = a.number_input("Estimated deal value ($)", 0, 10000000, 10000)
        timeline = b.selectbox("Buying timeline", ["Within 1 month","1–3 months","3–6 months","6+ months","Unknown"])
        source = a.selectbox("Lead source", ["Inbound","LinkedIn","Referral","Event","Outbound","Other"])
        pain = st.text_area("Pain point / requirement", placeholder="What problem is this prospect trying to solve?")
        submit = st.form_submit_button("✨ Save & Qualify Lead", use_container_width=True)
        if submit:
            if not name or not company:
                st.error("Contact name and company are required.")
            else:
                d=dict(name=name, company=company, email=email, job_title=job, industry=industry,
                       company_size=size, deal_value=value, timeline=timeline, source=source, pain_point=pain)
                score,priority,reason,next_action,follow=qualify(d)
                c=conn()
                c.execute("""INSERT INTO leads(name,company,email,job_title,industry,company_size,deal_value,pain_point,timeline,source,stage,score,priority,reasoning,next_action,followup,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name,company,email,job,industry,size,value,pain,timeline,source,"New",score,priority,reason,next_action,follow,datetime.now().isoformat()))
                c.commit()
                st.success(f"Lead qualified: {score}/100 • {priority} priority")
                st.rerun()

with tab1:
    q = st.text_input("🔎 Search leads", placeholder="Search contact, company, email...")
    f1,f2 = st.columns(2)
    priority_filter=f1.selectbox("Priority",["All","High","Medium","Low"])
    stage_filter=f2.selectbox("Stage",["All","New","Qualified","Contacted","Demo","Negotiation","Won","Lost"])
    filtered=[]
    for r in data:
        hay=f"{r['name']} {r['company']} {r['email']}".lower()
        if q.lower() not in hay: continue
        if priority_filter!="All" and r["priority"]!=priority_filter: continue
        if stage_filter!="All" and r["stage"]!=stage_filter: continue
        filtered.append(r)

    if not filtered:
        st.info("No leads yet. Add your first lead from the Add Lead tab.")
    for r in filtered:
        with st.expander(f"{'🔥' if r['priority']=='High' else '⚡' if r['priority']=='Medium' else '🌱'}  {r['name']} — {r['company']}  |  {r['score']}/100 • {r['priority']}"):
            x,y=st.columns([2,1])
            with x:
                st.markdown(f"**{r['job_title'] or 'Role not provided'}** · {r['industry']} · {r['company_size']} employees")
                st.markdown(f"**Pain point:** {r['pain_point'] or 'Not provided'}")
                st.markdown("#### AI Qualification")
                st.write(r["reasoning"])
                st.markdown(f"**Recommended next action:** {r['next_action']}")
                st.markdown("**Personalized follow-up**")
                st.code(r["followup"], language=None)
            with y:
                st.metric("Lead Score", f"{r['score']}/100")
                stages=["New","Qualified","Contacted","Demo","Negotiation","Won","Lost"]
                newstage=st.selectbox("Lead stage", stages, index=stages.index(r["stage"]), key=f"s{r['id']}")
                if newstage != r["stage"]:
                    c=conn(); c.execute("UPDATE leads SET stage=? WHERE id=?",(newstage,r["id"])); c.commit(); st.rerun()
                st.write(f"**Deal:** ${r['deal_value'] or 0:,.0f}")
                st.write(f"**Timeline:** {r['timeline']}")
                st.write(f"**Source:** {r['source']}")
        if st.button("📝 Edit lead", key=f"edit{r['id']}"):
            st.session_state[f"editing{r['id']}"] = not st.session_state.get(f"editing{r['id']}", False)

        if st.session_state.get(f"editing{r['id']}", False):
            with st.form(key=f"editform{r['id']}"):
                edit_name = st.text_input("Contact name", value=r["name"])
                edit_company = st.text_input("Company", value=r["company"])
                edit_email = st.text_input("Email", value=r["email"] or "")
                edit_job = st.text_input("Job title", value=r["job_title"] or "")
                edit_deal = st.number_input("Estimated deal value ($)", min_value=0.0, value=float(r["deal_value"] or 0))
                edit_pain = st.text_area("Pain point / requirement", value=r["pain_point"] or "")

                save_edit = st.form_submit_button("💾 Save changes")

                if save_edit:
                    c = conn()
                    c.execute(
                        """UPDATE leads
                           SET name=?, company=?, email=?, job_title=?, deal_value=?, pain_point=?
                           WHERE id=?""",
                        (edit_name, edit_company, edit_email, edit_job, edit_deal, edit_pain, r["id"])
                    )
                    c.commit()
                    c.close()
                    st.session_state[f"editing{r['id']}"] = False
                    st.success("Lead updated successfully!")
                    st.rerun()
                if st.button("🗑️ Delete lead", key=f"d{r['id']}"):
                    c=conn(); c.execute("DELETE FROM leads WHERE id=?",(r["id"],)); c.commit(); st.rerun()
