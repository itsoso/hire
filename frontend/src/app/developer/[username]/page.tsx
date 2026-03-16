"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  getDeveloper,
  getNetwork,
  getScholar,
  DeveloperProfile,
  NetworkData,
  ScholarData,
} from "@/lib/api";

function MetricBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-500 w-32 capitalize">
        {label.replace("_", " ")}
      </span>
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className="bg-indigo-500 h-2 rounded-full transition-all"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-sm w-10 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}

function NetworkGraph({ data }: { data: NetworkData }) {
  if (data.connections.length === 0) {
    return <p className="text-gray-400 text-sm">No connections found.</p>;
  }
  return (
    <div className="space-y-3">
      {data.connections.slice(0, 10).map((conn) => (
        <div
          key={conn.username}
          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
        >
          <div>
            <a
              href={`/developer/${conn.username}`}
              className="font-medium text-indigo-600 hover:underline"
            >
              @{conn.username}
            </a>
            <div className="flex gap-1.5 mt-1">
              {conn.relationship_types.map((rt) => (
                <span
                  key={rt}
                  className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded"
                >
                  {rt.replace("_", " ")}
                </span>
              ))}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">
              {Math.round(conn.strength * 100)}%
            </div>
            <div className="text-xs text-gray-400">
              {conn.interaction_count} interactions
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ScholarSection({ data }: { data: ScholarData }) {
  if (data.papers.length === 0 && data.co_authors.length === 0) {
    return <p className="text-gray-400 text-sm">No academic data found.</p>;
  }
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-indigo-600">
            {data.h_index}
          </div>
          <div className="text-xs text-gray-500">h-index</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-indigo-600">
            {data.total_citations.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Citations</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-indigo-600">
            {data.paper_count}
          </div>
          <div className="text-xs text-gray-500">Papers</div>
        </div>
      </div>

      {data.papers.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Top Papers</h4>
          <div className="space-y-2">
            {data.papers.slice(0, 5).map((paper, i) => (
              <div
                key={i}
                className="flex items-start justify-between py-2 border-b border-gray-100"
              >
                <div className="flex-1 mr-4">
                  <p className="text-sm font-medium">{paper.title}</p>
                  <p className="text-xs text-gray-400">
                    {paper.venue} {paper.year && `· ${paper.year}`}
                    {paper.author_position !== null &&
                      ` · Position: ${paper.author_position + 1}/${paper.total_authors}`}
                  </p>
                </div>
                <span className="text-sm text-gray-500 whitespace-nowrap">
                  {paper.citations.toLocaleString()} citations
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.co_authors.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Top Co-Authors</h4>
          <div className="flex flex-wrap gap-2">
            {data.co_authors.slice(0, 8).map((ca) => (
              <span
                key={ca.name}
                className="px-3 py-1 bg-purple-50 text-purple-700 text-sm rounded-full"
              >
                {ca.name} ({ca.papers_together})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DeveloperPage() {
  const params = useParams();
  const username = params.username as string;

  const [profile, setProfile] = useState<DeveloperProfile | null>(null);
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [scholar, setScholar] = useState<ScholarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "network" | "scholar">("overview");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [profileData, networkData, scholarData] = await Promise.allSettled([
          getDeveloper(username),
          getNetwork(username),
          getScholar(username),
        ]);
        if (profileData.status === "fulfilled") setProfile(profileData.value);
        if (networkData.status === "fulfilled") setNetwork(networkData.value);
        if (scholarData.status === "fulfilled") setScholar(scholarData.value);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [username]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400">Loading profile for @{username}...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-gray-600">
          Developer @{username} not found
        </h2>
      </div>
    );
  }

  const tabs = [
    { id: "overview" as const, label: "Overview" },
    { id: "network" as const, label: `Network${network ? ` (${network.total_connections})` : ""}` },
    { id: "scholar" as const, label: "Academic" },
  ];

  return (
    <div>
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-8 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              {profile.user_info.name || username}
            </h1>
            <p className="text-gray-500 mt-1">
              @{username}
              {profile.user_info.company && ` · ${profile.user_info.company}`}
              {profile.user_info.location && ` · ${profile.user_info.location}`}
            </p>
            {profile.user_info.bio && (
              <p className="text-gray-600 mt-3">{profile.user_info.bio}</p>
            )}
          </div>
          <div className="text-center ml-8">
            <div className="w-20 h-20 rounded-full bg-indigo-100 flex items-center justify-center">
              <span className="text-3xl font-bold text-indigo-600">
                {Math.round(profile.overall_score * 100)}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">Overall Score</div>
          </div>
        </div>

        {profile.profile_summary && (
          <p className="text-gray-600 mt-4 leading-relaxed border-t border-gray-100 pt-4">
            {profile.profile_summary}
          </p>
        )}

        <div className="flex gap-3 mt-4">
          <a
            href={`https://github.com/${username}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50"
          >
            GitHub ↗
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.id
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold mb-4">Metrics</h3>
            <div className="space-y-3">
              {Object.entries(profile.metrics).map(([key, val]) => (
                <MetricBar key={key} label={key} value={val} />
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold mb-4">Languages</h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {Object.entries(profile.languages).map(([lang, pct]) => (
                <span
                  key={lang}
                  className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full"
                >
                  {lang} ({Math.round(pct * 100)}%)
                </span>
              ))}
            </div>

            <h3 className="font-semibold mb-4">Top Repositories</h3>
            <div className="space-y-2">
              {profile.top_repos.map((repo) => (
                <div
                  key={repo.name}
                  className="flex justify-between py-2 border-b border-gray-100"
                >
                  <span className="text-sm">{repo.name}</span>
                  <span className="text-sm text-gray-500">
                    ★ {repo.stars.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "network" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold mb-4">Collaboration Network</h3>
          {network ? (
            <NetworkGraph data={network} />
          ) : (
            <p className="text-gray-400 text-sm">Could not load network data.</p>
          )}
        </div>
      )}

      {activeTab === "scholar" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold mb-4">Academic Profile</h3>
          {scholar ? (
            <ScholarSection data={scholar} />
          ) : (
            <p className="text-gray-400 text-sm">Could not load academic data.</p>
          )}
        </div>
      )}
    </div>
  );
}
