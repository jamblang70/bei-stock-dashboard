"use client";

type BannerType = "warning" | "error" | "info";

interface BannerProps {
  type: BannerType;
  message: string;
  onDismiss?: () => void;
}

const typeClasses: Record<BannerType, string> = {
  warning: "bg-yellow-50 border-yellow-400 text-yellow-800",
  error: "bg-red-50 border-red-400 text-red-800",
  info: "bg-blue-50 border-blue-400 text-blue-800",
};

const icons: Record<BannerType, string> = {
  warning: "⚠️",
  error: "❌",
  info: "ℹ️",
};

export default function Banner({ type, message, onDismiss }: BannerProps) {
  return (
    <div
      className={`border-l-4 p-4 ${typeClasses[type]}`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-2">
          <span aria-hidden="true">{icons[type]}</span>
          <p className="text-sm">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="shrink-0 text-sm font-medium underline hover:no-underline"
            aria-label="Tutup peringatan"
          >
            Tutup
          </button>
        )}
      </div>
    </div>
  );
}
