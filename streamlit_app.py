import streamlit as st
import pandas as pd

# 1. Load Data (update with your actual CSV filename)
st.title("LinkedIn Job Explorer (Multi-Industry, Persona-Powered)")

uploaded = st.file_uploader("Upload your 'linkedin_job_postings.csv' file", type="csv")
if uploaded is not None:
    df = pd.read_csv(uploaded)
    df = df.fillna("")
else:
    st.warning("Please upload the dataset to continue.")
    st.stop()

# 2. Define Broader Personas (can always edit these later)
personas = {
    "Data Scientist / Analyst": ["data analyst", "data science", "statistics", "analytics", "python", "r"],
    "Software/IT Professional": ["developer", "software", "programming", "engineer", "it", "network"],
    "Marketing & Sales": ["marketing", "sales", "seo", "business development", "advertising"],
    "Finance & Accounting": ["finance", "accountant", "accounting", "cpa", "auditor", "budgeting"],
    "Operations & Logistics": ["operations", "logistics", "supply chain", "warehouse", "inventory"],
    "Customer Service": ["customer service", "support", "representative", "call center"],
    "Human Resources": ["hr", "human resources", "recruiter", "talent", "recruitment"],
    "Healthcare Professional": ["nurse", "doctor", "physician", "medical", "healthcare", "clinic"],
    "Education & Teaching": ["teacher", "teaching", "instructor", "education", "professor"],
    "Design & Creative": ["designer", "creative", "graphic", "ui", "ux", "visual"],
    "Legal": ["lawyer", "attorney", "legal", "counsel", "paralegal"],
    "Construction & Real Estate": ["construction", "real estate", "property", "site manager"],
    "Administration": ["admin", "administrative", "office", "executive assistant"],
    "Custom": []
}

# 3. Streamlit UI
st.title("LinkedIn Job Explorer (Multi-Industry, Persona-Powered)")
st.write("Find jobs tailored for your career path or interests.")

# Persona selection
persona_choice = st.selectbox("Select a career persona:", list(personas.keys()))

if persona_choice == "Custom":
    user_keywords = st.text_input("Enter custom keywords (comma-separated):")
    keywords = [k.strip().lower() for k in user_keywords.split(",") if k.strip()]
else:
    keywords = personas[persona_choice]
    st.info(f"Using keywords for **{persona_choice}**: {', '.join(keywords)}")
    user_keywords = st.text_input("Optionally add extra keywords to refine (comma-separated):")
    extra_keywords = [k.strip().lower() for k in user_keywords.split(",") if k.strip()]
    if extra_keywords:
        keywords += extra_keywords

# 4. Extra Filters (Location, Company, Work Type, Experience Level)
with st.expander("More filters"):
    location_options = sorted({loc for loc in df["location"].unique() if loc})
    selected_locations = st.multiselect("Job Location(s):", location_options)
    company_options = sorted({comp for comp in df["company_name"].unique() if comp})
    selected_companies = st.multiselect("Company(s):", company_options)
    work_type_options = sorted({wt for wt in df["formatted_work_type"].unique() if wt})
    selected_work_types = st.multiselect("Work Type(s):", work_type_options)
    experience_options = sorted({exp for exp in df["formatted_experience_level"].unique() if exp})
    selected_experiences = st.multiselect("Experience Level(s):", experience_options)

# 5. Filtering Logic (uses correct columns!)
def row_matches_keywords(row, keywords):
    haystack = " ".join([
        str(row["title"]),
        str(row["description"]),
        str(row["skills_desc"])
    ]).lower()
    return any(kw in haystack for kw in keywords)

if keywords:
    filtered_df = df[df.apply(lambda row: row_matches_keywords(row, keywords), axis=1)]
else:
    filtered_df = df.copy()

if selected_locations:
    filtered_df = filtered_df[filtered_df["location"].isin(selected_locations)]
if selected_companies:
    filtered_df = filtered_df[filtered_df["company_name"].isin(selected_companies)]
if selected_work_types:
    filtered_df = filtered_df[filtered_df["formatted_work_type"].isin(selected_work_types)]
if selected_experiences:
    filtered_df = filtered_df[filtered_df["formatted_experience_level"].isin(selected_experiences)]

# 6. Grouping & Display (adjusted grouping columns)
groupby_option = st.selectbox(
    "Group results by:",
    ["None", "location", "company_name", "formatted_work_type", "formatted_experience_level"]
)

display_cols = [
    "title",
    "company_name",
    "location",
    "formatted_work_type",
    "formatted_experience_level",
    "skills_desc",
    "description",
    "job_posting_url"
]

if filtered_df.empty:
    st.warning("No jobs found for these criteria. Try adjusting keywords or filters.")
else:
    st.success(f"Found {filtered_df.shape[0]} matching jobs.")

    if groupby_option == "None":
        st.dataframe(filtered_df[display_cols].head(50))
    else:
        for group, group_df in filtered_df.groupby(groupby_option):
            st.subheader(f"{groupby_option.replace('_', ' ').title()}: {group} ({len(group_df)})")
            st.dataframe(group_df[display_cols].head(10))

# 7. Download Results
if not filtered_df.empty:
    st.download_button(
        label="Download these results as CSV",
        data=filtered_df[display_cols].to_csv(index=False),
        file_name="filtered_jobs.csv"
    )
