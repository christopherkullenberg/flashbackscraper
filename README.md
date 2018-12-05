# Flashbackscraper
A simple python script for scraping Flasback forum threads.

## Requirements

* Python3
* Beautiful Soup 4

Install with:

    easy_install beautifulsoup4

or...

    pip install beautifulsoup4

## Usage, single thread mode

    python flashbackscraper.py -u <URL to flashback thread>


### Example

    python flashbackscraper.py -u https://www.flashback.org/t2977018

See the example_output folder for  sqlite3/csv files.

## Usage, multiple threads from file mode

    python flashbackscraper -f <file with newline separated urls>


### Example

    python flashbackscraper -f filewithurls.txt


## Extras

If you want to map the network created as an effect of the "quote" function in the Flashback forum, there is a script, ``sqlite2gexf.py`` that converts the scraped data to a .gexf file, which can be opened in for instance [Gephi](https://gephi.org). The script requires the module [networkx](https://networkx.github.io/), then you can simply run:

    python sqlite2gexf <name of sqlite3 file>

See the file ``t2977018.gexf`` for an example in the example_outputs folder. 
