import subprocess

for nr in range(1,82):
    subprocess.run(['rm {}.png'.format(nr)],shell=True)
