"""
WEST AFRICA PORTS DASHBOARD - PHASE 1: GROQ CHAT
Créé pour : Master 2 IA & Big Data - Port Autonome de Cotonou
Objectif : Dashboard "Océan Bleu" avec IA Conversationnelle

Installation:
  pip install streamlit plotly pandas psycopg2-binary python-dotenv anthropic

Exécution:
  streamlit run app_v2.py

Fonctionnalités Phase 1:
- Chat conversationnel avec Claude AI
- Function calling pour SQL queries
- Graphiques générés dynamiquement
- 5 questions prédéfinies
- Insights business avec contexte géopolitique
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
import anthropic
import json
import re

# ============================================================================
# CONFIGURATION & CACHE
# ============================================================================

load_dotenv()

st.set_page_config(
    page_title="West Africa Ports - Ocean Blue",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Océan Bleu
st.markdown("""
<style>
    .chat-container {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%);
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid #00bfff;
        margin: 10px 0;
    }
    
    .user-message {
        background: linear-gradient(135deg, #0066cc 0%, #003d99 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-radius: 10px 0px 10px 10px;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #e6f2ff 0%, #ffffff 100%);
        color: #003d99;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-radius: 0px 10px 10px 10px;
        border-left: 4px solid #00bfff;
    }
    
    .quick-button {
        background: linear-gradient(135deg, #00bfff 0%, #0066cc 100%);
        color: white !important;
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .quick-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
    }
    
    .insight-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f8ff 100%);
        border-left: 4px solid #00bfff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
    }
    
    h1, h2 {
        color: #003d99;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid #00bfff;
        color: #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

@st.cache_resource
def get_db_connection():
    """Crée connexion PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'ports_dashboard'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur BD: {str(e)[:100]}")
        return None

@st.cache_data(ttl=3600)
def load_data(query):
    """Charge données avec cache 1h"""
    try:
        conn = get_db_connection()
        if conn:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ Erreur requête: {str(e)[:100]}")
        return pd.DataFrame()

def execute_query(query):
    """Exécute requête et retourne résultats"""
    try:
        conn = get_db_connection()
        if conn:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ============================================================================
# GROQ/CLAUDE API FUNCTIONS
# ============================================================================

@st.cache_resource
def init_claude_client():
    """Initialise client Claude API"""
    return anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))

def generate_sql_query(question: str, context: str) -> str:
    """
    Claude génère une requête SQL basée sur la question
    Utilise function calling pour générer du SQL sûr
    """
    client = init_claude_client()
    
    prompt = f"""
    Tu es un expert SQL pour une base de données PostgreSQL contenant des données de ports d'Afrique de l'Ouest.
    
    CONTEXTE DATABASE:
    - Tables disponibles:
      * public_marts.mart_port_annual_summary (port_code, port_name, year, total_tonnage_mt, total_teus)
      * public_marts.mart_port_comparison (port_code, port_name, year, total_tonnage_mt, tonnage_market_share_pct, total_teus, teu_market_share_pct)
      * public_marts.mart_port_trends (port_code, port_name, year, total_tonnage_mt, tonnage_yoy_pct, total_teus)
      * public_marts.mart_data_quality (port_code, port_name, year, tonnage_coverage_pct, quality_level)
    
    - Ports disponibles: ABIDJAN, LOME, PAC, TEMA
    - Années: 2020-2024
    
    QUESTION UTILISATEUR: {question}
    
    Génère une requête SQL PostgreSQL valide pour répondre à cette question.
    Retourne UNIQUEMENT la requête SQL, sans explications.
    La requête doit être robuste et inclure ORDER BY si approprié.
    """
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        sql_text = message.content[0].text.strip()
        # Nettoie si Claude ajoute des backticks
        sql_text = sql_text.replace("```sql", "").replace("```", "").strip()
        return sql_text
    except Exception as e:
        st.error(f"❌ Erreur génération SQL: {str(e)[:100]}")
        return ""

def get_claude_insights(question: str, data_context: str) -> str:
    """
    Claude analyse les données et génère insights avec contexte business
    """
    client = init_claude_client()
    
    prompt = f"""
    Tu es un analyste stratégique pour les ports d'Afrique de l'Ouest, expert en :
    - Logistique portuaire et commerce maritime
    - Géopolitique régionale (Bénin, Ghana, Côte d'Ivoire, Togo)
    - Stratégie business et compétitivité
    
    QUESTION UTILISATEUR: {question}
    
    DONNÉES CONTEXTUELLES:
    {data_context}
    
    CONTEXTE BUSINESS:
    - Ports majeurs: Abidjan (Côte d'Ivoire), Tema (Ghana), Lomé (Togo), PAC (Bénin)
    - Abidjan: Infrastructure moderne, hinterland étendu (Mali, Burkina, Niger)
    - Tema: Spécialisé conteneurs (TEU), proche capital Accra
    - Lomé: Hub régional, en croissance rapide
    - PAC Cotonou: Vulnérable, doit se différencier
    
    Fournis une analyse RICHE qui :
    1. Répond directement à la question avec données
    2. Ajoute contexte géopolitique/business
    3. Identifie patterns et tendances
    4. Propose recommandations stratégiques
    5. Reste concis (max 300 mots)
    
    Format: Utilise **gras** pour les points clés et emojis pour clarté.
    """
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"⚠️ Erreur analyse: {str(e)[:100]}"

def generate_chart_data(df: pd.DataFrame, chart_type: str) -> go.Figure | None:
    """
    Génère graphique Plotly basé sur les données
    """
    if df.empty:
        return None
    
    try:
        if chart_type == "line_time":
            # Graphique temporal
            fig = px.line(
                df,
                x=df.columns[0],
                y=df.columns[1],
                markers=True,
                title=f"Évolution: {df.columns[1]}"
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
        
        elif chart_type == "bar_comparison":
            # Comparaison ports
            fig = px.bar(
                df,
                x=df.columns[0],
                y=df.columns[1],
                color=df.columns[0],
                title=f"Comparaison: {df.columns[1]}"
            )
            fig.update_layout(showlegend=False)
        
        elif chart_type == "heatmap":
            # Heatmap
            if len(df.columns) >= 2:
                fig = px.imshow(
                    df,
                    color_continuous_scale='RdYlGn',
                    title="Heatmap Analyse"
                )
        
        else:
            # Default: scatter
            fig = px.scatter(
                df,
                x=df.columns[0],
                y=df.columns[1],
                title="Analyse"
            )
        
        # Styling océan bleu
        fig.update_layout(
            plot_bgcolor='rgba(240,248,255,0.5)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color='#003d99'),
            title_font_size=16,
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        return None

# ============================================================================
# QUESTIONS PRÉDÉFINIES
# ============================================================================

PREDEFINED_QUESTIONS = {
    "📈 Quel port a la meilleure croissance ?": {
        "sql": """
            SELECT port_code, port_name, year, tonnage_yoy_pct
            FROM public_marts.mart_port_trends
            WHERE year >= 2023
            ORDER BY tonnage_yoy_pct DESC
            LIMIT 10
        """,
        "chart_type": "bar_comparison"
    },
    "🥊 Compare Lomé vs Abidjan sur 2024": {
        "sql": """
            SELECT port_code, port_name, 
                   total_tonnage_mt, total_teus, 
                   tonnage_market_share_pct
            FROM public_marts.mart_port_comparison
            WHERE port_code IN ('LOME', 'ABIDJAN')
            AND year = 2024
        """,
        "chart_type": "bar_comparison"
    },
    "⚠️ Pourquoi PAC perd des parts de marché ?": {
        "sql": """
            SELECT port_code, year, tonnage_market_share_pct
            FROM public_marts.mart_port_comparison
            WHERE port_code = 'PAC'
            AND year >= 2020
            ORDER BY year
        """,
        "chart_type": "line_time"
    },
    "💪 Quelles sont les forces d'Abidjan ?": {
        "sql": """
            SELECT port_code, year, total_tonnage_mt, 
                   tonnage_market_share_pct, tonnage_rank
            FROM public_marts.mart_port_comparison
            WHERE port_code = 'ABIDJAN'
            AND year = (SELECT MAX(year) FROM public_marts.mart_port_comparison)
        """,
        "chart_type": "bar_comparison"
    },
    "🔮 Projections 2025 pour tous les ports": {
        "sql": """
            SELECT port_code, year, total_tonnage_mt
            FROM public_marts.mart_port_annual_summary
            WHERE year >= 2022
            ORDER BY port_code, year
        """,
        "chart_type": "line_time"
    }
}

# ============================================================================
# SESSION STATE
# ============================================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 30px 0;'>
    <h1>🌊 West Africa Ports Strategic Intelligence</h1>
    <p style='font-size: 16px; color: #0066cc;'>
        AI-Powered Analytics for Port Autonome de Cotonou
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "💬 Claude Chat",
    "🏆 Comparaison",
    "📈 Tendances",
    "✅ Qualité"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================

with tab1:
    st.markdown("## 📊 Vue d'ensemble des Ports")
    
    annual_df = load_data("""
        SELECT port_code, port_name, year, total_tonnage_mt, total_teus
        FROM public_marts.mart_port_annual_summary
        WHERE year BETWEEN 2020 AND 2024
        ORDER BY port_code, year
    """)
    
    if not annual_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tonnage = annual_df['total_tonnage_mt'].sum() / 1_000_000
            st.metric("📦 Tonnage Total", f"{total_tonnage:.1f}M t")
        
        with col2:
            total_teus = annual_df['total_teus'].sum() / 1_000_000
            st.metric("🚢 Conteneurs", f"{total_teus:.1f}M TEU")
        
        with col3:
            num_ports = annual_df['port_code'].nunique()
            st.metric("🌍 Ports", f"{num_ports}")
        
        with col4:
            st.metric("📅 Années", "5 (2020-2024)")
        
        st.markdown("---")
        
        fig = px.line(
            annual_df,
            x='year',
            y='total_tonnage_mt',
            color='port_code',
            markers=True,
            title="Évolution Tonnage par Port"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(240,248,255,0.5)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color='#003d99')
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: CLAUDE CHAT ⭐ FEATURE WOW
# ============================================================================

with tab2:
    st.markdown("## 💬 Posez des Questions sur les Ports d'Afrique de l'Ouest")
    
    st.markdown("""
    <div class='insight-card'>
    🤖 <b>Claude AI vous écoute!</b> Posez n'importe quelle question sur les ports.
    L'IA analyse les données en temps réel et génère graphiques dynamiques.
    </div>
    """, unsafe_allow_html=True)
    
    # Questions prédéfinies
    st.markdown("### 💡 Questions Prédéfinies (Click pour exécuter)")
    
    cols = st.columns(2)
    question_keys = list(PREDEFINED_QUESTIONS.keys())
    
    for idx, question in enumerate(question_keys):
        col = cols[idx % 2]
        with col:
            if st.button(question, key=f"btn_{idx}", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                st.rerun()
    
    st.markdown("---")
    
    # Chat conversationnel
    st.markdown("### 🗨️ Chat Conversationnel")
    
    # Affiche historique
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class='user-message'>
            👤 <b>Vous:</b> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='assistant-message'>
            🤖 <b>Claude:</b> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Affiche graphique si disponible
            if "chart" in msg and msg["chart"] is not None:
                st.plotly_chart(msg["chart"], use_container_width=True)
    
    # Input utilisateur
    st.markdown("---")
    
    user_input = st.text_input(
        "Votre question:",
        placeholder="Ex: Quel port domine le marché TEU ?",
        label_visibility="collapsed"
    )
    
    if user_input:
        # Ajoute question à historique
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Prépare contexte pour Claude
        context_df = load_data("""
            SELECT port_code, port_name, year, total_tonnage_mt, total_teus
            FROM public_marts.mart_port_annual_summary
            WHERE year = 2024
        """)
        
        data_context = context_df.to_string(index=False)
        
        # Génère SQL
        with st.spinner("🔄 Claude analyse votre question..."):
            sql_query = generate_sql_query(user_input, data_context)
            
            if sql_query:
                # Exécute requête
                result_df = execute_query(sql_query)
                
                # Génère insights
                insight = get_claude_insights(user_input, result_df.to_string(index=False))
                
                # Génère graphique si données
                chart = None
                if not result_df.empty and len(result_df.columns) >= 2:
                    chart = generate_chart_data(result_df, "line_time")
                
                # Ajoute réponse à historique
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": insight,
                    "chart": chart
                })
                
                st.rerun()

# ============================================================================
# TAB 3: COMPARAISON
# ============================================================================

with tab3:
    st.markdown("## 🏆 Comparaison Inter-Ports")
    
    comparison_df = load_data("""
        SELECT port_code, port_name, year, 
               total_tonnage_mt, tonnage_market_share_pct,
               total_teus
        FROM public_marts.mart_port_comparison
        WHERE year = 2024
    """)
    
    if not comparison_df.empty:
        fig = px.bar(
            comparison_df,
            x='port_code',
            y='total_tonnage_mt',
            color='port_code',
            title="Tonnage par Port (2024)"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(240,248,255,0.5)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color='#003d99'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 4: TENDANCES
# ============================================================================

with tab4:
    st.markdown("## 📈 Tendances (2020-2024)")
    
    trends_df = load_data("""
        SELECT port_code, year, total_tonnage_mt, tonnage_yoy_pct
        FROM public_marts.mart_port_trends
        WHERE year >= 2020
        ORDER BY port_code, year
    """)
    
    if not trends_df.empty:
        fig = px.line(
            trends_df,
            x='year',
            y='total_tonnage_mt',
            color='port_code',
            markers=True,
            title="Tonnage au fil du temps"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(240,248,255,0.5)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(color='#003d99')
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5: QUALITÉ
# ============================================================================

with tab5:
    st.markdown("## ✅ Qualité des Données")
    
    quality_df = load_data("""
        SELECT port_code, year, tonnage_coverage_pct, quality_level
        FROM public_marts.mart_data_quality
        WHERE year >= 2020
    """)
    
    if not quality_df.empty:
        st.info("📊 Couverture de données entre 50-100%")
        st.dataframe(quality_df, use_container_width=True, hide_index=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

st.markdown("""
<div style='text-align:center; color:#0066cc; padding:20px;'>
<small>🌊 West Africa Ports Dashboard | Claude AI Powered | Candidate: Master 2 IA & Big Data</small>
</div>
""", unsafe_allow_html=True)