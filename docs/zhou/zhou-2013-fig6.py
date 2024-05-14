#!/usr/bin/env python3
#
# Sample code of hystfit to draw Fig.6 of Zhou (2013)
#
# Zhou, A. (2013) A contact angle-dependent hysteresis model for soil–water retention behaviour.
#   Computers and Geotechnics 49: 36-42. https://doi.org/10.1016/j.compgeo.2012.10.004
#
# Author: Katsutoshi Seki
# License: MIT License

def draw_zhou(fig_label, angle, b, theta_hyst):
    import hystfit
    import math
    import matplotlib.pyplot as plt
    # Parameters
    a = 1 / 180
    n = 1.65
    p = (math.cos(math.radians(angle)), b)

    # Figure preparation
    fig, ax1 = plt.subplots(figsize=[4.3, 3.2])
    ax1.set_xscale("log")
    fig.subplots_adjust(top=0.95, bottom=0.15, right=0.95, left=0.15)
    ax1.axis([1, 10000, 0, 1])
    ax1.set_xlabel('h (kPa)')
    ax1.set_ylabel('Se')
    ax1.text(10 ** 0.4, 0.1,
             f'$\\alpha^{{-1}} = {int(1/a)}$ kPa\nn = {n:.02f}\n$\\gamma_A = {angle}^\\circ$\nb = {b:.2f}')

    # Plotting
    f = hystfit.Fit()
    f.set_vg(1, 0, a, n)
    theta = f.smooth_theta((1, 0.07, 1, 0.3) + theta_hyst)
    h = f.h(p, theta)
    ax1.plot(h, theta, marker='', linestyle='solid', color='black')
    plt.savefig(f'zhou-2013-fig6{fig_label}.png')


figs = {'a': (85, 0.3, (0.70, 0.55, 0.90, 0.80)),
        'b': (85, 0.6, (0.85, 0.55, 0.95, 0.80)),
        'c': (70, 0.3, (0.92, 0.91, 0.55, 0.98)),
        'd': (70, 0.6, (0.92, 0.91, 0.55, 0.98))}
for label in figs:
    draw_zhou(label, *figs[label])
