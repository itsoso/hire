const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserInfo {
  name: string | null;
  bio: string | null;
  company: string | null;
  location: string | null;
  followers: number;
}

export interface Metrics {
  repo_influence: number;
  pr_quality: number;
  language_diversity: number;
  consistency: number;
  collaboration: number;
}

export interface Repo {
  name: string;
  stars: number;
}

export interface Candidate {
  username: string;
  overall_score: number;
  user_info: UserInfo;
  metrics: Metrics;
  languages: Record<string, number>;
  top_repos: Repo[];
}

export interface SearchResult {
  query: string;
  intent: Record<string, unknown>;
  candidates: Candidate[];
  total_found: number;
}

export interface DeveloperProfile {
  github_username: string;
  profile_summary: string;
  user_info: UserInfo;
  overall_score: number;
  metrics: Metrics;
  languages: Record<string, number>;
  top_repos: Repo[];
  pr_count: number;
  external_pr_count: number;
}

export interface NetworkConnection {
  username: string;
  interaction_count: number;
  relationship_types: string[];
  shared_repos: string[];
  strength: number;
}

export interface NetworkData {
  username: string;
  connections: NetworkConnection[];
  total_connections: number;
}

export interface ScholarPaper {
  title: string;
  year: number | null;
  citations: number;
  venue: string;
  author_position: number | null;
  total_authors: number;
}

export interface CoAuthor {
  name: string;
  papers_together: number;
}

export interface ScholarData {
  author_name: string;
  h_index: number;
  total_citations: number;
  paper_count: number;
  papers: ScholarPaper[];
  co_authors: CoAuthor[];
}

export async function searchCandidates(query: string): Promise<SearchResult> {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export async function getDeveloper(username: string): Promise<DeveloperProfile> {
  const res = await fetch(`${API_BASE}/api/developer/${username}`);
  if (!res.ok) throw new Error(`Developer not found: ${res.statusText}`);
  return res.json();
}

export async function getNetwork(username: string): Promise<NetworkData> {
  const res = await fetch(`${API_BASE}/api/developer/${username}/network`);
  if (!res.ok) throw new Error(`Network not found: ${res.statusText}`);
  return res.json();
}

export async function getScholar(username: string): Promise<ScholarData> {
  const res = await fetch(`${API_BASE}/api/developer/${username}/scholar`);
  if (!res.ok) throw new Error(`Scholar data not found: ${res.statusText}`);
  return res.json();
}

export async function analyzeUser(username: string): Promise<DeveloperProfile> {
  const res = await fetch(`${API_BASE}/api/analyze/${username}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
  return res.json();
}
