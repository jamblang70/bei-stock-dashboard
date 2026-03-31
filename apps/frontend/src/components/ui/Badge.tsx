import { ReactNode } from "react";

type BadgeVariant = "success" | "info" | "warning" | "danger" | "neutral";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: "bg-emerald-500/20 text-emerald-400",
  info: "bg-blue-500/20 text-blue-400",
  warning: "bg-yellow-500/20 text-yellow-400",
  danger: "bg-red-500/20 text-red-400",
  neutral: "bg-gray-500/20 text-text-secondary",
};

export default function Badge({ variant = "neutral", children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

// Helper: konversi score ke variant Badge
export function scoreVariant(score: number): BadgeVariant {
  if (score >= 80) return "success";
  if (score >= 60) return "info";
  if (score >= 40) return "warning";
  return "danger";
}

// Helper: konversi rekomendasi ke variant Badge
export function recommendationVariant(
  recommendation: string | null | undefined
): BadgeVariant {
  switch (recommendation) {
    case "Beli Kuat":
      return "success";
    case "Beli":
      return "info";
    case "Tahan":
      return "warning";
    case "Jual":
      return "danger";
    default:
      return "neutral";
  }
}

// ScoreBadge — convenience wrapper
export function ScoreBadge({ score }: { score: number }) {
  const labels: Record<string, string> = {
    success: "Sangat Baik",
    info: "Baik",
    warning: "Cukup",
    danger: "Perlu Perhatian",
  };
  const variant = scoreVariant(score);
  return <Badge variant={variant}>{labels[variant]}</Badge>;
}
