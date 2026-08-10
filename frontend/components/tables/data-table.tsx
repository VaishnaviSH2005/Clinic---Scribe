"use client";

import { ChevronLeft, ChevronRight, Search as SearchIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface DataTableColumn<T> {
  header: string;
  accessor: (row: T) => React.ReactNode;
  className?: string;
}

interface EmptyState {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string;
  isLoading?: boolean;
  isError?: boolean;
  emptyState: EmptyState;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  search?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  toolbar?: React.ReactNode;
}

// Generic reusable table (PRD Ch5.13): sticky header, 56px rows, mandatory
// pagination, search, loading skeleton, and empty state. Used across every
// list screen instead of one-off table markup per feature.
export function DataTable<T>({
  columns,
  data,
  rowKey,
  isLoading = false,
  isError = false,
  emptyState,
  page,
  pageSize,
  total,
  onPageChange,
  search,
  onSearchChange,
  searchPlaceholder = "Search…",
  toolbar,
}: DataTableProps<T>) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex flex-col gap-4">
      {(onSearchChange || toolbar) && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {onSearchChange && (
            <div className="relative w-full max-w-xs">
              <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
              <Input
                value={search ?? ""}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder={searchPlaceholder}
                className="pl-9"
              />
            </div>
          )}
          {toolbar}
        </div>
      )}

      <div className="overflow-x-auto rounded-card border border-border bg-surface">
        <table className="w-full min-w-full text-left">
          <thead className="bg-muted sticky top-0">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.header}
                  className={cn(
                    "px-4 py-3 text-caption font-medium uppercase text-text-secondary",
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="h-14 border-t border-border">
                  {columns.map((col) => (
                    <td key={col.header} className="px-4 py-3">
                      <Skeleton className="h-4 w-3/4" />
                    </td>
                  ))}
                </tr>
              ))}

            {!isLoading && isError && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-10 text-center text-body text-danger"
                >
                  Something went wrong while loading this data. Please try again.
                </td>
              </tr>
            )}

            {!isLoading && !isError && data.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center">
                  <p className="text-body-lg font-medium text-text-primary">{emptyState.title}</p>
                  {emptyState.description && (
                    <p className="mt-1 text-body text-text-secondary">{emptyState.description}</p>
                  )}
                  {emptyState.action && (
                    <div className="mt-4 flex justify-center">{emptyState.action}</div>
                  )}
                </td>
              </tr>
            )}

            {!isLoading &&
              !isError &&
              data.map((row) => (
                <tr key={rowKey(row)} className="hover:bg-muted/50 h-14 border-t border-border">
                  {columns.map((col) => (
                    <td
                      key={col.header}
                      className={cn("px-4 py-3 text-body text-text-primary", col.className)}
                    >
                      {col.accessor(row)}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {!isLoading && !isError && total > 0 && (
        <div className="flex items-center justify-between text-body text-text-secondary">
          <span>
            Page {page} of {totalPages} ({total} total)
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
