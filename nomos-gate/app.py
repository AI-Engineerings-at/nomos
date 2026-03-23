"""NomOS Compliance Gate."""
import streamlit as st

st.set_page_config(page_title="NomOS Compliance Gate", page_icon="⚖️", layout="wide")

st.title("⚖️ NomOS Compliance Gate")
st.subheader("AI-Mitarbeiter gesetzeskonform einstellen")

st.markdown("""
### 8-Step Wizard
1. Agent-Identitaet
2. Risiko-Einstufung (Art. 6)
3. DSGVO (DPIA, Art. 30, AVV)
4. AI Act (Art. 50, 14, 12)
5. Killswitch-Policy
6. Technische Config
7. Agent-Config (SOUL.md, Skills)
8. Compliance-Paket (SHA-256 Hash Chain)
""")

st.info("Coming soon — NomOS Compliance Gate v0.1.0")
