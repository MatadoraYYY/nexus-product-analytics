import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Plot from 'react-plotly.js';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'https://nexus-product-analytics-api.onrender.com';

type Overview = Record<string, number | string | null>;

async function getJson(path: string) {
  const response = await fetch(`${API}/api/v1/${path}`);
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

function fmt(value: number | string | null, percent = false) {
  if (value == null) return '—';
  if (typeof value === 'string') return value;
  return percent ? `${(value * 100).toFixed(1)}%` : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function App() {
  const [data, setData] = useState<{ overview: Overview; funnel: any[]; revenue: any[]; features: any[] } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [overview, funnel, revenue, features] = await Promise.all([getJson('overview'), getJson('funnel'), getJson('revenue'), getJson('features')]);
        if (!cancelled) setData({ overview, funnel, revenue, features });
        if (!cancelled) setError('');
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    };
    load();
    const timer = window.setInterval(load, 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, []);

  if (error && !data) return <main><h1>NEXUS</h1><p>Analytics API is warming up. Retrying automatically…</p><small>{error}</small></main>;
  if (!data) return <main><h1>NEXUS</h1><p>Loading analytics…</p></main>;

  const d = data.overview;
  const cards = [
    ['DAU', fmt(d.dau)], ['MAU', fmt(d.mau)], ['Stickiness', fmt(d.stickiness, true)],
    ['Activation', fmt(d.activation_rate, true)], ['D30 Retention', fmt(d.d30_retention, true)],
    ['MRR', `$${fmt(d.mrr)}`], ['Churn', fmt(d.churn, true)], ['LTV:CAC', fmt(d.ltv_cac)],
  ];

  return <main>
    <header><div><span>NEXUS</span><h1>Product Intelligence</h1></div><small>{d.period}</small></header>
    <section className="grid">{cards.map(([label, value]) => <article key={label}><small>{label}</small><strong>{value}</strong></article>)}</section>
    <section className="panel"><h2>Acquisition funnel</h2><Plot data={[{type:'funnel', y:data.funnel.map(x=>x.step), x:data.funnel.map(x=>x.users), textinfo:'value+percent initial'}]} layout={{height:380, margin:{l:120,r:30,t:20,b:30}}} config={{displayModeBar:false}} /></section>
    <section className="panel"><h2>Revenue</h2><Plot data={[{x:data.revenue.map(x=>x.month), y:data.revenue.map(x=>x.net_revenue), type:'scatter', mode:'lines+markers', name:'Net revenue'},{x:data.revenue.map(x=>x.month), y:data.revenue.map(x=>x.mrr), type:'scatter', mode:'lines+markers', name:'MRR'}]} layout={{height:330, margin:{l:55,r:20,t:20,b:55}, legend:{orientation:'h'}}} config={{displayModeBar:false}} /></section>
    <section className="panel"><h2>Feature adoption</h2><div className="table">{data.features.map((x) => <div className="row" key={x.feature_name}><b>{x.feature_name}</b><span>{fmt(x.adoption_rate, true)}</span><span>D30 {fmt(x.d30_retention, true)}</span></div>)}</div></section>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
