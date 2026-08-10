import * as React from "react";

import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

// Native select styled to match Input (PRD Ch5.12). Kept dependency-free
// (no Radix Select) — this milestone's forms don't need search/multi-select.
const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error = false, ...props }, ref) => {
    return (
      <select
        ref={ref}
        aria-invalid={error}
        className={cn(
          "h-11 w-full rounded-md border bg-surface px-4 text-body text-text-primary transition-colors duration-micro focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-60",
          error ? "border-danger" : "border-border",
          className,
        )}
        {...props}
      />
    );
  },
);
Select.displayName = "Select";

export { Select };
