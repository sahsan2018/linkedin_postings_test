import streamlit as st
import pandas as pd
import sqlite3
import os

DB_URL = st.secrets.get("DB_URL")
DB_PATH = "linkedin_job_postings.db"
TABLE_NAME = "job_postings"

conn = None


def init_connection():
    if not os.path.exists(DB_PATH):
        st.info(
            "Database not found locally. Downloading from Google Drive (this may take a while)..."
        )
        try:
            import gdown

            gdown.download(DB_URL, DB_PATH, quiet=False)
        except Exception as e:
            st.error(f"Failed to download database: {e}")
            st.stop()
    return sqlite3.connect(DB_PATH)


# 2. Define Personas and run the app
def main():
    global conn
    conn = init_connection()

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

    st.title("LinkedIn Job Explorer (SQLite Powered)")
    st.write("Find jobs tailored for your career path or interests.")

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

    with st.expander("More filters"):
        location_options = get_unique("location")
        selected_locations = st.multiselect("Job Location(s):", location_options)
        company_options = get_unique("company_name")
        selected_companies = st.multiselect("Company(s):", company_options)
        work_type_options = get_unique("formatted_work_type")
        selected_work_types = st.multiselect("Work Type(s):", work_type_options)
        experience_options = get_unique("formatted_experience_level")
        selected_experiences = st.multiselect("Experience Level(s):", experience_options)

    # --- SQL Query Construction ---
    where_clauses = []
    params = []

    if keywords:
        kw_clause = "(" + " OR ".join(
            [f"LOWER(title) LIKE ?" for _ in keywords]
            + [f"LOWER(description) LIKE ?" for _ in keywords]
            + [f"LOWER(skills_desc) LIKE ?" for _ in keywords]
        ) + ")"
        where_clauses.append(kw_clause)
        params += [f"%{kw}%" for kw in keywords] * 3

    if selected_locations:
        placeholders = ",".join(["?"] * len(selected_locations))
        where_clauses.append(f"location IN ({placeholders})")
        params += selected_locations
    if selected_companies:
        placeholders = ",".join(["?"] * len(selected_companies))
        where_clauses.append(f"company_name IN ({placeholders})")
        params += selected_companies
    if selected_work_types:
        placeholders = ",".join(["?"] * len(selected_work_types))
        where_clauses.append(f"formatted_work_type IN ({placeholders})")
        params += selected_work_types
    if selected_experiences:
        placeholders = ",".join(["?"] * len(selected_experiences))
        where_clauses.append(f"formatted_experience_level IN ({placeholders})")
        params += selected_experiences

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    groupby_option = st.selectbox(
        "Group results by:",
        ["None", "location", "company_name", "formatted_work_type", "formatted_experience_level"],
    )

    display_cols = [
        "title",
        "company_name",
        "location",
        "formatted_work_type",
        "formatted_experience_level",
        "skills_desc",
        "description",
        "job_posting_url",
    ]

    LIMIT = 1000
    query = f"SELECT {', '.join(display_cols)} FROM {TABLE_NAME} {where} LIMIT {LIMIT}"
    df = pd.read_sql(query, conn, params=params)

    if df.empty:
        st.warning("No jobs found for these criteria. Try adjusting keywords or filters.")
    else:
        st.success(f"Found {df.shape[0]} matching jobs (showing up to {LIMIT}).")

        if groupby_option == "None":
            st.dataframe(df.head(50))
        else:
            for group, group_df in df.groupby(groupby_option):
                st.subheader(
                    f"{groupby_option.replace('_', ' ').title()}: {group} ({len(group_df)})"
                )
                st.dataframe(group_df.head(10))

        st.download_button(
            label="Download these results as CSV",
            data=df.to_csv(index=False),
            file_name="filtered_jobs.csv",
        )


def get_unique(col, connection=None, table_name=None):
    connection = connection or conn
    table_name = table_name or TABLE_NAME
    if connection is None:
        raise ValueError("Database connection not initialized")
    q = f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL AND {col} != ''"
    result = pd.read_sql(q, connection)[col].sort_values().tolist()
    return result


if __name__ == "__main__":
    main()
