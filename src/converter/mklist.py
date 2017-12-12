import sys

print '['
first = True
for line in sys.stdin.readlines():
    if not first: print ','
    print line
    first = False
print ']'
