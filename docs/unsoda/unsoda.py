#!/usr/bin/env python3
#
# Fit UNSODA data with hystfit
#
# Author: Katsutoshi Seki
# License: MIT License
import numpy as np


def main():
    import argparse
    import requests
    import hystfit
    # Create fitting object f
    f = hystfit.Fit()
    # Output markdown when invoked with -m option
    parser = argparse.ArgumentParser(
        description='Fit UNSODA data with hystfit')
    parser.add_argument('-m', '--markdown',
                        action='store_true', help='output in markdown')
    f.markdown = parser.parse_args().markdown
    f.no_warn = f.markdown
    # Load UNSODA data converted to JSON
    # See document at https://sekika.github.io/file/unsoda/
    unsoda_url = 'https://sekika.github.io/file/unsoda/unsoda.json'
    response = requests.get(unsoda_url)
    assert response.status_code == 200
    j = response.json()
    # Load UNSODA tables
    general = j['general']
    dry = j['lab_drying_h-t']  # Laboratory drying curve
    wet = j['lab_wetting_h-t']  # Laboratory wetting curve
    prop = j['soil_properties']
    f.pub_id = j['publication']
    # Prepare data and call calculation functions
    count_fig = 0
    for id in dry:
        # Skip some data because
        # 4690: Identical drying and wetting curve (no hysteresis)
        # 4870, 4880: Wetting curve begins much drier than the measured drying curve,
        #             and therefore, the drying curve requires excessive extrapolation
        # 4921: 2 wetting curves are mixed
        if int(id) in [4690, 4870, 4880, 4921]:
            continue
        f.general = general[id]
        # Select data which have more than 3 data points in the wetting curve
        if id in wet and len(wet[id][0]) > 3:
            # Set drying data
            h, t = dry[id]
            f.swrc = (np.array(h), np.array(t))
            # Check is theta_s is available
            if 'theta_sat' in prop[id]:
                qs = prop[id]['theta_sat']
                if qs == '':
                    f.qs = 0
                else:
                    f.qs = float(qs)
            else:
                f.qs = 0
            # Set wetting data in the order of wetting
            h, t = wet[id]
            if t[0] > t[-1]:
                h = h[::-1]
                t = t[::-1]
            f.swrc_wet = (np.array(h), np.array(t))
            # Calculate parameters of drying curve
            f = calc_dry(f)
            # Select data with good the drying curve
            if f.r2_ht < 0.98:
                if not f.markdown:
                    print(f'Skipping UNSODA {id} where R2 = {f.r2_ht:.3}')
                continue
            # Calculate parameters of the wetting curve
            f = calc_wet(f)
            # Output the result and draw a figure
            output(f)
            draw_figure(f)
            count_fig += 1
    if not f.markdown:
        print(f'{count_fig} figures were produced.')


def calc_dry(f):
    """Calculation of drying curve"""
    if f.qs == 0:
        # theta_s is not measured
        f.set_model('VG', const=['qr=0', 'q=1'])
        f.ini = (max(f.swrc[1]), *f.get_init())
        f.optimize()
        vg_aic = f.aicc_ht
        f.set_model('FX', const=['qr=0'])
        f.ini = (max(f.swrc[1]), *f.get_init())
        f.optimize()
        # Compare corrected AIC of VG and FX
        if vg_aic < f.aicc_ht:
            f.set_model('VG', const=['qr=0', 'q=1'])
            f.ini = (max(f.swrc[1]), *f.get_init())
            f.optimize()
            f.qs, a, m = f.fitted
            n = 1 / (1 - m)
            f.message_dry = f'qs = {f.qs:.3} alpha = {a:.3} n = {n:.3}'
            f.qs_wet = qs_wet(f)
            f.set_vg(f.qs_wet, 0, a, n)
        else:
            f.message_dry = f.message
            f.qs, a, m, n = f.fitted
            f.qs_wet = qs_wet(f)
            f.set_fx(f.qs_wet, 0, a, m, n)
    else:
        # theta_s is measured
        f.set_model('VG', const=[f'qs={f.qs}', 'qr=0', 'q=1'])
        f.ini = f.get_init()
        f.optimize()
        vg_aic = f.aicc_ht
        f.set_model('FX', const=[f'qs={f.qs}', 'qr=0'])
        f.ini = f.get_init()
        f.optimize()
        # Compare corrected AIC of VG and FX
        if vg_aic < f.aicc_ht:
            f.set_model('VG', const=[f'qs={f.qs}', 'qr=0', 'q=1'])
            f.ini = f.get_init()
            f.optimize()
            a, m = f.fitted
            n = 1 / (1 - m)
            f.message_dry = f'qs = {f.qs:.3} alpha = {a:.3} n = {n:.3}'
            f.qs_wet = qs_wet(f)
            f.set_vg(f.qs_wet, 0, a, n)
        else:
            f.message_dry = f.message
            a, m, n = f.fitted
            f.qs_wet = qs_wet(f)
            f.set_fx(f.qs_wet, 0, a, m, n)
    return f


