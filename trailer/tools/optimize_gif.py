"""Re-encode the email GIF so each frame stores only what changed, on one shared palette.

    uv run --with pillow python trailer/tools/optimize_gif.py <in.gif> <out.gif> <frame_ms>
"""

import sys

from PIL import Image, ImageSequence

source, target, frame_ms = sys.argv[1], sys.argv[2], int(sys.argv[3])
with Image.open(source) as gif:
    frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(gif)]

# One palette for the whole loop, built from a strip of every frame, so colours never shimmer.
strip = Image.new("RGB", (frames[0].width, frames[0].height * len(frames)))
for index, frame in enumerate(frames):
    strip.paste(frame, (0, frames[0].height * index))
palette = strip.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
paletted = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]

paletted[0].save(
    target,
    save_all=True,
    append_images=paletted[1:],
    duration=frame_ms,
    loop=0,
    optimize=True,
    disposal=1,
)
print(f"{len(frames)} frames")
