"""
julian.py

Calculate Julian date format. Borrowed from:
http://www.pauahtun.org/julian_period.html
"""
import os, sys, math, time 

def main():
    print now()

def now():
    """Return today's date in Julian format"""
    return julian_from_tuple(time.localtime(time.time()))

def julian_from_tuple(tup):
    """Turn a 9-tuple of time data into Julian Format"""
    iyyy, mm, id = tup[0], tup[1], tup[2]

    tm = 0.0
    if mm > 2 :
	    jy = iyyy
	    jm = mm + 1
    else :
	    jy = iyyy - 1
	    jm = mm + 13

    jul = int ( math.floor ( 365.25 * jy ) +
        math.floor ( 30.6001 * jm ) + ( id + 1720995.0 + tm ) )
    ja  = int ( 0.01 * jy )
    jul = int ( jul + ( 2 - ja + ( int ( 0.25 * ja ) ) ) )

    return jul

if __name__=='__main__': main()
