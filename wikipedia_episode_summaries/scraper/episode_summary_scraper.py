import asyncio
import inspect
import os
import sys
import urllib.parse
from pathlib import Path
import bs4
import requests


class EpisodeSummaryScraper:

    def __init__(
        self,
        url_pattern: str,
        num_seasons: int,
        script_filepath: str = None
    ) -> None:
        """Initialize an EpisodeSummaryScraper.

        url_pattern - portion of the Wikipedia URL after the final '/' with
            '{}' as the season number, e.g., 'Adventure_Time_(season_{})'
        num_seasons - integer number of seasons
        script_filepath - (optional) path to script, which will be inferred
            if not provided
        """
        if not script_filepath:
            script_filepath = inspect.stack(0)[1].filename
        self.script_filepath = script_filepath
        self.url_pattern = url_pattern
        self.num_seasons = num_seasons

    def _table_of_contents(self) -> str:
        lines = []
        for season in range(1, self.num_seasons + 1):
            lines.append(f'- [Season {season}](#season-{season})')
        lines.append('___')
        return '\n'.join(lines) + '\n'

    async def _get_soup(self, url: str) -> bs4.BeautifulSoup:
        r = await asyncio.to_thread(requests.get, url)
        return bs4.BeautifulSoup(r.text.replace('<br />', ' '), 'html.parser')

    async def _season_episode_summaries(self, season: int) -> str:
        url = urllib.parse.urljoin(
            'https://en.wikipedia.org/wiki/',
            urllib.parse.quote(self.url_pattern.format(season))
        )
        lines = [f'## [Season {season}]({url})']
        soup = await self._get_soup(url)
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
            for part in range(2, hr_count + 2):
                lines.append(f'1. **{title_text} (Part {part})**')
        return '\n'.join(lines) + '\n'

    async def _main(self) -> None:
        show_title = self.url_pattern.partition('_(')[0].replace('_', ' ')
        page_title = '# ' + show_title + ' Episode Summaries'
        toc = self._table_of_contents()
        scrape_coroutines = (
            self._season_episode_summaries(season)
            for season in range(1, self.num_seasons + 1)
        )
        season_summaries = await asyncio.gather(*scrape_coroutines)
        script_path = Path(self.script_filepath)
        markdown_filename = script_path.stem + '.md'
        out_path = script_path.with_name(markdown_filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join([page_title, toc] + season_summaries))

    def scrape(self) -> None:
        """Collect all of a show's Wikipedia episode summaries across
        different seasons and write them into a markdown file.
        """
        asyncio.run(self._main())


if __name__ == '__main__':
    try:
        url_pattern, num_seasons = sys.argv[1:3]
        filepath = os.path.join(os.getcwd(), 'episode_summaries')
        EpisodeSummaryScraper(url_pattern, int(num_seasons), filepath).scrape()
    except ValueError:
        sys.exit(
            'Usage: python episode_summary_scraper.py url_pattern num_seasons'
        )
