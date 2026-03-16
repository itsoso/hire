"use client";

import { useState } from "react";
import { analyzeUser, DeveloperProfile } from "@/lib/api";

export default function AnalyzePage() {
  const [username, setUsername] = useState("");
  const [profile, setProfile] = useState<DeveloperProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await analyzeUser(username);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-3">Analyze a Developer</h1>
        <p className="text-gray-500 text-lg">
          Enter a GitHub username to generate a contribution-based profile
        </p>
      </div>

      <form onSubmit={handleAnalyze} className="max-w-md mx-auto mb-10">
        <div className="flex gap-3">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="GitHub username (e.g. karpathy)"
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </form>

      {error && (
        <div className="max-w-md mx-auto mb-6 p-4 bg-red-50 text-red-700 rounded-xl">
          {error}
        </div>
      )}

      {profile && (
        <div className="max-w-2xl mx-auto bg-white rounded-xl border border-gray-200 p-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">
                {profile.user_info.name || profile.github_username}
              </h2>
              <p className="text-gray-500">
                @{profile.github_username}
                {profile.user_info.company &&
                  ` · ${profile.user_info.company}`}
              </p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600">
                {Math.round(profile.overall_score * 100)}
              </div>
              <div className="text-xs text-gray-400">Score</div>
            </div>
          </div>

          {profile.profile_summary && (
            <p className="text-gray-600 mb-6 leading-relaxed">
              {profile.profile_summary}
            </p>
          )}

          <div className="grid grid-cols-2 gap-4 mb-6">
            {Object.entries(profile.metrics).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="text-sm text-gray-500 w-32 capitalize">
                  {key.replace("_", " ")}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-500 h-2 rounded-full"
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-10 text-right">
                  {Math.round(value * 100)}%
                </span>
              </div>
            ))}
          </div>

          <div className="mb-6">
            <h3 className="font-semibold mb-2">Languages</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(profile.languages).map(([lang, pct]) => (
                <span
                  key={lang}
                  className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full"
                >
                  {lang} ({Math.round(pct * 100)}%)
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Top Repositories</h3>
            <div className="space-y-2">
              {profile.top_repos.map((repo) => (
                <div
                  key={repo.name}
                  className="flex items-center justify-between py-2 border-b border-gray-100"
                >
                  <span className="text-sm">{repo.name}</span>
                  <span className="text-sm text-gray-500">
                    ★ {repo.stars.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <a
              href={`/developer/${profile.github_username}`}
              className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Full Profile
            </a>
            <a
              href={`https://github.com/${profile.github_username}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50 transition-colors"
            >
              GitHub ↗
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
