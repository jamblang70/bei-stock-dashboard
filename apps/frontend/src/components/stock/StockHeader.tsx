import type { StockProfile } from "@/types";

interface StockHeaderProps {
  stock: StockProfile;
}

function formatNumber(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return "N/A";
  return value.toLocaleString("id-ID", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function formatVolume(volume: number | null | undefined): string {
  if (volume === null || volume === undefined) return "N/A";
  if (volume >= 1_000_000_000) return `${(volume / 1_000_000_000).toFixed(2)}M lot`;
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(2)}jt`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(1)}rb`;
  return volume.toString();
}

export default function StockHeader({ stock }: StockHeaderProps) {
  // Backend returns price as nested object: stock.price.price, stock.price.change_nominal, etc.
  const priceData = (stock as any).price;
  const lastPrice = priceData?.price ?? priceData?.close ?? stock.last_price ?? null;
  const changeNominal = priceData?.change_nominal ?? stock.change_nominal ?? null;
  const changePct = priceData?.change_pct ?? stock.change_pct ?? null;
  const volume = priceData?.volume ?? stock.volume ?? null;

  const isPositive = (changeNominal ?? 0) >= 0;
  const changeColor = isPositive ? "text-emerald-400" : "text-red-400";
  const changeBg = isPositive ? "bg-emerald-500/10 border-emerald-500/20" : "bg-red-500/10 border-red-500/20";

  return (
    <div className="rounded-xl border border-dark-border bg-dark-surface p-4 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between sm:gap-4">
        {/* Left: identity */}
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-lg bg-emerald-500 px-2.5 py-1 text-base font-bold text-white sm:text-lg">
              {stock.code}
            </span>
            {stock.sector && (
              <span className="rounded-full border border-dark-border bg-dark-bg px-2.5 py-0.5 text-xs text-text-secondary">
                {stock.sector}
              </span>
            )}
            {stock.is_syariah && (
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
                ☪ Syariah
              </span>
            )}
          </div>
          <h1 className="mt-1.5 text-lg font-semibold text-text-primary sm:text-xl">{stock.name}</h1>
          {stock.sub_sector && (
            <p className="mt-0.5 text-xs text-text-muted sm:text-sm">{stock.sub_sector}</p>
          )}
        </div>

        {/* Right: price — full width on mobile */}
        <div className={`rounded-xl border px-4 py-3 sm:px-5 sm:text-right ${changeBg}`}>
          <p className="text-2xl font-bold text-text-primary sm:text-3xl">
            Rp {formatNumber(lastPrice, 0)}
          </p>
          <div className={`mt-1 flex items-center gap-2 text-sm font-medium sm:justify-end ${changeColor}`}>
            <span>
              {isPositive ? "+" : ""}
              {formatNumber(changeNominal, 0)}
            </span>
            <span>
              ({isPositive ? "+" : ""}
              {changePct !== null && changePct !== undefined ? Number(changePct).toFixed(2) : "N/A"}%)
            </span>
          </div>
          <p className="mt-1 text-xs text-text-muted">
            Vol: {formatVolume(volume)}
          </p>
        </div>
      </div>
    </div>
  );
}
