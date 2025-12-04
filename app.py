import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import requests
import os

st.set_page_config(page_title="Industry Emissions Dashboard", layout="wide")
st.title("Industry & Sector Emissions — HackForward 2025")
st.markdown("Dashboard visualizing emissions by industry + an interactive chat panel for questions & web lookups.")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("sample_data.csv")
    except Exception:
        sectors = ["Energy","Transport","Industry","Agriculture","Residential"]
        industries = ["Coal Power","Oil & Gas","Automobile","Steel","Cement","Fertilizer"]
        rows=[]
        for year in range(2015,2024):
            for s in sectors:
                for ind in industries:
                    rows.append({
                        "year": year,
                        "sector": s,
                        "industry": ind,
                        "emissions_mtco2": max(0, np.random.normal(50,20))
                    })
        df = pd.DataFrame(rows)
    return df

df = load_data()

st.sidebar.header("Filters")
years = sorted(df["year"].unique())
selected_year = st.sidebar.selectbox("Year", years, index=len(years)-1)
sectors = ["All"] + sorted(df["sector"].unique().tolist())
selected_sector = st.sidebar.selectbox("Sector", sectors)

filtered = df[df["year"]==selected_year]
if selected_sector != "All":
    filtered = filtered[filtered["sector"]==selected_sector]

st.subheader(f"Emissions — {selected_year} — Sector: {selected_sector}")
agg = filtered.groupby(["industry","sector"], as_index=False)["emissions_mtco2"].sum().sort_values("emissions_mtco2", ascending=False)

bar = alt.Chart(agg).mark_bar().encode(
    x=alt.X("emissions_mtco2:Q", title="Emissions (Mt CO2)"),
    y=alt.Y("industry:N", sort='-x', title="Industry"),
    tooltip=["industry","sector","emissions_mtco2"]
).properties(height=420)

st.altair_chart(bar, use_container_width=True)

st.write("Top industries by emissions")
st.dataframe(agg)

csv = agg.to_csv(index=False)
st.download_button("Download current data as CSV", csv, file_name=f"emissions_{selected_year}.csv", mime="text/csv")

st.markdown("---")
st.sidebar.header("Chat & Web Insights")
user_q = st.sidebar.text_input("Ask about the data or type web: <topic> for web lookup")

def simple_web_lookup(query: str) -> str:
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if "query" in data and data["query"]["search"]:
            title = data["query"]["search"][0]["title"]
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            s = requests.get(summary_url, timeout=8).json()
            return s.get("extract","No summary found.")
    except Exception as e:
        return f"Web lookup failed: {e}"
    return "No results found."

def dataset_answer(prompt: str) -> str:
    p = prompt.lower()
    if "which industry" in p or "most" in p:
        top = agg.iloc[0]
        return f"According to the dataset, {top['industry']} ({top['sector']}) has the highest emissions: {top['emissions_mtco2']:.2f} Mt CO2."
    if "total" in p or "sum" in p:
        return f"Total emissions in view: {agg['emissions_mtco2'].sum():.2f} Mt CO2."
    return "I can answer dataset questions (try 'Which industry emits most?') or use web: <topic> to fetch web info."

if user_q:
    if user_q.strip().lower().startswith("web:"):
        query = user_q.split("web:",1)[1].strip()
        st.sidebar.write(simple_web_lookup(query))
    else:
        st.sidebar.write(dataset_answer(user_q))

st.markdown("**Notes:** Replace sample_data.csv with official emissions data.")
