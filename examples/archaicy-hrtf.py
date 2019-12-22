#!/usr/bin/env python3
# HRTF rendering example using ALC_SOFT_HRTF extension
# Copyright (C) 2019  Nguyễn Gia Phong
#
# This file is part of archaicy.
#
# archaicy is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# archaicy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with archaicy.  If not, see <https://www.gnu.org/licenses/>.

from argparse import ArgumentParser
from datetime import datetime, timedelta
from itertools import count, takewhile
from sys import stderr
from time import sleep
from typing import Iterable

from archaicy import ALC_TRUE, ALC_HRTF_SOFT, ALC_HRTF_ID_SOFT, DeviceManager

PERIOD = 0.025


def pretty_time(seconds: float) -> str:
    """Return human-readably formatted time."""
    time = datetime.min + timedelta(seconds=seconds)
    if seconds < 3600: return time.strftime('%M:%S')
    return time.strftime('%H:%M:%S')


def hrtf(files: Iterable[str], device: str, hrtf_name: str,
         omega: float, angle: float):
    devmrg = DeviceManager()
    try:
        dev = devmrg.open_playback(device)
    except RuntimeError:
        stderr.write(f'Failed to open "{device}" - trying default\n')
        dev = devmrg.open_playback()
    print('Opened', dev.full_name)

    hrtf_names = dev.hrtf_names
    if hrtf_names:
        print('Available HRTFs:')
        for name in hrtf_names: print(f'    {name}')
    else:
        print('No HRTF found!')
    attrs = {ALC_HRTF_SOFT: ALC_TRUE}
    if hrtf_name is not None:
        try:
            attrs[ALC_HRTF_ID_SOFT] = hrtf_names.index(hrtf_name)
        except ValueError:
            stderr.write(f'HRTF "{hrtf_name}" not found\n')

    with dev.create_context(attrs) as ctx:
        if dev.hrtf_enabled:
            print(f'Using HRTF "{dev.current_hrtf}"')
        else:
            print('HRTF not enabled!')

        for filename in files:
            try:
                decoder = ctx.create_decoder(filename)
            except RuntimeError:
                stderr.write(f'Failed to open file: {filename}\n')
                continue
            source = ctx.create_source()

            source.play_from_decoder(decoder, 12000, 4)
            print(f'Playing {filename} ({decoder.sample_type_name},',
                  f'{decoder.channel_config_name}, {decoder.frequency} Hz)')

            invfreq = 1 / decoder.frequency
            for i in takewhile(lambda i: source.playing, count(step=PERIOD)):
                source.stereo_angles = i*omega, i*omega+angle
                print(f' {pretty_time(source.sample_offset*invfreq)} /'
                      f' {pretty_time(decoder.length*invfreq)}',
                      end='\r', flush=True)
                sleep(PERIOD)
                ctx.update()
            print()
            source.destroy()
    dev.close()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('files', nargs='+', help='audio files')
    parser.add_argument('-d', '--device', help='device name')
    parser.add_argument('-n', '--hrtf', dest='hrtf_name', help='HRTF name')
    parser.add_argument('-o', '--omega', type=float, default=1.0,
                        help='angular velocity')
    parser.add_argument('-a', '--angle', type=float, default=1.0,
                        help='relative angle between left and right sources')
    args = parser.parse_args()
    hrtf(args.files, args.device, args.hrtf_name, args.omega, args.angle)
