import requests
import os
import re

from dotenv import load_dotenv
from generic_functions import is_allowed_filetype, escape_xml, process_ipynb_file, download_file

class GitMethods():
    def __init__(self, url):
        self.url = url
        self.headers = self.get_github_token()


    @staticmethod
    def get_github_token():
        load_dotenv()
        github_token = os.getenv('GITHUB_TOKEN')
        headers = {"Authorization": f"token {github_token}"}
        return headers

    def process_github_main_branch(self, repo_owner, repo_name):
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        repo_content = self.process_github_repo(repo_url)
        
        xml_formatted_repository = '<repository>\n'
        xml_formatted_repository += repo_content
        xml_formatted_repository += '</repository>\n'
        xml_formatted_repository += '</source>'

        return xml_formatted_repository

    def handle_git_url(self):
        if "/pull/" in self.url:
            final_output = self.process_github_pull_request()
        elif "/issues/" in self.url:
            final_output = self.process_github_issue()
        else:
            final_output = self.process_github_repo()

        return final_output
    
    def process_git_directory(self, url, repo_content):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        files = response.json()

        for file in files:
            if file["type"] == "file" and is_allowed_filetype(file["name"]):
                print(f"Processing {file['path']}...")

                temp_file = f"temp_{file['name']}"
                download_file(file["download_url"], temp_file, self.headers)

                repo_content.append(f'<file name="{escape_xml(file["path"])}">') 
                if file["name"].endswith(".ipynb"):
                    repo_content.append(escape_xml(process_ipynb_file(temp_file)))
                else:
                    with open(temp_file, "r", encoding='utf-8', errors='ignore') as f:
                        repo_content.append(escape_xml(f.read()))
                repo_content.append('</file>')
                os.remove(temp_file)

            elif file["type"] == "dir":
                self.process_git_directory(file["url"], repo_content)
            else:
                print(f"Skipped {file}")


    def process_github_repo(self, base_url=None):
        # Only possible for public repositories
        # Pull repository locally and use local path if private
        if not base_url:
            base_url = self.url

        print(base_url)
        api_base_url = "https://api.github.com/repos"
        repo_url_parts = base_url.split("https://github.com/")[-1].split("/")
        repo_name = "/".join(repo_url_parts[:2])

        # Detect if we have a branch or tag reference
        branch_or_tag = ""
        subdirectory = ""
        if len(repo_url_parts) > 2 and repo_url_parts[2] == "tree":
            # The branch or tag name should be at index 3
            if len(repo_url_parts) > 3:
                branch_or_tag = repo_url_parts[3]
            # Any remaining parts after the branch/tag name form the subdirectory
            if len(repo_url_parts) > 4:
                subdirectory = "/".join(repo_url_parts[4:])
        
        contents_url = f"{api_base_url}/{repo_name}/contents"
        if subdirectory:
            contents_url = f"{contents_url}/{subdirectory}"
        if branch_or_tag:
            contents_url = f"{contents_url}?ref={branch_or_tag}"

        # Configure a variable with a XML-like structure
        # This variable will be exported as a .txt file
        repo_content = [f'<source type="github_repository" url="{base_url}">']

        self.process_git_directory(contents_url, repo_content)
        repo_content.append('</source>')
        print("All files processed.")

        return "\n".join(repo_content)


    def process_github_pull_request(self):
        url_parts = self.url.split("/")
        repo_owner = url_parts[3]
        repo_name = url_parts[4]
        pull_request_number = url_parts[-1]
        api_base_url = "https://api.github.com/repos"

        pull_request_url = f"{api_base_url}/{repo_owner}/{repo_name}/pulls/{pull_request_number}"
        
    #region PR: Get changes and comments
        # 1. Get all metadata related to the PR
        response = requests.get(pull_request_url, headers=self.headers)
        pull_request_data = response.json()

        # 2. Get all changes made to the repository
        diff_url = pull_request_data["diff_url"]
        diff_response = requests.get(diff_url, headers=self.headers)
        pull_request_diff = diff_response.text

        # 3. Get all PR-level comments (general comments left on the submitted PR)
        comments_url = pull_request_data["comments_url"]
        comments_response = requests.get(comments_url, headers=self.headers)
        comments_data = comments_response.json()

        # 4. Get all code-level comments (comments on the changed files)
        review_comments_url = pull_request_data["review_comments_url"]
        review_comments_response = requests.get(review_comments_url, headers=self.headers)
        review_comments_data = review_comments_response.json()

        # 5. Sort the comments on their position
        all_comments = comments_data + review_comments_data
        all_comments.sort(key=lambda comment: comment.get("position") or float("inf"))
    #endregion


    #region PR: Add XML elements
        # Add opening element: pull_request_info
        formatted_text = f'<source type="github_pull_request" url="{self.url}">\n'
        formatted_text += '<pull_request_info>\n'

        # Add generic elements: title, description, merge_details
        formatted_text += f'<title>{escape_xml(pull_request_data["title"])}</title>\n'
        formatted_text += f'<description>{escape_xml(pull_request_data["body"])}</description>\n'
        formatted_text += '<merge_details>\n'
        formatted_text += f'{escape_xml(pull_request_data["user"]["login"])} wants to merge {pull_request_data["commits"]} commit into {repo_owner}:{pull_request_data["base"]["ref"]} from {pull_request_data["head"]["label"]}\n'
        formatted_text += '</merge_details>\n'

        # Iteratively add PR changes and comments left on PR as text fields
        # Parent element: diff_and_comments
        formatted_text += '<diff_and_comments>\n'
        diff_lines = pull_request_diff.split("\n")
        comment_index = 0

        for line in diff_lines:
            formatted_text += f'{escape_xml(line)}\n'
            while comment_index < len(all_comments) and all_comments[comment_index].get("position") == diff_lines.index(line):
                comment = all_comments[comment_index]
                # Comment element
                """
                <review_comment>
                    <author>xxx</author>
                    <content>xxx</content>
                    <path>xxx</path>
                    <line>xxx</line>
                </review_comment>
                """
                formatted_text += f'<review_comment>\n'
                formatted_text += f'<author>{escape_xml(comment["user"]["login"])}</author>\n'
                formatted_text += f'<content>{escape_xml(comment["body"])}</content>\n'
                formatted_text += f'<path>{escape_xml(comment["path"])}</path>\n'
                formatted_text += f'<line>{comment["original_line"]}</line>\n'
                formatted_text += '</review_comment>\n'
                comment_index += 1

        # Close open elements
        formatted_text += '</diff_and_comments>\n'
        formatted_text += '</pull_request_info>\n'

        # Regular processing of the repo
        formatted_text += self.process_github_main_branch(repo_owner, repo_name)
    #endregion

        print(f"Pull request {pull_request_number} and repository content processed successfully.")
        return formatted_text
        

    def process_github_issue(self):
        url_parts = self.issue_url.split("/")
        repo_owner = url_parts[3]
        repo_name = url_parts[4]
        issue_number = url_parts[-1]
        api_base_url = "https://api.github.com/repos"

        issue_url = f"{api_base_url}/{repo_owner}/{repo_name}/issues/{issue_number}"
    
    #region ISSUE: Get metadata
        response = requests.get(issue_url, headers=self.headers)
        issue_data = response.json()

        comments_url = issue_data["comments_url"]
        comments_response = requests.get(comments_url, headers=self.headers)
        comments_data = comments_response.json()
    #endregion


    #region ISSUE: Add XML elements
        # Add opening element: issue_info
        formatted_text = f'<source type="github_issue" url="{self.issue_url}">\n'
        formatted_text += '<issue_info>\n'

        # Add generic elements: title, description
        formatted_text += f'<title>{escape_xml(issue_data["title"])}</title>\n'
        formatted_text += f'<description>{escape_xml(issue_data["body"])}</description>\n'
        
        # Iteratively add comments left on PR as text fields
        # Parent element: comments
        formatted_text += '<comments>\n'

        for comment in comments_data:
            # Comment element
            """
            <comment>
                <author>xxx</author>
                <content>
                    <code_snippet>xxx</code_snippet>
                </content>
            </comment>
            """
            formatted_text += '<comment>\n'
            formatted_text += f'<author>{escape_xml(comment["user"]["login"])}</author>\n'
            formatted_text += f'<content>{escape_xml(comment["body"])}</content>\n'

            # Extract code snippets from comments on a GitHub issue
            # Regex: Find all occurrences of URLs in the comment body that match the pattern for GitHub file links with line ranges
            code_snippets = re.findall(r'https://github.com/.*#L\d+-L\d+', comment['body'])
            for snippet_url in code_snippets:
                # Split URL into two parts: the base URL and the line range.
                url_parts = snippet_url.split("#")

                # Use the FILE URL to get the raw contents of the file
                try:
                    file_url = url_parts[0].replace("/blob/", "/raw/")
                    file_response = requests.get(file_url, headers=self.headers)
                    file_content = file_response.text

                    # Using the file content, get the relevant code snippets back using the start and end indices
                    line_range = url_parts[1]
                    start_line, end_line = map(int, line_range.split("-")[0][1:]), map(int, line_range.split("-")[1][1:])
                    code_lines = file_content.split("\n")[start_line-1:end_line]
                    code_snippet = "\n".join(code_lines)

                    # Format the final code snippet using XML
                    formatted_text += '<code_snippet>\n'
                    formatted_text += f'<![CDATA[{code_snippet}]]>\n'
                    formatted_text += '</code_snippet>\n'
                except requests.exceptions.RequestException as e:
                    Warning(f"Error fetching file: {e}")
                    continue  # Skip to the next snippet if there's an error

            formatted_text += '</comment>\n'

        # Close open elements
        formatted_text += '</comments>\n'
        formatted_text += '</issue_info>\n'

        # Regular processing of the repo
        formatted_text += self.process_github_main_branch(repo_owner, repo_name)
    #endregion

        print(f"Issue {issue_number} and repository content processed successfully.")

        return formatted_text