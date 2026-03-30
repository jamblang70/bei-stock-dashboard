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
      .get<{ data: WatchlistItem[]; total: number } | WatchlistItem[]>("/watchlist/", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        if (!cancelled) {
          const items = Array.isArray(res.data) ? res.data : (res.data as any).data ?? [];
          setItems(items);
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

      // Optimistic add — buat placeholder item
      const optimisticItem: WatchlistItem = {
        id: Date.now(),
        stock: { id: 0, code, name: code, sector: null, sub_sector: null, is_active: true },
        last_price: null,
        change_nominal: null,
        change_pct: null,
        score: null,
        added_at: new Date().toISOString(),
      };

      setItems((prev) => [...prev, optimisticItem]);

      try {
        const res = await api.post<WatchlistItem>(
          "/watchlist/",
          { stock_code: code },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        // Ganti placeholder dengan data asli dari server
        setItems((prev) =>
          prev.map((item) => (item.id === optimisticItem.id ? res.data : item))
        );
      } catch (err: unknown) {
        // Rollback
        setItems((prev) => prev.filter((item) => item.id !== optimisticItem.id));
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

      // Simpan snapshot untuk rollback
      const snapshot = items;
      setItems((prev) => prev.filter((item) => item.stock.code !== code));

      try {
        await api.delete(`/watchlist/${code}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (err: unknown) {
        // Rollback ke snapshot
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
