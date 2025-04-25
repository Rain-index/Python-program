import sys
import time
from urllib.parse import urljoin, urlparse
from collections import deque
import requests
from bs4 import BeautifulSoup


def get_random_url():
    try:
        response = requests.get(
            'https://en.wikipedia.org/wiki/Special:Random',
            allow_redirects=True
        )
        return response.url
    except requests.RequestException:
        return None


def is_valid_link(href):
    if not href.startswith('/wiki/'):
        return False
    parts = href.split('/wiki/')[1].split('#')[0]
    if ':' in parts:
        return False
    return True


def get_links(url, rate_limit):
    time.sleep(rate_limit)  # Rate limiting
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find(id='mw-content-text')
    reflist = soup.find('div', class_='reflist')
    links = []
    if content:
        for a in content.find_all('a', href=True):
            href = a['href']
            if is_valid_link(href):
                links.append(href)
    if reflist:
        for a in reflist.find_all('a', href=True):
            href = a['href']
            if is_valid_link(href):
                links.append(href)
    base_url = 'https://en.wikipedia.org'
    clean_links = []
    for href in links:
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        clean_url = parsed._replace(fragment='', query='').geturl()
        clean_links.append(clean_url)
    return list(set(clean_links))


def bidirectional_bfs(start_url, end_url, rate_limit):
    forward_queue = deque([(start_url, 0)])
    forward_visited = {start_url: (None, 0)}
    backward_queue = deque([(end_url, 0)])
    backward_visited = {end_url: (None, 0)}

    while forward_queue or backward_queue:
        # Expand forward level
        current_level_size = len(forward_queue)
        for _ in range(current_level_size):
            current_url, depth = forward_queue.popleft()
            if depth > 5:
                continue
            # Check if current_url is in backward_visited
            if current_url in backward_visited:
                backward_depth = backward_visited[current_url][1]
                if depth + backward_depth <= 5:
                    path = construct_path(current_url, forward_visited, backward_visited)
                    return path
            # Fetch links
            links = get_links(current_url, rate_limit)
            for link in links:
                if link not in forward_visited:
                    forward_visited[link] = (current_url, depth + 1)
                    forward_queue.append((link, depth + 1))

        # Expand backward level
        current_level_size = len(backward_queue)
        for _ in range(current_level_size):
            current_url, depth = backward_queue.popleft()
            if depth > 5:
                continue
            # Check if current_url is in forward_visited
            if current_url in forward_visited:
                forward_depth = forward_visited[current_url][1]
                if depth + forward_depth <= 5:
                    path = construct_path(current_url, forward_visited, backward_visited)
                    return path
            # Fetch links
            links = get_links(current_url, rate_limit)
            for link in links:
                if link not in backward_visited:
                    backward_visited[link] = (current_url, depth + 1)
                    backward_queue.append((link, depth + 1))

    return None

def construct_path(node, forward_visited, backward_visited):
    # 前向路径：node → 起点
    forward_path = []
    current = node
    while current is not None:
        forward_path.append(current)
        current = forward_visited.get(current, (None, 0))[0]
    forward_path.reverse()  # 反转为：起点 → node

    # 后向路径：node → 终点
    backward_path = []
    current = node
    while current is not None:
        backward_path.append(current)
        current = backward_visited.get(current, (None, 0))[0]
    # 合并后向路径为：node → 终点（无需反转）

    # 合并路径：起点 → node → 终点
    merged_path = forward_path + backward_path[1:]
    merged_path_re = merged_path.reverse()
    return merged_path, merged_path_re  # 直接返回，无需反转
# def construct_path(node, forward_visited, backward_visited):
#     # Build forward path
#     forward_path = []
#     current = node
#     while current is not None:
#         forward_path.append(current)
#         current = forward_visited.get(current, (None, 0))[0]
#     forward_path.reverse()
#
#     # Build backward path
#     backward_path = []
#     current = node
#     while current is not None:
#         backward_path.append(current)
#         current = backward_visited.get(current, (None, 0))[0]
#     # The backward path is from node to end_url, reverse to get end_url to node
#     backward_path = backward_path[::-1]
#
#     # Merge paths and reverse to show from end_url to start_url
#     merged_path = forward_path + backward_path[1:]
#     merged_path.reverse()
#     return merged_path


def main():
    rate_limit = 1  # 默认速率限制1秒
    if len(sys.argv) >= 2:
        rate_limit = float(sys.argv[1])

    url1, url2 = None, None
    while url1 is None:
        url1 = get_random_url()
    while url2 is None:
        url2 = get_random_url()
    print(f"URL1: {url1}")
    print(f"URL2: {url2}")

    path = bidirectional_bfs(url1, url2, rate_limit)
    if path:
        print(" => ".join(path))
    else:
        print("No path found within 5 transitions.")

    if path:
        print(f"Path from URL1 to URL2:")
        print(" => ".join(path))
    else:
        print("No path found within 5 transitions.")


if __name__ == "__main__":
    main()