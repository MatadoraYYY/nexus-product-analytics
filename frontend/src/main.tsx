import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import './styles.css';

const Plot = createPlotlyComponent(Plotly);
const API = (import.meta.env.VITE_API_BASE_URL || 'https://nexus-product-analytics-api-live.onrender.com').replace(/\/$/, '');

type Overview = Record<string, number | string | null>;
type Row = Record<string, any>;

async function getJson(path: string) {
  const response = await fetch(`${API}/api/v1/${path}`);
  if (!response.ok) {
    if (response.status === 503) throw new Error('Данные ещё готовятся. Сервис автоматически повторит запрос.');
    throw new Error(`Ошибка API: ${response.status}`);
  }
  return response.json();
}

function fmt(value: number | string | null, percent = false) {
  if (value == null) return '—';
  if (typeof value === 'string') return value;
  return percent ? `${(value * 100).toFixed(1)}%` : value.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
}

function App() {
  const [data, setData] = useState<{ overview: Overview; funnel: Row[]; revenue: Row[]; features: Row[] } | null>(null);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [overview, funnel, revenue, features] = await Promise.all([
          getJson('overview'),
          getJson('funnel'),
          getJson('revenue'),
          getJson('features'),
        ]);
        if (!cancelled) {
          setData({ overview, funnel, revenue, features });
          setError('');
          setLastUpdated(new Date());
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    };
    load();
    const timer = window.setInterval(load, 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, []);

  const d = data?.overview;
  const cards = useMemo(() => d ? [
    ['DAU', fmt(d.dau)], ['MAU', fmt(d.mau)], ['Stickiness', fmt(d.stickiness, true)],
    ['Activation', fmt(d.activation_rate, true)], ['D30 Retention', fmt(d.d30_retention, true)],
    ['MRR', `$${fmt(d.mrr)}`], ['Churn', fmt(d.churn, true)], ['LTV:CAC', fmt(d.ltv_cac)],
  ] : [], [d]);

  if (error && !data) return <main className="shell"><section className="state"><div className="brand">NEXUS</div><h1>Product Intelligence</h1><p>{error}</p><span>Повторяем подключение автоматически…</span></section></main>;
  if (!data || !d) return <main className="shell"><section className="state"><div className="spinner" /><div className="brand">NEXUS</div><h1>Загрузка аналитики</h1><p>Подключаемся к аналитическому API и готовим показатели.</p></section></main>;

  return <main className="shell">
    <header className="topbar">
      <div><div className="brand">NEXUS</div><h1>Product Intelligence</h1><p className="subtitle">Продуктовая аналитика в одном окне</p></div>
      <div className="statusBlock"><span className="status"><i /> API ONLINE</span><span className="period">Период: {d.period}</span></div>
    </header>
    <section className="grid" aria-label="Ключевые показатели">{cards.map(([label, value]) => <article className="metric" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    <section className="panel">
      <div className="panelHead"><div><h2>Воронка привлечения</h2><p>Конверсия между ключевыми этапами</p></div><span className="pill">LIVE</span></div>
      <div className="chart"><Plot data={[{type:'funnel', y:data.funnel.map(x=>x.step), x:data.funnel.map(x=>x.users), textinfo:'value+percent initial', hovertemplate:'%{y}<br>%{x:,} пользователей<extra></extra>'}]} layout={{height:380, margin:{l:150,r:30,t:12,b:24}, paper_bgcolor:'transparent', plot_bgcolor:'transparent', font:{family:'Inter,system-ui,sans-serif'}}} config={{displayModeBar:false, responsive:true}} useResizeHandler style={{width:'100%',height:'100%'}} /></div>
    </section>
    <section className="panel">
      <div className="panelHead"><div><h2>Выручка</h2><p>Net revenue и MRR по месяцам</p></div></div>
      <div className="chart"><Plot data={[{x:data.revenue.map(x=>x.month), y:data.revenue.map(x=>x.net_revenue), type:'scatter', mode:'lines+markers', name:'Net revenue', line:{width:3}}, {x:data.revenue.map(x=>x.month), y:data.revenue.map(x=>x.mrr), type:'scatter', mode:'lines+markers', name:'MRR', line:{width:3}}]} layout={{height:360, margin:{l:55,r:20,t:12,b:55}, paper_bgcolor:'transparent', plot_bgcolor:'transparent', legend:{orientation:'h',y:-0.18}, hovermode:'x unified', font:{family:'Inter,system-ui,sans-serif'}}} config={{displayModeBar:false, responsive:true}} useResizeHandler style={{width:'100%',height:'100%'}} /></div>
    </section>
    <section className="panel">
      <div className="panelHead"><div><h2>Использование функций</h2><p>Adoption и удержание D30</p></div></div>
      <div className="tableHead"><span>Функция</span><span>Adoption</span><span>D30</span></div>
      <div className="table">{data.features.map((x) => <div className="row" key={x.feature_name}><b>{x.feature_name}</b><span>{fmt(x.adoption_rate, true)}</span><span>{fmt(x.d30_retention, true)}</span></div>)}</div>
    </section>
    <footer><span>Data refresh: каждые 5 секунд</span><span>{lastUpdated ? `Обновлено ${lastUpdated.toLocaleTimeString('ru-RU')}` : ''}</span></footer>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
