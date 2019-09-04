import sys

shading = 'fhe'
shape = 'sdo'
color = 'rpg'
number = '123'

spec = sys.argv[1]
t = [r.find(a) for (r,a) in zip((number,shape,color,shading),spec)]
n = sum(x*y for (x,y) in zip(t,[1,9,3,27]))
print('{}.png'.format(n+1))