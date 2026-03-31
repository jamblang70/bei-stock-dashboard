"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createChart, ColorType, CrosshairMode } from "lightweight-charts";
import type { IChartApi, ISeriesApi, CandlestickData, LineData, Time } from "lightweight-charts";
import {
  ResponsiveContainer,
  LineChart,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import { apiGet } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Range = "1w" | "1m" | "3m" | "6m" | "1y" | "5y";
type Indicator = "RSI" | "MACD" | "Volume";

interface TechnicalDataItem {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  ma20: number | null;
  ma50: number | null;
  ma200: number | null;
  ema20: number | null;
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}

interface PriceChartProps {
  code: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RANGES: { label: string; value: Range }[] = [
  { label: "1M", value: "1w" },
  { label: "1B", value: "1m" },
  { label: "3B", value: "3m" },
  { label: "6B", value: "6m" },
  { label: "1T", value: "1y" },
  { label: "5T", value: "5y" },
];

const OVERLAYS = ["MA20", "MA50", "MA200", "BB"] as const;
type Overlay = (typeof OVERLAYS)[number];

const OVERLAY_COLORS: Record<Overlay, string> = {
  MA20: "#eab308",
  MA50: "#3b82f6",
  MA200: "#ef4444",
  BB: "#a855f7",
};

const INDICATORS: Indicator[] = ["RSI", "MACD", "Volume"];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function PriceChart({ code }: PriceChartProps) {
  const [range, setRange] = useState<Range>("3m");
  const [data, setData] = useState<TechnicalDataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [activeOverlays, setActiveOverlays] = useState<Set<Overlay>>(new Set(["MA20", "MA50"]));
  const [indicator, setIndicator] = useState<Indicator>("RSI");

  // lightweight-charts refs
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lineRefs = useRef<Partial<Record<string, ISeriesApi<"Line">>>>({});

  // ---------------------------------------------------------------------------
  // Fetch
  // ---------------------------------------------------------------------------

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    apiGet<TechnicalDataItem[]>(`/stocks/${code}/technical?range=${range}`)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [code, range]);

  // ---------------------------------------------------------------------------
  // Chart init
  // ---------------------------------------------------------------------------

  const initChart = useCallback(() => {
    if (!chartContainerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      candleRef.current = null;
      lineRefs.current = {};
    }

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "#0a0a0f" },
        textColor: "#9ca3af",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "#374151", width: 1, style: 3, labelBackgroundColor: "#1f2937" },
        horzLine: { color: "#374151", width: 1, style: 3, labelBackgroundColor: "#1f2937" },
      },
      rightPriceScale: {
        borderColor: "#1f2937",
        scaleMargins: { top: 0.05, bottom: 0.05 },
      },
      timeScale: {
        borderColor: "#1f2937",
        timeVisible: false,
      },
      width: container.clientWidth,
      height: container.clientHeight,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;

    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Init chart when data arrives
  useEffect(() => {
    if (!loading && !error && data.length > 0) {
      const cleanup = initChart();
      return () => {
        cleanup?.();
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
          candleRef.current = null;
          lineRefs.current = {};
        }
      };
    }
  }, [loading, error, data.length, initChart]);

  // ---------------------------------------------------------------------------
  // Populate candlestick data
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!candleRef.current || data.length === 0) return;

    const candleData: CandlestickData[] = data.map((d) => ({
      time: d.date as Time,
      open: d.open ?? d.close,
      high: d.high ?? d.close,
      low: d.low ?? d.close,
      close: d.close,
    }));

    candleRef.current.setData(candleData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  // ---------------------------------------------------------------------------
  // Overlay lines
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    const overlayConfig: Array<{
      key: Overlay;
      field: keyof TechnicalDataItem;
      color: string;
      dash?: boolean;
    }> = [
      { key: "MA20", field: "ma20", color: OVERLAY_COLORS.MA20 },
      { key: "MA50", field: "ma50", color: OVERLAY_COLORS.MA50 },
      { key: "MA200", field: "ma200", color: OVERLAY_COLORS.MA200 },
      { key: "BB", field: "bb_upper", color: OVERLAY_COLORS.BB, dash: true },
      { key: "BB", field: "bb_middle", color: OVERLAY_COLORS.BB, dash: true },
      { key: "BB", field: "bb_lower", color: OVERLAY_COLORS.BB, dash: true },
    ];

    // Remove all existing overlay series
    Object.values(lineRefs.current).forEach((s) => {
      try { chartRef.current?.removeSeries(s!); } catch { /* ignore */ }
    });
    lineRefs.current = {};

    overlayConfig.forEach(({ key, field, color, dash }) => {
      if (!activeOverlays.has(key) || !chartRef.current) return;

      const lineData: LineData[] = data
        .filter((d) => d[field] != null)
        .map((d) => ({ time: d.date as Time, value: d[field] as number }));

      if (lineData.length === 0) return;

      const series = chartRef.current.addLineSeries({
        color,
        lineWidth: 1,
        lineStyle: dash ? 2 : 0,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      series.setData(lineData);

      const refKey = `${key}_${field}`;
      lineRefs.current[refKey] = series;
    });
  }, [data, activeOverlays]);

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const toggleOverlay = (o: Overlay) => {
    setActiveOverlays((prev) => {
      const next = new Set(prev);
      next.has(o) ? next.delete(o) : next.add(o);
      return next;
    });
  };

  // ---------------------------------------------------------------------------
  // Indicator panel data
  // ---------------------------------------------------------------------------

  const indicatorData = data.map((d) => ({
    date: d.date,
    rsi: d.rsi,
    macd: d.macd,
    macd_signal: d.macd_signal,
    macd_hist: d.macd_hist,
    volume: d.volume,
    isUp: d.close >= (d.open ?? d.close),
  }));

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-6">
      {/* Header row */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-secondary">
          Grafik Harga
        </h2>
        <div className="flex flex-wrap gap-1">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setRange(r.value)}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                range === r.value
                  ? "bg-emerald-500 text-white"
                  : "bg-dark-bg text-text-secondary hover:bg-dark-hover hover:text-text-primary"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Overlay toggles */}
      <div className="mb-3 flex flex-wrap items-center gap-1">
        <span className="mr-1 text-xs text-text-muted">Overlay:</span>
        {OVERLAYS.map((o) => (
          <button
            key={o}
            onClick={() => toggleOverlay(o)}
            className={`rounded-full px-2 py-0.5 text-xs font-medium transition-colors border ${
              activeOverlays.has(o)
                ? "border-transparent text-white"
                : "border-dark-border bg-transparent text-text-muted hover:text-text-primary"
            }`}
            style={activeOverlays.has(o) ? { backgroundColor: OVERLAY_COLORS[o] } : {}}
          >
            {o}
          </button>
        ))}
      </div>

      {/* Main candlestick chart */}
      <div className="h-[300px]">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-dark-border border-t-emerald-500" />
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center text-sm text-text-muted">
            Gagal memuat data harga
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-text-muted">
            Data tidak tersedia
          </div>
        ) : (
          <div ref={chartContainerRef} className="h-full w-full" />
        )}
      </div>

      {/* Indicator selector */}
      {!loading && !error && data.length > 0 && (
        <>
          <div className="mt-4 mb-2 flex items-center gap-1">
            <span className="mr-1 text-xs text-text-muted">Indikator:</span>
            {INDICATORS.map((ind) => (
              <button
                key={ind}
                onClick={() => setIndicator(ind)}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  indicator === ind
                    ? "bg-dark-hover text-text-primary"
                    : "text-text-muted hover:text-text-primary"
                }`}
              >
                {ind}
              </button>
            ))}
          </div>

          {/* Indicator panel */}
          <div className="h-[150px]">
            {indicator === "RSI" && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={indicatorData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <XAxis dataKey="date" hide />
                  <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} width={28} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: 6, fontSize: 11 }}
                    labelStyle={{ color: "#9ca3af" }}
                    itemStyle={{ color: "#22c55e" }}
                    formatter={(v: number) => [v?.toFixed(2), "RSI"]}
                  />
                  <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeWidth={1} />
                  <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" strokeWidth={1} />
                  <Line
                    type="monotone"
                    dataKey="rsi"
                    stroke="#22c55e"
                    dot={false}
                    strokeWidth={1.5}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            )}

            {indicator === "MACD" && (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={indicatorData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <XAxis dataKey="date" hide />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} width={40} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: 6, fontSize: 11 }}
                    labelStyle={{ color: "#9ca3af" }}
                  />
                  <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
                  <Bar dataKey="macd_hist" name="Histogram">
                    {indicatorData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={(entry.macd_hist ?? 0) >= 0 ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)"}
                      />
                    ))}
                  </Bar>
                  <Line
                    type="monotone"
                    dataKey="macd"
                    stroke="#3b82f6"
                    dot={false}
                    strokeWidth={1.5}
                    connectNulls
                    name="MACD"
                  />
                  <Line
                    type="monotone"
                    dataKey="macd_signal"
                    stroke="#f97316"
                    dot={false}
                    strokeWidth={1.5}
                    connectNulls
                    name="Signal"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}

            {indicator === "Volume" && (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={indicatorData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                  <XAxis dataKey="date" hide />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} width={40} tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: 6, fontSize: 11 }}
                    labelStyle={{ color: "#9ca3af" }}
                    formatter={(v: number) => [`${(v / 1e6).toFixed(2)}M`, "Volume"]}
                  />
                  <Bar dataKey="volume" name="Volume">
                    {indicatorData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={entry.isUp ? "rgba(34,197,94,0.5)" : "rgba(239,68,68,0.5)"}
                      />
                    ))}
                  </Bar>
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  );
}
