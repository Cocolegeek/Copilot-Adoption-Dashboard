import streamlit as st
import pandas as pd
from datetime import datetime, timedelta



st.set_page_config(page_title="Copilot M365 - Adoption Dashboard", layout="wide")

st.logo(
    "Microsoft_Copilot_Icon.png",
    size="large",
    link="http://localhost:8501/"
)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b1220;
        background-image:
            radial-gradient(at 29% 74%, hsla(257,85%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 31% 83%, hsla(148,87%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 77% 7%, hsla(297,69%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 19% 18%, hsla(261,77%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 70% 36%, hsla(10,87%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 5% 0%, hsla(85,72%,60%,0.3) 0px, transparent 50%),
            radial-gradient(at 59% 57%, hsla(191,76%,60%,0.3) 0px, transparent 50%);
        background-size: 150% 150%;
        animation: meshGradient 10s ease infinite;
    }

    @keyframes meshGradient {
        0% { background-position: 0% 0%; }
        25% { background-position: 100% 0%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
        100% { background-position: 0% 0%; }
    }

           background: rgba(0, 0, 0, 0.6);  /* Voile sombre sur les blocs */
        padding: 1rem;
        border-radius: 10px;
    }

    h1, h2, h3 {
        color: #6ea8fe;
    }

    .stButton>button {
        background-color: #6ea8fe;
        color: white;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)
# Menu latéral simplifié
with st.sidebar:
    
    st.markdown("""
        <style>
        body {
            background-color: #0b1220;
            color: #f0f0f0;
            background-image: url("Microsoft_Copilot_Icon.png");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }
        .block-container {
            padding-top: 2rem;
        }
        h1, h2, h3 {
            color: #6ea8fe;
        }
        .stButton>button {
            background-color: #6ea8fe;
            color: white;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)


    # Custom menu with buttons
    menu_options = ["Dashboard", "Logs utilisateur"]
    if "page" not in st.session_state:
        st.session_state["page"] = menu_options[0]

    for option in menu_options:
        if st.button(
            option,
            key=f"menu_{option}",
            help=f"Aller à {option}",
            use_container_width=True
        ):
            st.session_state["page"] = option

        # Add custom style for selected
        st.markdown(
            f"""
            <script>
            var btn = window.parent.document.querySelectorAll('button[kind="secondary"]')[{menu_options.index(option)}];
            if (btn) {{
                btn.classList.add('sidebar-menu-item');
                {"btn.classList.add('selected');" if st.session_state["page"] == option else ""}
            }}
            </script>
            """,
            unsafe_allow_html=True
        )

    page = st.session_state["page"]

st.title("Dashboard Adoption Copilot")

# Initialisation session
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(columns=["UPN", "Activity date"])

# Onglet Dashboard
if page == "Dashboard":
    st.header("Importer vos fichiers")
    uploaded_files = st.file_uploader(
        "Glissez-déposez vos fichiers Copilot (export admin M365, .csv)", 
        type="csv", accept_multiple_files=True
    )

    if uploaded_files:
        dfs = []
        for file in uploaded_files:
            try:
                df = pd.read_csv(file, skiprows=1)
                df = df[["UPN", "Activity date"]].dropna()
                dfs.append(df)
            except Exception as e:
                st.error(f"Erreur de lecture du fichier {file.name}: {e}")
        if dfs:
            new_data = pd.concat(dfs)
            combined = pd.concat([st.session_state["data"], new_data])
            combined.drop_duplicates(subset=["UPN", "Activity date"], inplace=True)
            st.session_state["data"] = combined
            st.success(f"{len(new_data)} lignes importées. Total: {len(st.session_state['data'])} lignes uniques.")

    data = st.session_state["data"]
    if not data.empty:
        st.header("Statistiques")
        data["Activity date"] = pd.to_datetime(data["Activity date"], errors="coerce")
        now = data["Activity date"].max()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)
        last_180_days = now - timedelta(days=180)

        total_users = data["UPN"].nunique()
        active_7d = data[data["Activity date"] >= last_7_days]["UPN"].nunique()
        active_30d = data[data["Activity date"] >= last_30_days]["UPN"].nunique()
        active_180d = data[data["Activity date"] >= last_180_days]["UPN"].nunique()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Utilisateurs distincts", total_users)
        col2.metric("Actifs 7j", active_7d)
        col3.metric("Actifs 30j", active_30d)
        col4.metric("Actifs 180j", active_180d)

        st.subheader("Évolution des actifs (90 derniers jours)")
        daily_counts = data[data["Activity date"] >= last_90_days].groupby("Activity date")["UPN"].nunique()
        
        chart = st.line_chart(
            daily_counts,
            use_container_width=True,
            height=400
        )

        # Onglet Classement des utilisateurs inactifs
        with st.expander("🏆 Top 100 utilisateurs les plus inactifs"):
            st.subheader("Classement des 100 utilisateurs avec la date de dernière activité la plus ancienne")
            last_activity = data.groupby("UPN")["Activity date"].max().reset_index()
            last_activity["Jours depuis dernière activité"] = (now - last_activity["Activity date"]).dt.days.astype('Int64')
            classement = last_activity.sort_values("Activity date").head(100)
            classement = classement.rename(columns={"Activity date": "Dernière activité"})
            classement = classement[["UPN", "Dernière activité", "Jours depuis dernière activité"]]

            # Appliquer une mise en forme conditionnelle (jaune -> rouge, plus c'est élevé plus c'est rouge)
            def color_gradient(val, min_val, max_val):
                if pd.isnull(val):
                    return ""
                ratio = (val - min_val) / (max_val - min_val) if max_val > min_val else 0
                # Inverser le ratio pour que plus c'est élevé, plus c'est rouge
                ratio = 1 - ratio
                r = 255
                g = int(255 * ratio)
                b = 0
                return f"background-color: rgba({r},{g},{b},0.15);"

            min_days = classement["Jours depuis dernière activité"].min()
            max_days = classement["Jours depuis dernière activité"].max()
            styled = classement.style.apply(
                lambda s: [color_gradient(v, min_days, max_days) if s.name == "Jours depuis dernière activité" else "" for v in s],
                axis=0
            )

            st.dataframe(styled, use_container_width=True)
            st.download_button(
            label="Exporter le classement (CSV)",
            data=classement.to_csv(index=False).encode("utf-8"),
            file_name="classement_inactifs.csv",
            mime="text/csv"
            )

# Onglet Logs utilisateur
elif page == "Logs utilisateur":
    st.header("Logs détaillés par utilisateur")
    data = st.session_state["data"]
    if not data.empty:
        data["Activity date"] = pd.to_datetime(data["Activity date"])
        users = data["UPN"].unique()
        default_user = "corentin.nicolas@vinci-energies.net"
        selected_user = st.selectbox(
            "Sélectionnez un utilisateur",
            users,
            index=list(users).index(default_user) if default_user in users else 0
        )
        user_logs = data[data["UPN"] == selected_user].sort_values("Activity date", ascending=False)
        st.write(f"Activités pour {selected_user} ({len(user_logs)} entrées):")
        st.dataframe(user_logs)
        st.download_button(
            label="Exporter les logs utilisateur (CSV)",
            data=user_logs.to_csv(index=False).encode("utf-8"),
            file_name=f"logs_{selected_user}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aucune donnée importée pour le moment.")