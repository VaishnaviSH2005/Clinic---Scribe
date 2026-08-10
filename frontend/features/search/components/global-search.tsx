"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, Loader2, Search as SearchIcon, Stethoscope, User, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";

import { searchService } from "../services/search.service";

const TYPE_ICON: Record<string, LucideIcon> = {
  patient: Users,
  appointment: SearchIcon,
  consultation: Stethoscope,
  report: FileText,
  user: User,
};

export function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data, isFetching } = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => searchService.search(debounced),
    enabled: debounced.trim().length >= 2,
  });

  const results = data?.results ?? [];

  return (
    <DropdownMenu open={open && debounced.trim().length >= 2} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <div className="relative w-full min-w-0 max-w-md">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
          <Input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            placeholder="Search patients, appointments, consultations…"
            className="pl-9"
          />
          {isFetching && (
            <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-text-secondary" />
          )}
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-[420px] w-[420px] overflow-y-auto">
        {results.length === 0 && !isFetching && (
          <p className="px-4 py-6 text-center text-body text-text-secondary">
            No results for &quot;{debounced}&quot;.
          </p>
        )}
        {results.map((result) => {
          const Icon = TYPE_ICON[result.type] ?? SearchIcon;
          return (
            <button
              key={`${result.type}-${result.id}`}
              onClick={() => {
                router.push(result.href);
                setOpen(false);
                setQuery("");
              }}
              className="hover:bg-muted flex w-full items-center gap-3 border-b border-border px-4 py-3 text-left last:border-b-0"
            >
              <Icon className="h-4 w-4 shrink-0 text-text-secondary" />
              <span className="flex flex-col">
                <span className="text-body text-text-primary">{result.title}</span>
                {result.subtitle && (
                  <span className="text-caption text-text-secondary">{result.subtitle}</span>
                )}
              </span>
            </button>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
