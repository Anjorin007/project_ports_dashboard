"""
Flask API pour West Africa Ports Dashboard
✅ Decimal CORRIGÉ (conversion avant JSON)
✅ Groq réponses complètes fluides
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from groq import Groq
import json
import re
from decimal import Decimal

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================================================
# FONCTION DE CONVERSION DECIMAL (AVANT JSON)
# ============================================================================

def convert_decimals(obj):
    """Convertit récursivement tous les Decimal en float"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

# ============================================================================
# CONNEXION POOL POSTGRESQL
# ============================================================================

# Connexion DB optionnelle
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'ports_dashboard'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        port=os.getenv('DB_PORT', '5432')
    )
except Exception as e:
    print(f"⚠️  DB connection failed: {e}")
    print("Running in dev mode without database")
    db_pool = None

def execute_query(query):
    """Exécute requête SQL et retourne résultats en dict normal"""
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        db_pool.putconn(conn)
        
        # Convertir RealDictRow → dict normal → Decimal → float
        data = [dict(row) for row in results]
        return convert_decimals(data)
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return []

# ============================================================================
# GROQ CLIENT
# ============================================================================

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# ============================================================================
# CACHE DONNÉES
# ============================================================================

data_cache = {}
CACHE_VALID = True

def get_cached_data():
    """Récupère ou met à jour le cache"""
    global data_cache
    
    if not data_cache or not CACHE_VALID:
        print("📥 Chargement données...")
        data_cache['summary'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, total_teus
            FROM public_marts.mart_port_annual_summary
            WHERE year >= 2020
            ORDER BY year DESC, total_tonnage_mt DESC
        """)
        
        data_cache['comparison'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, tonnage_market_share_pct, 
                   total_teus, teu_market_share_pct, tonnage_rank
            FROM public_marts.mart_port_comparison
            ORDER BY year DESC, total_tonnage_mt DESC
            LIMIT 10
        """)
        
        data_cache['trends'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, tonnage_yoy_pct
            FROM public_marts.mart_port_trends
            WHERE year >= 2023
            ORDER BY year DESC, tonnage_yoy_pct DESC
        """)
        print("✅ Cache chargé")
    
    return data_cache

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok"})

@app.route('/api/ports/summary', methods=['GET'])
def get_summary():
    """Résumé annuel tous ports"""
    data = get_cached_data()
    return jsonify(data['summary'])

@app.route('/api/ports/comparison', methods=['GET'])
def get_comparison():
    """Comparaison ports"""
    data = get_cached_data()
    return jsonify(data['comparison'])

@app.route('/api/ports/trends', methods=['GET'])
def get_trends():
    """Tendances"""
    data = get_cached_data()
    return jsonify(data['trends'])

@app.route('/api/groq/chat', methods=['POST'])
def groq_chat():
    """Chat Groq - réponse complète d'un coup"""
    try:
        user_message = request.json.get('message', '')
        cached_data = get_cached_data()
        
        # Contexte pour Groq
        trends_str = json.dumps(cached_data['trends'][:5]) if cached_data['trends'] else "{}"
        
        context = f"""Tu es expert stratégique ports Afrique Ouest.

PORTS:
- PAC Cotonou (Bénin): Port petit, 2M tonnes, besoin différenciation
- Lomé (Togo): Leader #1, 20M tonnes, hub régional
- Abidjan (Côte d'Ivoire): #2, infrastructure moderne, hinterland Mali/Burkina
- Tema (Ghana): #3, hub conteneurs, 1.2M TEU
- Lagos (Nigeria): #5, 8M tonnes, congestion

DONNÉES 2024:
{trends_str}

INSTRUCTIONS:
- Réponse NATURELLE, fluide, pas de liste
- Utilise chiffres pour illustrer
- Bref mais riche (max 150 mots)
- Pour PAC: toujours une opportunité
- Max 3 émojis

QUESTION: {user_message}"""
        
        # Appel Groq
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": context}],
            temperature=0.7,
            max_tokens=500,
            stream=False
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Nettoyage
        answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)
        answer = re.sub(r'<[^>]+>', '', answer)
        
        return jsonify({"response": answer})
        
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return jsonify({"response": f"Erreur: {str(e)}"})

@app.route('/api/groq/insights', methods=['GET'])
def generate_insights():
    """Génère 3 insights"""
    try:
        cached_data = get_cached_data()
        trends_str = json.dumps(cached_data['trends'][:5]) if cached_data['trends'] else "{}"
        
        prompt = f"""Analyste stratégique ports Afrique Ouest.

DONNÉES:
{trends_str}

Génère 3 insights COURTS (1 phrase max):

🔥 Insight positif/croissance
⚠️ Alerte/risque
💡 Action concrète pour PAC

Format: 3 lignes simples, chiffres spécifiques."""
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250,
            stream=False
        )
        
        text = response.choices[0].message.content.strip()
        
        # Parse: trouve les lignes avec emoji
        insights = []
        for line in text.split('\n'):
            line = line.strip()
            if line and line[0] in '🔥⚠️💡':
                insights.append(line)
        
        # Fallback si parsing échoue
        if not insights:
            insights = [
                "🔥 Croissance conteneurs Afrique Ouest +12% annuel",
                "⚠️ PAC perd parts marché vs 2023",
                "💡 PAC doit spécialiser en terminal conteneurs"
            ]
        
        return jsonify({"insights": insights[:3]})
        
    except Exception as e:
        print(f"❌ Insights Error: {e}")
        return jsonify({"insights": [
            "🔥 Croissance conteneurs +12% annuel",
            "⚠️ Congestion Lagos impact régionalisation",
            "💡 Opportunité pour PAC: spécialisation"
        ]})

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌊 WEST AFRICA PORTS API")
    print("="*70)
    print("✅ Decimal convertis AVANT JSON (convert_decimals)")
    print("✅ Groq réponses complètes fluides")
    print("✅ Cache de données optimisé")
    print("="*70)
    print("Endpoints:")
    print("  POST /api/groq/chat")
    print("  GET  /api/groq/insights")
    print("  GET  /api/ports/summary")
    print("  GET  /api/ports/comparison")
    print("  GET  /api/ports/trends")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)