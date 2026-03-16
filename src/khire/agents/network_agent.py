from __future__ import annotations

from khire.clients.github import GitHubClient


class NetworkAgent:
    """Builds collaboration network from GitHub data."""

    def __init__(self, github_client: GitHubClient | None = None):
        self.gh = github_client or GitHubClient()

    async def build_network(self, username: str, events: list[dict] | None = None) -> dict:
        """Build a collaboration network for a GitHub user.

        Extracts relationships from:
        - Co-contributors to same repos (via events)
        - PR review interactions
        - Shared repository contributions
        """
        if events is None:
            events = await self.gh.get_events(username)

        collaborators: dict[str, dict] = {}

        for event in events:
            repo_name = event.get("repo", {}).get("name", "")
            event_type = event.get("type", "")

            if event_type == "PullRequestEvent":
                pr = event.get("payload", {}).get("pull_request", {})
                # The repo owner is a collaborator if it's not the user's own repo
                repo_owner = repo_name.split("/")[0] if "/" in repo_name else ""
                if repo_owner and repo_owner != username:
                    self._add_collaborator(
                        collaborators, repo_owner,
                        relationship="contributed_to_repo",
                        repo=repo_name,
                    )

            elif event_type == "PullRequestReviewEvent":
                pr = event.get("payload", {}).get("pull_request", {})
                pr_author = pr.get("user", {}).get("login", "")
                if pr_author and pr_author != username:
                    self._add_collaborator(
                        collaborators, pr_author,
                        relationship="reviewed_pr",
                        repo=repo_name,
                    )

            elif event_type == "IssuesEvent":
                repo_owner = repo_name.split("/")[0] if "/" in repo_name else ""
                if repo_owner and repo_owner != username:
                    self._add_collaborator(
                        collaborators, repo_owner,
                        relationship="issue_interaction",
                        repo=repo_name,
                    )

        # Convert to list and compute strength
        network = []
        for login, data in collaborators.items():
            network.append({
                "username": login,
                "interaction_count": data["count"],
                "relationship_types": list(data["relationships"]),
                "shared_repos": list(data["repos"]),
                "strength": min(data["count"] / 5, 1.0),
            })

        network.sort(key=lambda x: x["strength"], reverse=True)

        return {
            "username": username,
            "connections": network[:20],
            "total_connections": len(network),
        }

    def _add_collaborator(
        self,
        collaborators: dict[str, dict],
        login: str,
        relationship: str,
        repo: str,
    ):
        if login not in collaborators:
            collaborators[login] = {
                "count": 0,
                "relationships": set(),
                "repos": set(),
            }
        collaborators[login]["count"] += 1
        collaborators[login]["relationships"].add(relationship)
        collaborators[login]["repos"].add(repo)
