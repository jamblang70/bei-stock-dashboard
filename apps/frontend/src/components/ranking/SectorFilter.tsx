"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface SectorFilterProps {
  value: string;
  onChange: (sector: string) => void;
}

export default function SectorFilter({ value, onChange }: SectorFilterProps) {
  const [sectors, setSectors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<string[]>("/stocks/sectors")
      .then(setSectors)
      .catch(() => setSectors([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor="sector-filter"
        className="text-sm font-medium text-text-secondary"
      >
        Sektor
      </label>
      <select
        id="sector-filter"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading}
        className="rounded-md border border-dark-border bg-dark-surface px-3 py-2 text-sm text-text-primary focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50 transition-colors"
      >
        <option value="">Semua Sektor</option>
        {sectors.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </div>
  );
}
