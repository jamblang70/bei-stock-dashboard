"use client";

import { useState, useEffect, useCallback } from "react";
import { apiGet } from "@/lib/api";
import type { StockProfile, PriceHistory } from "@/types";

interface UseStockResult {
  profile: StockProfile | null;
  priceHistory: PriceHistory[];
  loading: boolean;
  error: string | null;
  setRange: (range: string) => void;
}

export function useStock(code: string, initialRange = "3m"): UseStockResult {
  const [profile, setProfile] = useState<StockProfile | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState(initialRange);

  useEffect(() => {
    if (!code) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      apiGet<StockProfile>(`/stocks/${code}`),
      apiGet<PriceHistory[]>(`/stocks/${code}/price-history?range=${range}`),
    ])
      .then(([profileData, historyData]) => {
        if (!cancelled) {
          setProfile(profileData);
          setPriceHistory(historyData);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Gagal memuat data saham";
          setError(message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [code, range]);

  const handleSetRange = useCallback((newRange: string) => {
    setRange(newRange);
  }, []);

  return { profile, priceHistory, loading, error, setRange: handleSetRange };
}
