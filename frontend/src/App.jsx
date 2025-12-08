import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ComposedChart } from 'recharts';
import { Send, Ship, Brain, Loader } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

const PortsDashboard = () => {
  const [currentPage, setCurrentPage] = useState('overview');
  const [summaryData, setSummaryData] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [trendsData, setTrendsData] = useState([]);
  const [insights, setInsights] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  const COLORS = {
    PAC: '#ef4444',
    LOME: '#06b6d4',
    ABIDJAN: '#3b82f6',
    TEMA: '#10b981',
    LAGOS: '#f59e0b'
  };

  const PORTS_INFO = {
    PAC: { name: 'Port Autonome de Cotonou', country: 'Bénin', rank: 4 },
    LOME: { name: 'Port Autonome de Lomé', country: 'Togo', rank: 1 },
    ABIDJAN: { name: 'Port Autonome d\'Abidjan', country: 'Côte d\'Ivoire', rank: 2 },
    TEMA: { name: 'Port of Tema', country: 'Ghana', rank: 3 },
    LAGOS: { name: 'Lagos Port Complex', country: 'Nigeria', rank: 5 }
  };

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Health check API
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(() => setApiStatus('connected'))
      .catch(() => setApiStatus('error'));
  }, []);

  // Charge données au démarrage
  useEffect(() => {
    if (apiStatus === 'connected') {
      Promise.all([
        fetch(`${API_BASE}/ports/summary`).then(r => r.json()),
        fetch(`${API_BASE}/ports/comparison`).then(r => r.json()),
        fetch(`${API_BASE}/ports/trends`).then(r => r.json()),
        fetch(`${API_BASE}/groq/insights`).then(r => r.json()),
      ]).then(([summary, comparison, trends, insightsRes]) => {
        setSummaryData(summary);
        setComparisonData(comparison);
        setTrendsData(trends);
        setInsights(insightsRes.insights || []);
      }).catch(err => console.error('Erreur chargement données:', err));
    }
  }, [apiStatus]);

  // Typing animation: fluide et naturelle
  const animateMessage = (fullText) => {
    return new Promise((resolve) => {
      let index = 0;
      const speed = 15; // ms par caractère
      
      const interval = setInterval(() => {
        index++;
        
        setChatMessages(prev => {
          const msgs = [...prev];
          const lastMsg = msgs[msgs.length - 1];
          lastMsg.content = fullText.substring(0, index);
          return msgs;
        });
        
        if (index >= fullText.length) {
          clearInterval(interval);
          resolve();
        }
      }, speed);
    });
  };

  // Envoie message
  const handleSendMessage = async (messageText = chatInput) => {
    const trimmed = messageText.trim();
    if (!trimmed) return;

    // Ajoute message user IMMÉDIATEMENT
    setChatMessages(prev => [...prev, { role: 'user', content: trimmed }]);
    setChatInput(''); // ⭐ VIDER L'INPUT D'ABORD
    setLoading(true);

    try {
      // Appel API
      const response = await fetch(`${API_BASE}/groq/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      const reply = data.response || '⚠️ Pas de réponse du serveur';
      
      // Ajoute message vide, puis anime
      setChatMessages(prev => [...prev, { role: 'assistant', content: '' }]);
      setLoading(false);
      
      // Lance animation
      await animateMessage(reply);

    } catch (error) {
      setLoading(false);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `❌ Erreur: ${error.message}` 
      }]);
    }
  };

  // Transformations données
  const allPorts = ['PAC', 'LOME', 'ABIDJAN', 'TEMA', 'LAGOS'];
  const comparison2024 = comparisonData.map(d => ({
    name: d.port_code,
    tonnage: parseFloat(d.total_tonnage_mt) / 1000000,
    marketShare: parseFloat(d.tonnage_market_share_pct),
    teu: parseFloat(d.total_teus) || 0
  }));

  const yearlyData = {};
  trendsData.forEach(d => {
    if (!yearlyData[d.year]) yearlyData[d.year] = {};
    yearlyData[d.year][d.port_code] = parseFloat(d.total_tonnage_mt) / 1000000;
  });
  const yearlyArray = Object.entries(yearlyData)
    .map(([y, d]) => ({ year: parseInt(y), ...d }))
    .sort((a, b) => a.year - b.year);

  const heatmapData = allPorts.map(port => ({
    port,
    ['2020']: trendsData.find(t => t.port_code === port && t.year === 2020)?.total_tonnage_mt / 1000000 || 0,
    ['2021']: trendsData.find(t => t.port_code === port && t.year === 2021)?.total_tonnage_mt / 1000000 || 0,
    ['2022']: trendsData.find(t => t.port_code === port && t.year === 2022)?.total_tonnage_mt / 1000000 || 0,
    ['2023']: trendsData.find(t => t.port_code === port && t.year === 2023)?.total_tonnage_mt / 1000000 || 0,
    ['2024']: trendsData.find(t => t.port_code === port && t.year === 2024)?.total_tonnage_mt / 1000000 || 0,
  }));

  const radarData = [
    { metric: 'Volume', PAC: 30, LOME: 95, ABIDJAN: 70, TEMA: 40, LAGOS: 65 },
    { metric: 'Croissance', PAC: 85, LOME: 25, ABIDJAN: 50, TEMA: 60, LAGOS: 45 },
    { metric: 'Efficacité', PAC: 72, LOME: 60, ABIDJAN: 65, TEMA: 80, LAGOS: 55 },
    { metric: 'Spécialisation', PAC: 60, LOME: 45, ABIDJAN: 50, TEMA: 95, LAGOS: 40 },
    { metric: 'Infrastructure', PAC: 50, LOME: 85, ABIDJAN: 90, TEMA: 75, LAGOS: 60 },
    { metric: 'Connectivité', PAC: 75, LOME: 70, ABIDJAN: 80, TEMA: 50, LAGOS: 65 },
  ];

  if (apiStatus === 'error') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)' }}>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <p style={{ color: '#ffffff', fontSize: '1.1rem' }}>API non disponible</p>
          <code style={{ color: '#06b6d4', marginTop: '1rem', display: 'block' }}>cd dashboard && python api.py</code>
        </div>
      </div>
    );
  }

  // PAGE 1: OVERVIEW
  const OverviewPage = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '3.5rem', fontWeight: 900, marginBottom: '0.5rem', color: '#ffffff' }}>🌊 West Africa Ports</h1>
        <p style={{ fontSize: '1.1rem', color: 'rgba(6, 182, 212, 0.8)' }}>Intelligence comparative • Stratégie • Prédictions 2025</p>
      </div>

      {/* KPI CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        {allPorts.map(port => {
          const data = comparison2024.find(d => d.name === port);
          return (
            <div key={port} style={{ 
              padding: '1.5rem', 
              borderRadius: '0.75rem', 
              borderLeft: `4px solid ${COLORS[port]}`,
              background: `linear-gradient(135deg, ${COLORS[port]}15 0%, transparent 100%)`,
              backdropFilter: 'blur(8px)'
            }}>
              <div style={{ fontSize: '0.8rem', color: 'rgba(6, 182, 212, 0.7)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.5rem' }}>
                {port} #{PORTS_INFO[port].rank}
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 900, color: COLORS[port], marginBottom: '0.5rem' }}>
                {data?.tonnage.toFixed(1) || '—'}M
              </div>
              <div style={{ fontSize: '0.85rem', color: 'rgba(6, 182, 212, 0.8)' }}>
                {data?.marketShare.toFixed(1) || '—'}% parts marché
              </div>
            </div>
          );
        })}
      </div>

      {/* CHART 1: TONNAGE */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>📊 Classement Tonnage 2024</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={comparison2024}>
            <CartesianGrid stroke="rgba(6, 182, 212, 0.1)" />
            <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis stroke="rgba(255, 255, 255, 0.5)" />
            <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(6, 182, 212, 0.5)', borderRadius: '0.5rem' }} />
            <Bar dataKey="tonnage" radius={[12, 12, 0, 0]}>
              {comparison2024.map((entry, idx) => <Cell key={idx} fill={COLORS[entry.name]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* CHART 2: MARKET SHARE */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>🥧 Parts de Marché Régionale</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={comparison2024} cx="50%" cy="50%" labelLine={false} label={e => `${e.name}: ${e.marketShare.toFixed(1)}%`} outerRadius={80} fill="#8884d8" dataKey="marketShare">
              {comparison2024.map((e, idx) => <Cell key={idx} fill={COLORS[e.name]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(6, 182, 212, 0.5)', borderRadius: '0.5rem' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* CHART 3: HISTORICAL TREND */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>📈 Évolution 2020-2024</h3>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={yearlyArray}>
            <CartesianGrid stroke="rgba(6, 182, 212, 0.1)" />
            <XAxis dataKey="year" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis stroke="rgba(255, 255, 255, 0.5)" />
            <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(6, 182, 212, 0.5)', borderRadius: '0.5rem' }} />
            <Legend />
            {allPorts.map(port => <Line key={port} type="monotone" dataKey={port} stroke={COLORS[port]} strokeWidth={2} dot={{ r: 4 }} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* INSIGHTS IA */}
      {insights.length > 0 && (
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '1.5rem', color: '#ffffff' }}>💡 Insights IA</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {insights.map((insight, idx) => (
              <div key={idx} style={{
                padding: '1.5rem',
                background: 'rgba(6, 182, 212, 0.05)',
                border: '1px solid rgba(6, 182, 212, 0.2)',
                borderRadius: '0.75rem',
                backdropFilter: 'blur(8px)'
              }}>
                <p style={{ fontSize: '0.95rem', color: 'rgba(6, 182, 212, 0.95)', lineHeight: 1.6, margin: 0 }}>{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // PAGE 2: BENCHMARK
  const BenchmarkPage = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 900, color: '#ffffff' }}>🎯 Benchmark Multidimensionnel</h1>

      {/* RADAR */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>Radar 6 Dimensions</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(6, 182, 212, 0.2)" />
            <PolarAngleAxis dataKey="metric" stroke="rgba(255, 255, 255, 0.6)" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="rgba(6, 182, 212, 0.3)" />
            {allPorts.map(port => <Radar key={port} name={port} dataKey={port} stroke={COLORS[port]} fill={COLORS[port]} fillOpacity={0.15} />)}
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* SCATTER */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>📍 Volume vs Market Share</h3>
        <ResponsiveContainer width="100%" height={350}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid stroke="rgba(6, 182, 212, 0.1)" />
            <XAxis type="number" dataKey="tonnage" name="Tonnage (M)" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis type="number" dataKey="marketShare" name="Market Share %" stroke="rgba(255, 255, 255, 0.5)" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: 'rgba(15, 23, 42, 0.9)' }} />
            {allPorts.map(port => {
              const data = comparison2024.filter(d => d.name === port);
              return <Scatter key={port} name={port} data={data} fill={COLORS[port]} />;
            })}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* COMPOSITE */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>Composite: Tonnage + TEU</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={comparison2024}>
            <CartesianGrid stroke="rgba(6, 182, 212, 0.1)" />
            <XAxis dataKey="name" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis yAxisId="left" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis yAxisId="right" orientation="right" stroke="rgba(255, 255, 255, 0.5)" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="tonnage" fill="#06b6d4" radius={[8, 8, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="teu" stroke="#ef4444" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* TABLE */}
      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>Tableau Détaillé</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: '0.9rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(6, 182, 212, 0.3)' }}>
                <th style={{ textAlign: 'left', padding: '1rem', color: '#06b6d4' }}>Port</th>
                <th style={{ textAlign: 'right', padding: '1rem', color: '#06b6d4' }}>Tonnage</th>
                <th style={{ textAlign: 'right', padding: '1rem', color: '#06b6d4' }}>% Marché</th>
                <th style={{ textAlign: 'right', padding: '1rem', color: '#06b6d4' }}>TEU</th>
              </tr>
            </thead>
            <tbody>
              {comparison2024.map(d => (
                <tr key={d.name} style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.1)', background: `${COLORS[d.name]}08` }}>
                  <td style={{ padding: '1rem', fontWeight: 600, color: COLORS[d.name] }}>{d.name}</td>
                  <td style={{ textAlign: 'right', padding: '1rem', color: '#ffffff' }}>{d.tonnage.toFixed(2)}M</td>
                  <td style={{ textAlign: 'right', padding: '1rem', color: '#ffffff' }}>{d.marketShare.toFixed(2)}%</td>
                  <td style={{ textAlign: 'right', padding: '1rem', color: '#ffffff' }}>{d.teu.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // PAGE 3: HEATMAP
  const HeatmapPage = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 900, color: '#ffffff' }}>🔥 Heatmap Temporelle 2020-2024</h1>

      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)', overflowX: 'auto' }}>
        <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid rgba(6, 182, 212, 0.3)' }}>
              <th style={{ padding: '1rem', textAlign: 'left', color: '#06b6d4' }}>Port</th>
              {['2020', '2021', '2022', '2023', '2024'].map(year => (
                <th key={year} style={{ padding: '1rem', textAlign: 'center', color: '#06b6d4', minWidth: '100px' }}>{year}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {heatmapData.map(row => (
              <tr key={row.port} style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.1)' }}>
                <td style={{ padding: '1rem', fontWeight: 600, color: COLORS[row.port] }}>{row.port}</td>
                {['2020', '2021', '2022', '2023', '2024'].map(year => {
                  const val = row[year] || 0;
                  const maxVal = Math.max(...Object.values(heatmapData).map(r => r[year]));
                  const intensity = maxVal > 0 ? (val / maxVal) * 255 : 0;
                  return (
                    <td key={`${row.port}-${year}`} style={{
                      padding: '1rem',
                      textAlign: 'center',
                      background: `rgba(6, 182, 212, ${intensity / 255 * 0.6})`,
                      color: '#ffffff',
                      fontWeight: 500
                    }}>
                      {val.toFixed(1)}M
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ padding: '2rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#ffffff', fontSize: '1.2rem' }}>Distribution Temporelle</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={yearlyArray}>
            <CartesianGrid stroke="rgba(6, 182, 212, 0.1)" />
            <XAxis dataKey="year" stroke="rgba(255, 255, 255, 0.5)" />
            <YAxis stroke="rgba(255, 255, 255, 0.5)" />
            <Tooltip />
            {allPorts.map(port => <Area key={port} type="monotone" dataKey={port} stroke={COLORS[port]} fill={COLORS[port]} fillOpacity={0.3} />)}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  // PAGE 4: CHAT IA
  const ChatPage = () => (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)' }}>
      <nav style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.2)', backdropFilter: 'blur(16px)', background: 'rgba(15, 23, 42, 0.4)', padding: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#ffffff', margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Brain size={28} /> Groq Intelligence
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'rgba(6, 182, 212, 0.6)', margin: '0.5rem 0 0 0' }}>Analysez les 5 ports en temps réel</p>
      </nav>

      <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', scrollBehavior: 'smooth' }}>
        {chatMessages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <Brain size={64} style={{ color: 'rgba(6, 182, 212, 0.3)', marginBottom: '1.5rem' }} />
            <h2 style={{ fontSize: '1.8rem', fontWeight: 900, color: '#ffffff', margin: '0 0 0.5rem 0' }}>Analyse Intelligente</h2>
            <p style={{ color: 'rgba(6, 182, 212, 0.7)', fontSize: '1rem', margin: 0, maxWidth: '400px' }}>Posez vos questions sur les ports, stratégies et tendances</p>
          </div>
        ) : (
          chatMessages.map((msg, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', animation: 'fadeIn 0.3s ease-in' }}>
              <div style={{
                maxWidth: '75%',
                padding: '1rem 1.25rem',
                borderRadius: '1rem',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%)'
                  : 'rgba(6, 182, 212, 0.1)',
                color: '#ffffff',
                border: msg.role === 'assistant' ? '1px solid rgba(6, 182, 212, 0.3)' : 'none',
                lineHeight: 1.6,
                fontSize: '0.95rem',
                wordWrap: 'break-word'
              }}>
                {msg.content || (msg.fullContent?.substring(0, typingChars))}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Loader size={16} style={{ animation: 'spin 1s linear infinite', color: '#06b6d4' }} />
            <span style={{ color: 'rgba(6, 182, 212, 0.7)', fontSize: '0.9rem' }}>Réflexion...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {chatMessages.length === 0 && (
        <div style={{ padding: '1.5rem', borderTop: '1px solid rgba(6, 182, 212, 0.2)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          {[
            'Quel port a le meilleur potentiel ?',
            'Analyse SWOT pour PAC',
            'Comparer tous les 5 ports',
            'Stratégie 2025-2026'
          ].map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(q)}
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '0.5rem',
                background: 'rgba(6, 182, 212, 0.15)',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                color: 'rgba(6, 182, 212, 0.9)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(6, 182, 212, 0.25)'}
              onMouseLeave={(e) => e.target.style.background = 'rgba(6, 182, 212, 0.15)'}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div style={{ borderTop: '1px solid rgba(6, 182, 212, 0.2)', padding: '1.25rem', background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
            placeholder="Votre question sur les ports..."
            autoFocus
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.875rem 1.25rem',
              borderRadius: '0.75rem',
              background: 'rgba(6, 182, 212, 0.05)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              color: '#ffffff',
              fontSize: '0.95rem',
              outline: 'none',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = 'rgba(6, 182, 212, 0.8)'}
            onBlur={(e) => e.target.style.borderColor = 'rgba(6, 182, 212, 0.3)'}
            disabled={loading}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={loading || !chatInput.trim()}
            style={{
              padding: '0.875rem 1.5rem',
              borderRadius: '0.75rem',
              background: loading || !chatInput.trim()
                ? 'rgba(6, 182, 212, 0.3)'
                : 'linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%)',
              border: 'none',
              color: '#ffffff',
              cursor: loading || !chatInput.trim() ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s'
            }}
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        input::placeholder { color: rgba(6, 182, 212, 0.5); }
      `}</style>
    </div>
  );

  // LAYOUT PRINCIPAL
  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <nav style={{ position: 'sticky', top: 0, zIndex: 50, borderBottom: '1px solid rgba(6, 182, 212, 0.2)', backdropFilter: 'blur(16px)', background: 'rgba(15, 23, 42, 0.4)', padding: '1rem', boxShadow: '0 8px 16px rgba(0,0,0,0.2)' }}>
        <div style={{ maxWidth: '90rem', margin: '0 auto', padding: '0 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.2rem', fontWeight: 900, color: '#ffffff' }}>
            <Ship size={28} /> W-Africa Ports
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {[
              { id: 'overview', label: 'Vue d\'ensemble' },
              { id: 'benchmark', label: 'Benchmark' },
              { id: 'heatmap', label: 'Heatmap' },
              { id: 'chat', label: 'Chat IA' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setCurrentPage(tab.id)}
                style={{
                  padding: '0.6rem 1rem',
                  borderRadius: '0.75rem',
                  background: currentPage === tab.id ? 'linear-gradient(135deg, #06b6d4 0%, #0ea5e9 100%)' : 'transparent',
                  color: currentPage === tab.id ? 'white' : 'rgba(6, 182, 212, 0.7)',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  transition: 'all 0.2s'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {currentPage === 'overview' && <div style={{ maxWidth: '90rem', margin: '0 auto', padding: '2rem' }}><OverviewPage /></div>}
      {currentPage === 'benchmark' && <div style={{ maxWidth: '90rem', margin: '0 auto', padding: '2rem' }}><BenchmarkPage /></div>}
      {currentPage === 'heatmap' && <div style={{ maxWidth: '90rem', margin: '0 auto', padding: '2rem' }}><HeatmapPage /></div>}
      {currentPage === 'chat' && <ChatPage />}

      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; padding: 0; }
      `}</style>
    </div>
  );
};

export default PortsDashboard;