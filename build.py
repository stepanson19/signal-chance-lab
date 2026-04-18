import subprocess
import sys


def main():
    commands = [
        [sys.executable, "manage.py", "migrate", "--noinput"],
        [sys.executable, "manage.py", "seed_signal_lab"],
        [sys.executable, "manage.py", "collectstatic", "--noinput"],
    ]
    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
