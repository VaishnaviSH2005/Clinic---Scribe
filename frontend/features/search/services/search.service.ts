import { apiClient } from "@/lib/api-client";
import type { SearchResults } from "@/types/search";

export const searchService = {
  search: (q: string) => apiClient.get<SearchResults>(`/search?q=${encodeURIComponent(q)}`),
};
