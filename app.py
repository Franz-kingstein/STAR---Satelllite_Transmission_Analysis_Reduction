import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
import matplotlib.pyplot as plt
import math

st.set_page_config(page_title="Hipparcos Explorer", layout="wide")
st.title("Hipparcos Star Catalog Explorer")

# Connect to MongoDB with clear errors
@st.cache_resource
def get_collection(uri="mongodb://localhost:27017/", db_name="hippparcos_db", coll="stars"):
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")  # raises if not reachable
    return client[db_name][coll]

collection = None
error = None
try:
    collection = get_collection()
except ServerSelectionTimeoutError as e:
    error = f"MongoDB not reachable on 27017. Start Docker container 'mongodb'. Details: {e}"
except Exception as e:
    error = f"MongoDB error: {e}"

if error:
    st.error(error)
    st.stop()

# Metrics
c1, c2 = st.columns(2)
with c1:
    total = collection.count_documents({})
    st.metric("Total Stars", f"{total:,}")
with c2:
    with_dist = collection.count_documents({'Distance_pc': {'$ne': None}})
    st.metric("Stars with Distance", f"{with_dist:,}")

# Top spectral types
st.subheader("Top 10 Spectral Types")
pipeline = [
    {"$match": {"SpType": {"$ne": None}, "Vmag": {"$ne": None}}},
    {"$group": {"_id": "$SpType", "count": {"$sum": 1}, "avgVmag": {"$avg": "$Vmag"}}},
    {"$sort": {"count": -1}},
    {"$limit": 10},
]
df = pd.DataFrame(list(collection.aggregate(pipeline))).rename(
    columns={"_id": "Spectral Type", "count": "Count", "avgVmag": "Avg Vmag"}
)
st.dataframe(df, use_container_width=True)

# HR diagram
st.subheader("Hertzsprung–Russell Diagram")
sample_size = st.slider("Sample size", 1000, 30000, 10000, 1000)

cursor = collection.find(
    {"Distance_pc": {"$ne": None}, "Vmag": {"$ne": None}, "B-V": {"$ne": None}},
    {"Vmag": 1, "B-V": 1, "Distance_pc": 1, "_id": 0},
).limit(sample_size)

hr = list(cursor)
bv = []
Mv = []
for s in hr:
    d = s.get("Distance_pc")
    if d and d > 0:
        bv.append(s["B-V"])
        Mv.append(s["Vmag"] - 5 * math.log10(d) + 5)

fig, ax = plt.subplots(figsize=(8, 10))
ax.scatter(bv, Mv, s=2, alpha=0.5, c="black")
ax.invert_yaxis()
ax.set_xlabel("B-V (Color Index)")
ax.set_ylabel("Absolute Magnitude (Mv)")
ax.set_title("HR Diagram (sample)")
ax.grid(True, ls="--", alpha=0.4)
st.pyplot(fig)