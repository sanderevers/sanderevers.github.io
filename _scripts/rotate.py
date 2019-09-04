# brew install imagemagick

import subprocess

for nr in range(1,82):
    subprocess.run(['convert {}.png -rotate 90 {}r.png'.format(nr,nr)],shell=True)
