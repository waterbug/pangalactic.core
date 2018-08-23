# $Id$

from pangalactic.meta.utils      import extract
from pangalactic.node.uberorb    import UberORB
from pangalactic.test.utils4test import gen_linked_test_objects

ORB = UberORB(home='pangalaxian_test')
# if problems with ORB, use this to get log messages:
# ORB = UberORB(debug=True)
ORB.initCache(home='pangalaxian_test')
test_objects = gen_linked_test_objects('TFR', ORB)

for o in test_objects:
    ex = extract(o)
    # print '\n============================'
    # print 'Extract of %s:' % o.id
    # print '============================'
    # pprint(ex)
    # print
    print '========================================================='
    print
    print """Command:  ORB.remember(ex)"""
    print """--------"""

    rembd = ORB.remember(ex)

    print '\n============================'
    print '%s remembered:' % o.id
    print '============================'
    print rembd
    print
    print '========================================================='

# profile.run('test()', 'testprof')
# p = pstats.Stats('testprof')
# p.sort_stats('cumulative').print_stats(10)

