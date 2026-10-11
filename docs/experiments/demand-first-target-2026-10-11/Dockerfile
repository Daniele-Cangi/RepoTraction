FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY target /target
# The credential-free git archive lacks VCS version metadata. Supply only the
# distribution version via versioningit's PKG-INFO fallback; source stays pinned.
RUN python -c "from pathlib import Path; Path('/target/PKG-INFO').write_text('Metadata-Version: 2.1\nName: audio_feeder\nVersion: 0.0.0+study.2a5b58d\n')"
RUN python -m pip install /target pytest hypothesis && python -m pip freeze > /dependencies.txt
COPY study /study
WORKDIR /study
CMD ["python", "native_http.py", "/results"]
