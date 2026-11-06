import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dashboard Bike Sharing", page_icon="🚲", layout="wide")
sns.set_theme(style="whitegrid")

BASE = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    day = pd.read_csv(os.path.join(BASE, "main_data.csv"), parse_dates=["dteday"])
    hour = pd.read_csv(os.path.join(BASE, "hour_data.csv"), parse_dates=["dteday"])
    return day, hour

day_df, hour_df = load_data()

# ---------- Sidebar ----------
st.sidebar.header("🔎 Filter Data")
min_date, max_date = day_df["dteday"].min().date(), day_df["dteday"].max().date()
rentang = st.sidebar.date_input("Rentang tanggal", value=(min_date, max_date),
                                min_value=min_date, max_value=max_date)
if len(rentang) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()
start, end = pd.to_datetime(rentang[0]), pd.to_datetime(rentang[1])

musim = st.sidebar.multiselect("Musim", sorted(day_df["season"].unique()),
                               default=sorted(day_df["season"].unique()))
cuaca_opsi = ["Cerah", "Berkabut/Berawan", "Hujan/Salju"]
cuaca = st.sidebar.multiselect("Cuaca", cuaca_opsi, default=cuaca_opsi)

d = day_df[day_df["dteday"].between(start, end) & day_df["season"].isin(musim) & day_df["cuaca"].isin(cuaca)]
h = hour_df[hour_df["dteday"].between(start, end) & hour_df["season"].isin(musim) & hour_df["cuaca"].isin(cuaca)]

st.title("🚲 Dashboard Analisis Bike Sharing (2011–2012)")
st.caption("Sumber data: Capital Bikeshare, Washington D.C.")

if d.empty or h.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ---------- Metrik ----------
c1, c2, c3 = st.columns(3)
c1.metric("Total Penyewaan", f"{d['cnt'].sum():,}")
c2.metric("Rata-rata Penyewaan per Hari", f"{d['cnt'].mean():,.0f}")
c3.metric("Jumlah Hari", f"{len(d):,}")

# ---------- Pertanyaan 1 ----------
st.subheader("Pertanyaan 1: Pola Penyewaan per Jam, Hari Kerja vs Hari Libur")
pola = h.groupby(["hari", "hr"])["cnt"].mean().reset_index()
warna = {"Hari Kerja": "#1f77b4", "Hari Libur/Akhir Pekan": "#ff7f0e"}
fig, ax = plt.subplots(figsize=(11, 4.5))
for nama, g in pola.groupby("hari"):
    ax.plot(g["hr"], g["cnt"], marker="o", linewidth=2, label=nama, color=warna[nama])
    top = g.loc[g["cnt"].idxmax()]
    ax.annotate(f"Puncak {int(top['hr'])}:00\n({top['cnt']:.0f})", (top["hr"], top["cnt"]),
                textcoords="offset points", xytext=(0, 12), ha="center", fontsize=9, color=warna[nama])
ax.set_xticks(range(0, 24)); ax.set_xlabel("Jam"); ax.set_ylabel("Rata-rata penyewaan per jam")
ax.legend(); sns.despine()
st.pyplot(fig)

# ---------- Pertanyaan 2 ----------
st.subheader("Pertanyaan 2: Dampak Cuaca terhadap Penyewaan Harian")
col_a, col_b = st.columns(2)
urut = [c for c in cuaca_opsi if c in d["cuaca"].unique()]
rata = d.groupby("cuaca")["cnt"].mean().reindex(urut)
with col_a:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    palet = {"Cerah": "#1f77b4", "Berkabut/Berawan": "#9ecae1", "Hujan/Salju": "#d62728"}
    bars = ax.bar(rata.index, rata.values, color=[palet[c] for c in rata.index])
    for b, v in zip(bars, rata.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Rata-rata penyewaan per hari"); ax.set_xlabel(""); sns.despine()
    st.pyplot(fig)
    if "Cerah" in rata.index:
        for k in rata.index:
            if k != "Cerah":
                st.write(f"Penurunan **{k}** vs Cerah: **{(1 - rata[k] / rata['Cerah']) * 100:.1f}%**")
with col_b:
    pv = d.pivot_table(index="season", columns="cuaca", values="cnt", aggfunc="mean").reindex(columns=urut)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.heatmap(pv, annot=True, fmt=".0f", cmap="Blues", cbar=False, ax=ax)
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.set_title("Rata-rata penyewaan harian (musim x cuaca)", fontsize=10)
    st.pyplot(fig)
st.caption("⚠️ Hari hujan/salju hanya 21 hari (2011–2012), sehingga hasil per musim perlu dibaca hati-hati.")

# ---------- Analisis lanjutan ----------
st.subheader("Analisis Lanjutan: Binning Suhu dan Kategori Permintaan")
urut_suhu = ["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-30°C)", "Panas (>30°C)"]
ct = pd.crosstab(d["kategori_suhu"], d["kategori_permintaan"], normalize="index") * 100
ct = ct.reindex(index=[x for x in urut_suhu if x in ct.index],
                columns=[x for x in ["Rendah", "Sedang", "Tinggi"] if x in ct.columns])
fig, ax = plt.subplots(figsize=(9, 4))
ct.plot(kind="barh", stacked=True, ax=ax, color=["#d62728", "#bdbdbd", "#1f77b4"])
ax.set_xlabel("Persentase hari (%)"); ax.set_ylabel(""); ax.legend(title="Permintaan", bbox_to_anchor=(1, 1))
sns.despine()
st.pyplot(fig)
