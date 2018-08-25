## pelican-confluence

This is how I construct my website [kbni.net.au](https://kbni.net.au) using content retrieved from my personal
Confluence instance using Python and then fed to [Pelican](https://github.com/getpelican/pelican), a static-site generator.

A brief explaination of the contents of this repoistory:

 * `confluence2pelican/` - The actual Python module used for retrieving content from Confluence prior to pelican runs
 * `data/` - 
   * `data/theme/` - The theme I use for Pelican
   * `data/settings.json.example` - Configuration file for confluence2pelican
   * `data/pelicanconf.py` - The configuration file for pelican
 * `pelican.sh` - The script I run when I've added content to my Confluence to update my website

For more information about this repository, head on over to https://kbni.net.au/projects/confluence2pelican/

