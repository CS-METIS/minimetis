import sarge  # type: ignore


def _get_error_text(p):
    if p.stderr:
        return p.stderr.text
    if p.stdout:
        return p.stdout.text
    return "unknown error"


def call(cmd: str, stdin: str = None, cwd=None) -> str:
    print(cmd)
    p = sarge.capture_both(cmd, input=stdin, cwd=cwd, shell=True)
    if p.returncode != 0:
        raise RuntimeError(f"command {p.commands} exits with error code {p.returncode}")
    return p.stdout.text


def run(cmd: str, stdin: str = None, cwd=None):
    print(cmd)
    p = sarge.run(cmd, input=stdin, cwd=cwd, shell=True)
    if p.returncode != 0:
        raise RuntimeError(f"command {p.commands} exists with error code {p.returncode} {_get_error_text(p)}")
