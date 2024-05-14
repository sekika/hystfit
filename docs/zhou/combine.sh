#!/bin/sh
convert +append zhou-2013-fig6a.png zhou-2013-fig6b.png ab.png
convert +append zhou-2013-fig6c.png zhou-2013-fig6d.png cd.png
convert -append ab.png cd.png zhou-2013-fig6.png
rm -f ab.png cd.png
