# JCL Debt Terminal v2

> Bloomberg-style debt portfolio monitoring for Jindal Coke Limited.
> ₹3,410.7 Cr across 5 lenders · 34 facilities · 24 covenants · 3 term loans.

A complete rewrite of v1 with **60+ improvements**:
- 🔬 Stress-testing engine with sensitivity matrix & breach threshold finder
- 🤖 AI portfolio analyst (Anthropic Claude) — Q&A, narratives, email drafts
- 📊 Composite Health Score (covenant + maturity + concentration + rate-mix)
- 🏦 Per-lender one-pagers, board memo, compliance certificates (auto-generated `.docx`)
- 💱 Live FX feed (USD/INR) with graceful fallback
- 📈 Excel-first auto-sync with hardcoded fallback (dashboard never breaks)
- 🛡 Smart fixed-rate exclusion in stress tests (more realistic than v1)
- 🎨 Bloomberg Terminal aesthetic — amber/green/red on near-black, JetBrains Mono

---

## 🚀 Quickstart (local)

```bash
# 1. Clone
git clone https://github.com/divyanshuvatsa/jcl-debt-dashboard-v2.git
cd jcl-debt-dashboard-v2

# 2. Install
pip install -r requirements.txt

# 3. (Optional) Add Anthropic API key for AI features
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Then edit .streamlit/secrets.toml and paste your key

# 4. Run
streamlit run main.py
```

Open `http://localhost:8501`. The dashboard works **without** the API key — AI features simply show a setup prompt.

---

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub: `divyanshuvatsa/jcl-debt-dashboard-v2`
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → connect repo.
3. Set main file to `main.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy**. Done.

Subsequent pushes auto-redeploy.

---

## 📁 Project Structure

```
jcl-debt-dashboard-v2/
├── main.py                      # Entry point
├── requirements.txt
├── .streamlit/
│   ├── config.toml              # Bloomberg theme config
│   └── secrets.toml.example     # API key template (copy → secrets.toml)
├── data/
│   ├── jcl_data.py              # Hardcoded fallback (34 facilities, 24 covenants)
│   └── excel_loader.py          # Auto-sync from JCL_Debt_Model.xlsx
├── core/
│   └── financial_logic.py       # Calculation engine (covenants, scenarios, sensitivity)
├── services/
│   ├── live_data.py             # FX & SOFR feeds
│   ├── ai_assistant.py          # Anthropic API integration
│   └── exports.py               # Word doc generation
└── ui/
    ├── theme.py                 # Bloomberg CSS + Plotly template
    ├── components.py            # KPI tiles, alerts, ticker
    ├── charts.py                # Plotly charts (8 chart types)
    └── dashboard.py             # 7 tabs + sidebar
```

---

## 🎛 Features

### 7 Tabs
| Tab | Purpose |
|---|---|
| **📊 Overview** | Hero verdict + KPIs + health gauge + lender donut + AI commentary |
| **💰 Liquidity** | Maturity ladder + TL schedule + 365-day renewal calendar |
| **🛡 Covenants** | Headroom chart + status table + formula reference |
| **🔬 Scenarios** | Rate/EBITDA/debt sliders + sensitivity matrix + breach finder |
| **🤖 Ask AI** | Natural-language Q&A on the entire portfolio |
| **📊 Intel** | Health breakdown + lender risk scorecard + data quality |
| **📥 Export** | Board memo, lender one-pagers, compliance certs, email drafts, CSVs |

### Quick Scenario Buttons (Sidebar)
- **+100 bps** — parallel rate shock
- **Severe** — +200 bps + EBITDA -30% + debt +25%
- **EBITDA -20%** — earnings shock
- **Reset** — back to base case

---

## 🔄 Updating Data

The dashboard tries data sources in this order:
1. **Uploaded file** in current session (sidebar uploader)
2. **Local file** named `JCL_Debt_Model.xlsx` in repo root
3. **Hardcoded fallback** in `data/jcl_data.py` (always works)

To update facility/covenant data, edit `data/jcl_data.py` and commit.
The total is validated against **₹3,410.7 Cr** on every load.

---

## 🤝 Credits

Built by **Divyanshu Vatsa**, reviewed by **Paras Sir**.
Data source: JCL_Debt_Model.xlsx (sanction letters from RBL, YBL, Bajaj, ICICI, SIB).

---

## ⚠️ Disclaimer

For internal JCL use only. Not financial advice. Verify all figures against
sanction letters and audited financial statements before any commitment.
