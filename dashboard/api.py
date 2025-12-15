"""
Flask API pour West Africa Ports Dashboard
✅ Decimal CORRIGÉ (conversion avant JSON)
✅ Groq réponses complètes fluides
✅ Serveur frontend React intégré
"""

from flask import Flask, jsonify, request, send_from_directory
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
from pathlib import Path

load_dotenv()

# Configuration Flask avec dossier statique du frontend
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'),
    static_url_path=''
)
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
    return jsonify({
        "status": "ok",
        "message": "API du tableau de bord des ports d'Afrique de l'Ouest",
        "endpoints": {
            "health": "GET /api/health",
            "summary": "GET /api/ports/summary",
            "comparison": "GET /api/ports/comparison",
            "trends": "GET /api/ports/trends",
            "chat": "POST /api/groq/chat",
            "insights": "GET /api/groq/insights"
        }
    })

@app.route('/api/ports/summary', methods=['GET'])
def ports_summary():
    """Résumé ports"""
    data = get_cached_data()
    return jsonify(data['summary'])

@app.route('/api/ports/comparison', methods=['GET'])
def ports_comparison():
    """Comparaison ports"""
    data = get_cached_data()
    return jsonify(data['comparison'])

@app.route('/api/ports/trends', methods=['GET'])
def ports_trends():
    """Tendances ports"""
    data = get_cached_data()
    return jsonify(data['trends'])

@app.route('/api/groq/insights', methods=['GET'])
def groq_insights():
    """Génère insights IA"""
    try:
        data = get_cached_data()
        prompt = f"""Analysez ces données de ports d'Afrique de l'Ouest et donnez 3 insights clés:
        {json.dumps(data['comparison'][:5])}
        
        Répondez UNIQUEMENT avec 3 points clés, sans liste numérotée."""
        
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        text = response.choices[0].message.content
        insights = [s.strip() for s in text.split('\n') if s.strip()][:3]
        
        return jsonify({"insights": insights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groq/chat', methods=['POST'])
def groq_chat():
    """Chat IA avec Groq"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "Message vide"}), 400
        
        # Contexte données
        cache_data = get_cached_data()
        context = f"Vous êtes expert en logistique portuaire. Voici les données: {json.dumps(cache_data['comparison'][:5])}"
        
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        reply = response.choices[0].message.content
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SERVIR LE FRONTEND REACT
# ============================================================================

@app.route('/', methods=['GET'])
def serve_index():
    """Servir index.html du frontend"""
    dist_folder = app.static_folder
    if os.path.exists(os.path.join(dist_folder, 'index.html')):
        return send_from_directory(dist_folder, 'index.html')
    return jsonify({"message": "Frontend not built. Run: cd frontend && npm run build"}), 404

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Servir fichiers statiques ou rediriger vers index.html (React Router)"""
    dist_folder = app.static_folder
    file_path = os.path.join(dist_folder, path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(dist_folder, path)
    
    # Fallback vers index.html pour React Router
    if os.path.exists(os.path.join(dist_folder, 'index.html')):
        return send_from_directory(dist_folder, 'index.html')
    
    return jsonify({"error": "Not found"}), 404

# ============================================================================
# DÉMARRAGE
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)