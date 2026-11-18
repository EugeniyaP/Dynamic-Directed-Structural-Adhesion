import os
import json
import time
import requests
import pandas as pd


class GitHubNetworkPipeline:
    """
    Collects longitudinal issue and pull-request comment threads via the GitHub REST API
    and constructs monthly directed knowledge-exchange edge lists (seeker -> responder).
    """

    def __init__(self, token, base_dir="./data"):
        if not token:
            raise ValueError(
                "GitHub API token is required. Set the GITHUB_TOKEN environment variable."
            )
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_dir = base_dir
        self.issues_dir = os.path.join(self.base_dir, "raw_threads")
        self.networks_dir = os.path.join(self.base_dir, "temporal_networks")

        os.makedirs(self.issues_dir, exist_ok=True)
        os.makedirs(self.networks_dir, exist_ok=True)

    def _handle_rate_limit(self, response):
        """Dynamically pause execution until the GitHub API rate limit resets."""
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
        sleep_time = max(10, reset_time - int(time.time()) + 2)
        print(f"\nGitHub API rate limit reached. Waiting {sleep_time} seconds...")
        time.sleep(sleep_time)

    def download_open_and_closed_threads(self, owner, repo):
        """Download all open and closed issues and pull requests for a repository."""
        all_threads = []
        project_name = f"{owner}_{repo}"
        print(f"--- COLLECTING THREADS FOR: {project_name} ---")

        for state in ["open", "closed"]:
            state_count = 0
            url = f"https://github.com{owner}/{repo}/issues?per_page=100&page=1&state={state}"
            print(f"Fetching {state} threads: {url}")

            while url:
                try:
                    res = requests.get(url, headers=self.headers, timeout=15)

                    if res.status_code in (403, 429):
                        self._handle_rate_limit(res)
                        continue
                    elif res.status_code != 200:
                        print(f"API Error (HTTP {res.status_code}). Stopping {state} fetch.")
                        break

                    data = res.json()
                    if not isinstance(data, list) or len(data) == 0:
                        break

                    for item in data:
                        item["thread_type"] = (
                            "pull_request" if "pull_request" in item else "issue"
                        )

                    all_threads.extend(data)
                    state_count += len(data)

                    url = res.links["next"]["url"] if "next" in res.links else None
                    time.sleep(0.2)

                except Exception as e:
                    print(f"Network error while fetching threads, retrying... ({e})")
                    time.sleep(5)
                    continue

            print(f"Collected {state} threads: {state_count}")

        output_file = os.path.join(
            self.issues_dir, f"threads_{owner}_{repo}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_threads, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(all_threads)} total threads to: {output_file}\n")

    def build_temporal_networks(self, owner, repo):
        """
        Parse thread comments and construct monthly directed interaction graphs.
        Directed edge (u -> v) indicates that seeker u received expertise/response from responder v.
        """
        project_name = f"{owner}_{repo}"
        threads_path = os.path.join(
            self.issues_dir, f"threads_{owner}_{repo}.json"
        )

        if not os.path.exists(threads_path):
            print(f"Threads file not found: {threads_path}")
            return

        print(f"--- BUILDING TEMPORAL NETWORKS FOR: {project_name} ---")

        with open(threads_path, "r", encoding="utf-8") as f:
            threads_data = json.load(f)

        all_interactions = []
        total_threads = len(threads_data)

        for k, thread in enumerate(threads_data):
            if not thread.get("user"):
                continue
            id_seeker = thread["user"]["id"]
            current_url = f"{thread['comments_url']}?per_page=100"

            if k % 50 == 0:
                print(f"Processed discussions: {k}/{total_threads}...")

            time.sleep(0.2)

            while current_url:
                try:
                    res = requests.get(current_url, headers=self.headers, timeout=10)

                    if res.status_code in (403, 429):
                        self._handle_rate_limit(res)
                        continue
                    elif res.status_code != 200:
                        break

                    comments_list = res.json()
                    if not isinstance(comments_list, list) or len(comments_list) == 0:
                        break

                    for comment in comments_list:
                        if not comment.get("user"):
                            continue
                        id_responder = comment["user"]["id"]
                        year_month = comment["created_at"][:7]

                        all_interactions.append({
                            "seeker": id_seeker,
                            "responder": id_responder,
                            "timestamp": year_month,
                        })

                    current_url = (
                        res.links["next"]["url"] if "next" in res.links else None
                    )
                    if current_url:
                        time.sleep(0.2)

                except Exception as e:
                    print(f"Network error on thread {k}, retrying... ({e})")
                    time.sleep(5)
                    continue

        df = pd.DataFrame(all_interactions)
        if df.empty:
            print("No directed interactions found.")
            return

        # Exclude self-loops
        df = df[df["seeker"] != df["responder"]]

        project_network_dir = os.path.join(
            self.networks_dir, f"temporal_networks_{owner}_{repo}"
        )
        os.makedirs(project_network_dir, exist_ok=True)

        unique_months = sorted(df["timestamp"].unique())
        print(f"Detected monthly snapshots: {len(unique_months)}")

        for month in unique_months:
            df_t = df[df["timestamp"] == month]
            unique_edges = df_t[["seeker", "responder"]].drop_duplicates()

            date_suffix = month.replace("-", "_")
            file_path = os.path.join(
                project_network_dir, f"time_edge_list_file_{date_suffix}.txt"
            )
            unique_edges.to_csv(file_path, sep=" ", index=False, header=False)

        print(f"Monthly edge lists saved to: {project_network_dir}\n")


if __name__ == "__main__":
    # Set your token in terminal before running: export GITHUB_TOKEN="your_token_here"
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    pipeline = GitHubNetworkPipeline(token=GITHUB_TOKEN)

    pipeline.download_open_and_closed_threads("google", "zx")
    pipeline.build_temporal_networks("google", "zx")
