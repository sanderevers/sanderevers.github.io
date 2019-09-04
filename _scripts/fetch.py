import subprocess

for nr in range(1,82):
    subprocess.run(['curl https://www.setgame.com/sites/all/modules/setgame_set/assets/images/new/{}.png > {}.png'.format(nr,nr)],shell=True)
