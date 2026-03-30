"use client";

import { useState, useEffect, useRef } from "react";
import { apiGet } from "@/lib/api";
import type { Stock } from "@/types";

interface UseSearchResult {
  results: Stock[];
  loading: boolean;
  error: string | null;
}

export function useSearch(query: string): UseSearchResult {
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    if (!query.trim()) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    timerRef.current = setTimeout(async () => {
      try {
        const data = await apiGet<Stock[]>(`/stocks/search?q=${encodeURIComponent(query)}`);
        setResults(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Gagal memuat hasil pencarian";
        setError(message);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [query]);

  return { results, loading, error };
}
