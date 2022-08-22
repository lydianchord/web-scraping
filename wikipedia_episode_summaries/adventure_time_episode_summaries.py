import asyncio
from pathlib import Path
from typing import Final
import bs4
import requests

URL_PATTERN: Final = 'https://en.wikipedia.org/wiki/Adventure_Time_(season_{})'
NUM_SEASONS: Final = 10


async def get_soup(url: str) -> bs4.BeautifulSoup:
    r = await asyncio.to_thread(requests.get, url)
    return bs4.BeautifulSoup(r.text)


async def season_episode_summaries(season: int) -> str:
    lines = [f'## Season {season}']
    url = URL_PATTERN.format(season)
    soup = await get_soup(url)
    print(url)
    ep_numbers = soup.select('tr.vevent th[scope="row"]')
    ep_titles = soup.select('td.summary')
    ep_summaries = soup.select('td.description')
    for ep_num, title, summary in zip(ep_numbers, ep_titles, ep_summaries):
        title_text = title.get_text().strip()
        summary_text = summary.get_text().strip().replace('\n', ' ')
        episode_line = f'1. **{title_text}** - {summary_text}'
        lines.append(episode_line)
        hr_count = len(ep_num.select('hr'))
        for i in range(hr_count):
            lines.append(f'1. **{title_text} (Part {i + 2})**')
    lines.append('')
    return '\n'.join(lines)


async def main() -> None:
    script_path = Path(__file__)
    script_name = script_path.stem
    title = '# ' + ' '.join(script_name.split('_')).title()
    scrape_coroutines = [
        season_episode_summaries(i)
        for i in range(1, NUM_SEASONS + 1)
    ]
    season_summaries = await asyncio.gather(*scrape_coroutines)
    joined_summaries = '\n'.join(season_summaries)
    out_path = script_path.with_name(script_name + '.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'{title}\n\n{joined_summaries}')


if __name__ == '__main__':
    asyncio.run(main())
