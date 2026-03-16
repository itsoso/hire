"use client";

import { useState } from "react";
import { searchCandidates, SearchResult, Candidate } from "@/lib/api";

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-28 text-gray-500">{label}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className="bg-indigo-500 h-2 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-gray-600">{pct}%</span>
    </div>
  );
}

function CandidateCard({ candidate }: { candidate: Candidate }) {
  const { username, overall_score, user_info, metrics, languages, top_repos } =
    candidate;
  return (
    <a
      href={`/developer/${username}`}
      className="block bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{user_info.name || username}</h3>
          <p className="text-sm text-gray-500">
            @{username}
            {user_info.company && ` · ${user_info.company}`}
            {user_info.location && ` · ${user_info.location}`}
          </p>
        </div>
        <div className="text-2xl font-bold text-indigo-600">
          {Math.round(overall_score * 100)}
        </div>
      </div>

      <div className="space-y-1.5 mb-4">
        <ScoreBar score={metrics.repo_influence} label="Repo Influence" />
        <ScoreBar score={metrics.pr_quality} label="PR Quality" />
        <ScoreBar score={metrics.collaboration} label="Collaboration" />
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {Object.keys(languages)
          .slice(0, 5)
          .map((lang) => (
            <span
              key={lang}
              className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs rounded-full"
            >
              {lang}
            </span>
          ))}
      </div>

      <div className="text-xs text-gray-400">
        Top repos:{" "}
        {top_repos
          .slice(0, 3)
          .map((r) => `${r.name} (★${r.stars})`)
          .join(", ")}
      </div>
    </a>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await searchCandidates(query);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-3">Find Top Developers</h1>
        <p className="text-gray-500 text-lg">
          Search by skills, contributions, and real-world impact
        </p>
      </div>

      <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-10">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='Try "Find ML engineers who know PyTorch" or "Rust systems programmers"'
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-base"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {error && (
        <div className="max-w-2xl mx-auto mb-6 p-4 bg-red-50 text-red-700 rounded-xl">
          {error}
        </div>
      )}

      {result && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">
              {result.total_found} candidate{result.total_found !== 1 && "s"}{" "}
              found
            </h2>
            {result.intent.role_type ? (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                {String(result.intent.role_type).replace("_", " ")}
              </span>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {result.candidates.map((c) => (
              <CandidateCard key={c.username} candidate={c} />
            ))}
          </div>

          {result.total_found === 0 && (
            <p className="text-center text-gray-400 py-12">
              No candidates matched your search. Try broader terms.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
