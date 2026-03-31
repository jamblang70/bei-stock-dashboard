import { ButtonHTMLAttributes, ReactNode } from "react";
import Spinner from "./Spinner";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
}

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-50 focus-visible:ring-emerald-500",
  secondary:
    "bg-dark-surface text-text-secondary border border-dark-border hover:bg-dark-hover hover:text-text-primary disabled:opacity-50 focus-visible:ring-dark-border",
  danger:
    "bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 focus-visible:ring-red-500",
  ghost:
    "bg-transparent text-text-secondary hover:bg-dark-hover hover:text-text-primary disabled:opacity-50 focus-visible:ring-dark-border",
};

const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-3 py-1.5 text-sm gap-1.5",
  md: "px-4 py-2 text-sm gap-2",
  lg: "px-6 py-3 text-base gap-2",
};

const spinnerSizeMap: Record<NonNullable<ButtonProps["size"]>, "sm" | "md" | "lg"> = {
  sm: "sm",
  md: "sm",
  lg: "md",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-bg";

  return (
    <button
      className={`${base} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && <Spinner size={spinnerSizeMap[size]} />}
      {children}
    </button>
  );
}
