"""
This is starter code to demonstrate a working example of a EPI Spin Echo as a pure Python implementation.
"""
import time
start = time.time()

from math import pi, sqrt, ceil

from mr_gpi.Sequence.sequence import Sequence
from mr_gpi.calcduration import calcduration
from mr_gpi.makeadc import makeadc
from mr_gpi.makeblock import makeblockpulse
from mr_gpi.makedelay import makedelay
from mr_gpi.makesinc import makesincpulse
from mr_gpi.maketrap import maketrapezoid
from mr_gpi.opts import Opts


kwargs_for_opts = {"max_grad": 33, "grad_unit": "mT/m", "max_slew": 110, "slew_unit": "T/m/s", "rf_dead_time": 10e-6,
                   "adc_dead_time": 10e-6}
system = Opts(kwargs_for_opts)
seq = Sequence(system)

TE, TR = 70e-3, 200e-3
fov = 220e-3
Nx = 64
Ny = 64
slice_thickness = 3e-3
dt_GE = 4e-6

flip = 90 * pi / 180
kwargs_for_sinc = {"flip_angle": flip, "system": system, "duration": 2.5e-3, "slice_thickness": slice_thickness,
                   "apodization": 0.5, "time_bw_product": 4}
rf, gz = makesincpulse(kwargs_for_sinc, 2)
# plt.plot(rf.t[0], rf.signal[0])
# plt.show()

delta_k = 1 / fov
kWidth = Nx * delta_k
readoutTime = Nx * dt_GE
kwargs_for_gx = {"channel": 'x', "system": system, "flat_area": kWidth, "flat_time": readoutTime}
gx = maketrapezoid(kwargs_for_gx)
kwargs_for_adc = {"num_samples": Nx, "system": system, "duration": gx.flat_time, "delay": gx.rise_time}
adc = makeadc(kwargs_for_adc)

pre_time = 8e-4
kwargs_for_gxpre = {"channel": 'x', "system": system, "area": -gx.area / 2 - delta_k / 2, "duration": pre_time}
gx_pre = maketrapezoid(kwargs_for_gxpre)
kwargs_for_gz_reph = {"channel": 'z', "system": system, "area": -gz.area / 2, "duration": pre_time}
gz_reph = maketrapezoid(kwargs_for_gz_reph)
kwargs_for_gy_pre = {"channel": 'y', "system": system, "area": -Ny / 2 * delta_k, "duration": pre_time}
gy_pre = maketrapezoid(kwargs_for_gy_pre)

dur = ceil(2 * sqrt(delta_k / system.max_slew) / 10e-6) * 10e-6
kwargs_for_gy = {"channel": 'y', "system": system, "area": delta_k, "duration": dur}
gy = maketrapezoid(kwargs_for_gy)

flip = 180 * pi / 180
kwargs_for_sinc = {"flip_angle": flip, "system": system, "duration": 500e-6}
rf180 = makeblockpulse(kwargs_for_sinc)
kwargs_for_gz_spoil = {"channel": 'z', "system": system, "area": gz.area * 2, "duration": 3 * pre_time}
gz_spoil = maketrapezoid(kwargs_for_gz_spoil)


duration_to_center = (Nx / 2 + 0.5) * calcduration(gx) + Ny / 2 * calcduration(gy)
delayTE1 = TE / 2 - calcduration(gz) / 2 - pre_time - calcduration(gz_spoil) - calcduration(rf180) / 2
delayTE2 = TE / 2 - calcduration(rf180) / 2 - calcduration(gz_spoil) - duration_to_center
delay1 = makedelay(delayTE1)
delay2 = makedelay(delayTE2)

seq.add_block(rf, gz)
seq.add_block(gx_pre, gy_pre, gz_reph)
seq.add_block(delay1)
seq.add_block(gz_spoil)
seq.add_block(rf180)
seq.add_block(gz_spoil)
seq.add_block(delay2)
for i in range(Ny):
    seq.add_block(gx, adc)
    seq.add_block(gy)
    gx.amplitude = -gx.amplitude
seq.add_block(makedelay(1))

# Display 1 TR
#seq.plot(time_range=(0, TR))

# Display entire plot
# seq.plot()

# The .seq file will be available inside the /gpi/<user>/pulseq-gpi folder
seq.write("SE_EPI_Python_28082017.seq")

print ('It took', time.time()-start, 'seconds.')