export interface SearchResultItem {
  id: string;
  type: "patient" | "appointment" | "consultation" | "report" | "user";
  title: string;
  subtitle: string | null;
  href: string;
}

export interface SearchResults {
  query: string;
  results: SearchResultItem[];
}
