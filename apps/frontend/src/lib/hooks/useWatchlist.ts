"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import type { WatchlistItem } from "@/types";

interface UseWatchlistResult {
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;
  addStock: (code: string) => Promise<void>;
  removeStock: (code: string) => Promise<void>;
}

export function useWatchlist(token: string | undefined): UseWatchlistResult {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setItems([]);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .get<any>("/watchlist/", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        if (!cancelled) {
          const data = Array.isArray(res.data) ? res.data : (res.data?.data ?? []);
          setItems(data);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Gagal memuat watchlist";
          setError(message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const addStock = useCallback(
    async (code: string) => {
      if (!token) return;

      // Optimistic add — flat format matching backend response
      const optimisticItem: WatchlistItem = {
        code,
        name: code,
        sector: null,
        price: null,
        change_pct: null,
        score: null,
        recommendation: null,
        added_at: new Date().toISOString(),
      };

      setItems((prev) => [...prev, optimisticItem]);

      try {
        const res = await api.post<WatchlistItem>(
          "/watchlist/",
          { code },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setItems((prev) =>
          prev.map((item) => (item.code === optimisticItem.code ? res.data : item))
        );
      } catch (err: unknown) {
        setItems((prev) => prev.filter((item) => item.code !== optimisticItem.code));
        const message = err instanceof Error ? err.message : "Gagal menambahkan saham";
        setError(message);
        throw err;
      }
    },
    [token]
  );

  const removeStock = useCallback(
    async (code: string) => {
      if (!token) return;

      const snapshot = items;
      setItems((prev) => prev.filter((item) => (item.code ?? (item as any).stock?.code) !== code));

      try {
        await api.delete(`/watchlist/${code}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (err: unknown) {
        setItems(snapshot);
        const message = err instanceof Error ? err.message : "Gagal menghapus saham";
        setError(message);
        throw err;
      }
    },
    [token, items]
  );

  return { items, loading, error, addStock, removeStock };
}
