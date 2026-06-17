'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Activity,
  CheckCircle,
  Loader2
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import StatCard from '@/components/dashboard/StatCard';
import AnimatedList from '@/components/bits/AnimatedList';
import api from '@/lib/api';
import styles from './page.module.css';

interface Threat {
  id: string;
  threat_type: string;
  severity: string;
  source_ip: string;
  detected_at: string;
  confidence_score: number;
}

interface Stats {
  total_events: number;
  events_last_hour: number;
}

interface ThreatSummary {
  total: number;
  critical: number;
  high: number;
  unresolved: number;
}

interface ChartPoint {
  time: string;
  events: number;
  threats: number;
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

export default function DashboardPage() {
  const [threats, setThreats] = useState<Threat[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [summary, setSummary] = useState<ThreatSummary | null>(null);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [training, setTraining] = useState(false);
  const [wsEvents, setWsEvents] = useState(0);

  const fetchData = useCallback(async () => {
    try {
      const [threatsRes, statsRes, summaryRes] = await Promise.all([
        api.get('/threats/?limit=10&is_resolved=false'),
        api.get('/events/stats'),
        api.get('/threats/summary'),
      ]);
      setThreats(threatsRes.data);
      setStats(statsRes.data);
      setSummary(summaryRes.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/events');

  ws.onopen = () => console.log('WebSocket connected');

  ws.onclose = (e) => console.log('WebSocket closed', e.code, e.reason);

  ws.onerror = (e) => console.error('WebSocket error', e);

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
      if (msg.type === 'network_event') {
        setWsEvents((n) => n + 1);
        const now = new Date();
        const label = now.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
        setChartData((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.time === label) {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...last,
              events: last.events + 1,
              threats: last.threats + (msg.data.is_anomaly ? 1 : 0),
            };
            return updated;
          }
          return [
            ...prev,
            {
              time: label,
              events: 1,
              threats: msg.data.is_anomaly ? 1 : 0,
            },
          ].slice(-20);
        });
      }
    };

    return () => ws.close();
  }, []);

  const handleTrain = async () => {
    setTraining(true);
    try {
      await api.post('/ai/train');
      await fetchData();
    } finally {
      setTraining(false);
    }
  };

  const severityClass = (s: string) => {
    const map: Record<string, string> = {
      critical: styles.critical,
      high: styles.high,
      medium: styles.medium,
      low: styles.low,
    };
    return map[s] ?? styles.low;
  };

  return (
    <div className={styles.page}>
      <div className={styles.statsGrid}>
        <StatCard
          label="Total Threats"
          value={summary?.total ?? 0}
          icon={<ShieldAlert size={18} />}
          accent="red"
          delta={summary?.critical ?? 0}
          deltaLabel="critical"
        />
        <StatCard
          label="Unresolved"
          value={summary?.unresolved ?? 0}
          icon={<AlertTriangle size={18} />}
          accent="amber"
          deltaLabel="need attention"
        />
        <StatCard
          label="Events (1h)"
          value={stats?.events_last_hour ?? 0}
          icon={<Activity size={18} />}
          accent="blue"
          delta={wsEvents}
          deltaLabel="live this session"
        />
        <StatCard
          label="Total Events"
          value={stats?.total_events ?? 0}
          icon={<CheckCircle size={18} />}
          accent="green"
          deltaLabel="analyzed"
        />
      </div>

      <div className={styles.bentoGrid}>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>Live Event Stream</span>
            <span className={styles.panelBadge}>Live</span>
          </div>
          <div className={styles.chartWrapper}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="eventsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#457B9D" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#457B9D" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="threatsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E63946" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#E63946" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#E5E5E3" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11, fill: '#9B9B9B', fontFamily: 'DM Sans' }}
                  axisLine={false}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9B9B9B', fontFamily: 'DM Sans' }}
                  axisLine={false}
                  tickLine={false}
                  width={24}
                />
                <Tooltip
                  contentStyle={{
                    background: '#fff',
                    border: '1px solid #E5E5E3',
                    borderRadius: 8,
                    fontSize: 12,
                    fontFamily: 'DM Sans',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.06)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="events"
                  stroke="#457B9D"
                  strokeWidth={2}
                  fill="url(#eventsGrad)"
                  dot={false}
                  name="Events"
                />
                <Area
                  type="monotone"
                  dataKey="threats"
                  stroke="#E63946"
                  strokeWidth={2}
                  fill="url(#threatsGrad)"
                  dot={false}
                  name="Threats"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>Recent Threats</span>
            <button
              className={styles.trainButton}
              onClick={handleTrain}
              disabled={training}
            >
              {training
                ? <><Loader2 size={14} className="spin" /> Training...</>
                : 'Train Model'
              }
            </button>
          </div>
          <div className={styles.panelBody}>
            {threats.length === 0 ? (
              <div className={styles.emptyState}>
                No threats detected yet. Train the model to begin analysis.
              </div>
            ) : (
              <AnimatedList delay={50}>
                {threats.map((t) => (
                  <div key={t.id} className={styles.threatItem}>
                    <span className={`${styles.severityBadge} ${severityClass(t.severity)}`}>
                      {t.severity}
                    </span>
                    <div className={styles.threatInfo}>
                      <div className={styles.threatType}>{t.threat_type.replace('_', ' ')}</div>
                      <div className={styles.threatIp}>{t.source_ip}</div>
                    </div>
                    <span className={styles.threatTime}>
                      {formatTimeAgo(t.detected_at)}
                    </span>
                  </div>
                ))}
              </AnimatedList>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}