"use client";

interface SyariahFilterProps {
  value: boolean;
  onChange: (active: boolean) => void;
}

export default function SyariahFilter({ value, onChange }: SyariahFilterProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!value)}
      className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
        value
          ? "border-emerald-500 bg-emerald-500/15 text-emerald-400"
          : "border-dark-border bg-dark-surface text-text-secondary hover:bg-dark-hover"
      }`}
    >
      <span className="text-base leading-none">☪</span>
      Syariah
    </button>
  );
}
