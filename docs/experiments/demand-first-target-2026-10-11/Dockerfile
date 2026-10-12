FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY target /target
# The credential-free git archive lacks VCS version metadata. Supply only the
# distribution version via versioningit's PKG-INFO fallback; source stays pinned.
RUN python -c "from pathlib import Path; Path('/target/PKG-INFO').write_text('Metadata-Version: 2.1\nName: audio_feeder\nVersion: 0.0.0+study.2a5b58d\n')"
# Acquire wheels as data; never invoke a downloaded sdist build backend online.
RUN python -c "import tomllib; from pathlib import Path; p=tomllib.loads(Path('/target/pyproject.toml').read_text()); Path('/requirements.txt').write_text('\n'.join(p['project']['dependencies'] + p['build-system']['requires'] + ['pytest', 'hypothesis']))" \
    && python -m pip download --only-binary=:all: --dest /wheels -r /requirements.txt
# The target's setup/backend and wheel installation execute without networking.
RUN --network=none python -m pip install --no-index --find-links=/wheels setuptools wheel versioningit \
    && python -m pip install --no-index --find-links=/wheels --no-build-isolation /target pytest hypothesis \
    && python -m pip freeze > /dependencies.txt
COPY study /study
WORKDIR /study
CMD ["python", "native_http.py", "/results"]
