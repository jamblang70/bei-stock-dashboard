"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createChart, ColorType, CrosshairMode } from "lightweight-charts";
import type { IChartApi, ISeriesApi, CandlestickData, HistogramData, Time } from "lightweight-charts";
import { apiGet } from "@/lib/api";
import type { PriceHistory } from "@/types";

type Range = "1w" | "1m" | "3m" | "6m" | "1y" | "5y";

const RANGES: { label: string; value: Range }[] = [
  { label: "1M", value: "1w" },
  { label: "1B", value: "1m" },
  { label: "3B", value: "3m" },
  { label: "6B", value: "6m" },
  { label: "1T", value: "1y" },
  { label: "5T", value: "5y" },
];

interface PriceChartProps {
  code: string;
}

export default function PriceChart({ code }: PriceChartProps) {
  const [range, setRange] = useState<Range>("3m");
  const [data, setData] = useState<PriceHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    apiGet<PriceHistory[]>(`/stocks/${code}/price-history?range=${range}`)
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

    return () => {
      cancelled = true;
    };
  }, [code, range]);

  const initChart = useCallback(() => {
    if (!chartContainerRef.current) return;

    // Clean up existing chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
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
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: "#1f2937",
        timeVisible: false,
      },
      width: container.clientWidth,
      height: container.clientHeight,
    });

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Volume histogram series
    const volumeSeries = chart.addHistogramSeries({
      color: "#22c55e",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  // Initialize chart once
  useEffect(() => {
    if (!loading && !error && data.length > 0) {
      const cleanup = initChart();
      return () => {
        cleanup?.();
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
      };
    }
  }, [loading, error, data.length > 0, initChart]);

  // Update data when it changes
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) return;

    const candlestickData: CandlestickData[] = data.map((d) => ({
      time: d.date as Time,
      open: d.open ?? d.close,
      high: d.high ?? d.close,
      low: d.low ?? d.close,
      close: d.close,
    }));

    const volumeData: HistogramData[] = data.map((d) => ({
      time: d.date as Time,
      value: d.volume ?? 0,
      color: d.close >= (d.open ?? d.close) ? "rgba(34, 197, 94, 0.4)" : "rgba(239, 68, 68, 0.4)",
    }));

    candlestickSeriesRef.current.setData(candlestickData);
    volumeSeriesRef.current.setData(volumeData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-secondary">
          Grafik Harga
        </h2>
        <div className="flex gap-1">
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

      <div className="h-[400px]">
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
    </div>
  );
}