def qs_wet(f):
    """Change theta_s of wetting curve from the drying curve in some conditions"""
    if max(f.swrc_wet[1]) > f.qs:
        return max(f.swrc_wet[1])
    if min(f.swrc_wet[0]) > 2:
        return f.qs
    if max(f.swrc_wet[1]) < 0.95 * f.qs:
        return max(f.swrc_wet[1])
    return f.qs


def calc_wet(f):
    """Calculation of wetting curve"""
    h, t = f.swrc_wet
    # If there is a point of water content over saturation, omit it for fitting
    if h[-1] == 0 or t[-1] >= f.qs_wet:
        h = h[:-1]
        t = t[:-1]
        f.omit = True
    else:
        f.omit = False
    # Fit wetting curve
    f.opt(h, t)
    return f


def output(f):
    """Output the result"""
    texture = f.general['texture']
    d = f.general['keyword'].split(', ')
    if 'disturbed' in d[0]:
        disturbed = d[0]
    else:
        disturbed = d[1]
    pub_id = f.general['publication_ID']
    publication = f.pub_id[pub_id]
    id = int(f.general['code'])
    if f.markdown:
        print(f'### <a name="{id}"></a>UNSODA {id} {texture} ({disturbed})')
        print(f'- [Full data](https://sekika.github.io/unsoda/?{id})')
        if pub_id != '999':
            print(f'- {publication}')
        message = f.message_dry.replace(
            'qs', '&theta;<sub>s</sub>').replace('alpha', '&alpha;')
        print(f'- {f.model_name}: {message} R<sup>2</sup> = {f.r2_ht:.4f}')
        message = f.message.replace('(γA)', '&gamma;<sub>A</sub>')
        print(f'- Zhou: {message} R<sup>2</sup> = {f.r2:.3}')
        if f.qs != f.qs_wet:
            print(
                f'- &theta;<sub>s</sub> = {f.qs:.3} for drying and &theta;<sub>s</sub> = {f.qs_wet:.3} for wetting')
        print(f'![Figure of UNSODA {id}](unsoda/unsoda{id}.png)')
    else:
        print(f'UNSODA {id} {texture} https://sekika.github.io/unsoda/?{id}')
        print(f'{f.model_name}: {f.message_dry} R2 = {f.r2_ht:.4f}')
        if f.omit:
            print('Omitting saturated point')
        print(f'Zhou: {f.message} R2 = {f.r2:.3}')
        if f.qs != f.qs_wet:
            print(
                f'qs = {f.qs:.3} for drying and qs = {f.qs_wet:.3} for wetting')


def draw_figure(f):
    """Draw a figure"""
    import math
    import matplotlib.pyplot as plt
    id = int(f.general['code'])
    min_x = 0.8
    max_x = max(max(f.swrc[0]), max(f.swrc_wet[0])) * 2
    if id in [2310, 4700, 4890, 4920, 4940, 4941]:
        max_x *= 2.4
    min_y1 = 0
    max_y1 = max(f.qs, max(f.swrc[1]), max(f.swrc_wet[1])) * 1.1
    fig, ax1 = plt.subplots(figsize=[4.3, 3.2])
    ax1.set_xscale("log")
    fig.subplots_adjust(top=0.95, bottom=0.15, right=0.95, left=0.15)
    ax1.axis([min_x, max_x, min_y1, max_y1])
    ax1.set_xlabel('h (cm)')
    ax1.set_ylabel('$\\theta$')
    id = f.general['code']
    h, t = f.swrc
    h[h == 0] = 1
    ax1.plot(h, t, marker='o', linestyle='', color='black', label='Drying')
    h, t = f.swrc_wet
    h[h == 0] = 1
    ax1.plot(h, t, marker='^', linestyle='',
             color='red', label='Wetting')
    x = 2**np.linspace(math.log2(min_x),
                       math.log2(max_x), num=f.curve_smooth)
    y = f.f_ht(f.fitted, x)
    ax1.plot(x, y, color='black', linestyle='dashed', label=f'{f.model_name}')
    h, t = f.swrc_wet
    theta = f.smooth_theta((min(t), f.qs_wet))
    f.cos_g0 = f.contact(h[0], t[0])
    h_opt = f.h(f.hyst, theta)
    ax1.plot(h_opt, theta, marker='', linestyle='dotted',
             color='red', label='Zhou')
    loc = 'upper right'
    if min(f.swrc[1]) > 0.4:
        loc = 'lower right'
    leg = fig.legend(title=f'UNSODA {id}', loc=loc)
    leg.get_frame().set_alpha(1)
    plt.savefig(f'unsoda{id}.png')


if __name__ == "__main__":
    main()
