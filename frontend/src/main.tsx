import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Plot from 'react-plotly.js';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type Overview = Record<string, number | string | null>;

function fmt(value: number | string | null, percent = false) {
  if (value == null) return '—';
  if (typeof value === 'string') return value;
  return percent ? `${(value * 100).toFixed(1)}%` : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [funnel, setFunnel] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any[]>([]);
  const [features, setFeatures] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all(['overview', 'funnel', 'revenue', 'features'].map((name) => fetch(`${API}/api/v1/${name}`).then((r) => {
      if (!r.ok) throw new Error(`API ${r.status}`);
      return r.json();
    }))).then(([o, f, r, ft]) => {
      setOverview(o); setFunnel(f); setRevenue(r); setFeatures(ft);
    }).catch((e) => setError(String(e)));
  }, []);

  if (error) return <main><h1>NEXUS</h1><p>Analytics API is warming up. Refresh in a few seconds.</p><small>{error}</small></main>;
  if (!overview) return <main><h1>NEXUS</h1><p>Loading analytics…</p></main>;

  const cards = [
    ['DAU', fmt(overview.dau)], ['MAU', fmt(overview.mau)], ['Stickiness', fmt(overview.stickiness, true)],
    ['Activation', fmt(overview.activation_rate, true)], ['D30 Retention', fmt(overview.d30_retention, true)],
    ['MRR', `$${fmt(overview.mrr)}`], ['Churn', fmt(overview.churn, true)], ['LTV:CAC', fmt(overview.ltv_cac)],
  ];

  return <main>
    <header><div><span>NEXUS</span><h1>Product Intelligence</h1></div><small>{overview.period}</small></header>
    <section className="grid">{cards.map(([label, value]) => <article key={label}><small>{label}</small><strong>{value}</strong></article>)}</section>
    <section className="panel"><h2>Acquisition funnel</h2><Plot data={[{type:'funnel', y:funnel.map(x=>x.step), x:funnel.map(x=>x.users), textinfo:'value+percent initial'}]} layout={{height:380, margin:{l:120,r:30,t:20,b:30}}} config={{displayModeBar:false}} /></section>
    <section className="panel"><h2>Revenue</h2><Plot data={[{x:revenue.map(x=>x.month), y:revenue.map(x=>x.net_revenue), type:'scatter', mode:'lines+markers', name:'Net revenue'},{x:revenue.map(x=>x.month), y:revenue.map(x=>x.mrr), type:'scatter', mode:'lines+markers', name:'MRR'}]} layout={{height:330, margin:{l:55,r:20,t:20,b:55}, legend:{orientation:'h'}}} config={{displayModeBar:false}} /></section>
    <section className="panel"><h2>Feature adoption</h2><div className="table">{features.map((x) => <div className="row" key={x.feature_name}><b>{x.feature_name}</b><span>{fmt(x.adoption_rate, true)}</span><span>D30 {fmt(x.d30_retention, true)}</span></div>)}</div></section>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
