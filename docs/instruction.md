# Instruction of hystfit
To begin, install Python 3 along with the `hystfit` library. For installing on Debian system, [APT repository](https://sekika.github.io/apt/) is available.

Once installed, create a fitting object `f` from the `hystfit.Fit` class, which is a subclass of the `unsatfit.Fit` class. For more detailed information, refer to the [unsatfit documentation](https://sekika.github.io/unsatfit/).

```python
import math
import numpy as np
import hystfit
f = hystfit.Fit()
```

## Main drying curve
The main drying curve can be modeled using either the [van Genuchten](https://acsess.onlinelibrary.wiley.com/doi/10.2136/sssaj1980.03615995004400050002x) (VG) or the [Fredlund and Xing](http://dx.doi.org/10.1139/t94-061) (FX) model. Once a model is chosen, parameters can be set in two ways:

(1) **Provide given parameters**:
- For the VG model, parameters (&theta;<sub>s</sub>, &theta;<sub>r</sub>, &alpha;, n) can be set as follows:
  ```python
  f.set_vg(0.33, 0.05, 1 / 180, 1.65)
  ```
- For the FX model, parameters (&theta;<sub>s</sub>, &theta;<sub>r</sub>, a, m, n) can be set as follows:
  ```python
  f.set_fx(0.35, 0.02, 45, 1.25, 7.23)
  ```

(2) **Optimize parameters from measured data (h, &theta;)**:

As `hystfit.Fit` is a subclass of `unsatfit.Fit`, all methods from `unsatfit` are available in `f`. You can obtain fitting parameters for the main drying curve using `unsatfit` methods such as `get_init_vg` and `get_wrf_vg`. Note that for the VG function, parameter m should be converted to n=1/(1-m).

Set the water retention data (h, &theta;) for the main drying curve in `f.swrc` as described in the `unsatfit` documentation. After that, to obtain and set VG parameters:
```python
qs, qr, a, m, q = f.get_wrf_vg()
n = 1 / (1 - m)
f.set_vg(qs, qr, a, n)
```
To obtain and set FX parameters:
```python
f.set_fx(*f.get_wrf_fx())
```

If &theta;<sub>r</sub> is equal to 0, you can use the `init_hyst` method. For instance, for the VG model:
```python
f.model_name = 'VG'
f.init_hyst()
print(f.message)
```
To use the FX model, simply set `f.model_name = 'FX'`.

## Hysteresis parameters
The hysteresis behavior in soil is determined by the advancing contact angle (&gamma;<sub>A</sub>) and the parameter b. These parameters are collectively set in a single tuple `p`, defined as p=(cos &gamma;<sub>A</sub>, b). For instance, to set &gamma;<sub>A</sub> = 75&deg; and b = 0.24:
```python
p = (math.cos(math.radians(75)), 0.24)
```
Please note that in Zhou (2013), the contact angle is denoted by &theta;; however, we use &gamma; instead to avoid confusion with volumetric water content. A detailed description of Zhou's model is omitted here; please refer to [Zhou's paper](https://doi.org/10.1016/j.compgeo.2012.10.004) for more information.

The receding contact angle &gamma;<sub>r</sub> is fixed at 0&deg;, and its cosine value is initially set to `f.cos_gr = 1`. This value remains unchanged unless manually altered by the user.

## Predicting change in h from change in &theta;
The change in h can be predicted from changes in &theta; using the `h` method as shown below:
```python
h = f.h(p, theta)
```
Where:
- `p` represents (cos &gamma;<sub>A</sub>, b).
- `theta` is a numpy array representing the change in &theta;.
- `f.cos_g0` is set to cos(&gamma;<sub>0</sub>).

By default, the initial contact angle &gamma;<sub>0</sub> is set at 0&deg;, meaning `f.cos_g0 = 1`. Since it is the same as the default &gamma;<sub>R</sub>, it indicates that the initial (h,&theta;) data point is on the main drying curve. After executing the `h` method, &gamma;<sub>0</sub> is updated to the last state, enabling the reproduction of the hysteresis behavior through repeated usage of the `h` method. &gamma;<sub>0</sub> is reset to 0&deg; when `set_vg` or `set_fx` methods are called.

To set &gamma;<sub>0</sub> to a specific state of (h, &theta;):
```python
f.cos_g0 = f.contact(h_ini, theta_ini)
```
Here, `h_ini` and `theta_ini` represent the initial values of h and &theta;, respectively.

## Optimizing hysteresis parameters from changes in (h, &theta;)
To optimize hysteresis parameters based on changes in (h, &theta;)—for instance, from the main wetting curve—use the `opt` method. Ensure that each (h, &theta;) dataset adheres to the data structure conventions of `unsatfit`, and that the order of the data reflects the sequence of time events. The optimization can be performed with the following code:
```python
f.opt(h, theta)
p = f.hyst
print(f'{f.message} R2 = {f.r2:.3}')
```
This code obtains the hysteresis parameter p=(cos &gamma;<sub>A</sub>, b) and outputs the result. In the optimization, the residual of ln(h) is used as the cost function. Note that the contact angle &gamma;<sub>0</sub> is set at the initial state before optimization and updated to its last state after this operation.
