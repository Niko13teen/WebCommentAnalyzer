import re
import argparse
from requests_html import HTMLSession
from colorama import Fore
from bs4 import BeautifulSoup
from typing import List, NoReturn


requests = HTMLSession()


def get_links_from_page(url: str) -> List[str]:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        links = []

        for link in soup.find_all("a"):
            links.append(link.get("href"))

        for script in soup.find_all("script"):
            if script.get("src"):
                links.append(script.get("src"))

        for link in soup.find_all("link"):
            if link.get("href") and link.get("rel") == "stylesheet":
                links.append(link.get("href"))
                
        # Grabber media files 
        #for link in soup.find_all():
        #    if link.get("src") and not link.get("src").startswith("http"):
        #        links.append(link.get("src"))

        return links
    except Exception as error:
        return f"Error: {error}"


def crawl_site(base_url: str, max_depth: int) -> List[str]:
    try:
        visited = set()
        links_to_visit = [base_url]
        all_links = []

        while links_to_visit and max_depth > 0:
            current_url = links_to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            links = get_links_from_page(current_url)
            all_links.extend(links)

            for link in links:
                if (
                    link.startswith(base_url)
                    and link not in visited
                    and link not in links_to_visit
                ):
                    links_to_visit.append(link)

            max_depth -= 1

        return all_links

    except Exception as error:
        return f"Error: {error}"


def get_clean_links(all_links: List[str]) -> List[str]:
    pattern = r"(?:https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))?/(.*)"
    clean_urls = []

    for link in all_links:
        match = re.search(pattern, link)
        if match:
            clean_urls.append(match.group(3))

    return clean_urls


def get_page_code(url: str) -> str:
    response = requests.get(url)
    return response.text


def find_comments(code: str, comment_type: str) -> List[str]:
    if comment_type == "html":
        comment_regex = r"<!--.*?-->"
    elif comment_type == "css":
        comment_regex = r"/\*.*?\*/"
    elif comment_type == "js":
        comment_regex = r"//.*?\n"
    else:
        raise Exception(f"Неизвестный тип комментария: {comment_type}")

    return re.findall(comment_regex, code)


def search_comments(url: str) -> List[str]:
    try:
        code = get_page_code(url)

        if url.endswith(".js"):
            comments = find_comments(code, "js")
        elif url.endswith(".css"):
            comments = find_comments(code, "css")
        else:
            comments = find_comments(code, "html")

        return comments
    except Exception as error:
        return f"Error: {error}"


def main(base_url: str, max_depth: int = 5):
    preload_links = crawl_site(base_url, max_depth)
    clean_links = get_clean_links(preload_links)
    for link in clean_links:
        text = search_comments(f"{base_url}/{link}")
        if len("".join(text)) > 10:
            print(
                f"{Fore.RED}[+] Адрес: {base_url}/{link} {Fore.GREEN}| КОММЕНТАРИЙ: {text} | DEBUG: {len(''.join(text))}"
            )
        else:
            print(
                f"{Fore.RED}[-] Адрес: {base_url}/{link} {Fore.GREEN}| Не найдено! DEBUG: {len(''.join(text))}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        "-t",
        action="store",
        dest="target",
        help="https://example.com",
    )
    parser.add_argument(
        "--deep_scan",
        "-d",
        action="store",
        dest="deep_scan",
        help="1-10",
        default=5,
    )
    args = parser.parse_args()
    main(str(args.target), int(args.deep_scan))
