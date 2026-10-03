"""Print duration, size and streams of rendered trailer files, to check them against the targets."""

import sys
from pathlib import Path

import av

for name in sys.argv[1:]:
    path = Path(name)
    with av.open(str(path)) as container:
        duration = container.duration / av.time_base if container.duration else 0.0
        streams = []
        for stream in container.streams:
            context = stream.codec_context
            if stream.type == "video":
                streams.append(f"video {context.name} {context.width}x{context.height}")
            elif stream.type == "audio":
                streams.append(f"audio {context.name} {context.sample_rate}Hz {context.channels}ch")
    size_mb = path.stat().st_size / 1_048_576
    print(f"{path.name}: {size_mb:.2f} MB, {duration:.2f}s, {'; '.join(streams)}")
