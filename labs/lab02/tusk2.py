"""Analyze sudo logs and detect potentially suspicious commands."""

import argparse
import json
import logging
import re
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_LOG = Path("labs/lab02/data/data_v15/sudo.log")
DEFAULT_OUTPUT = Path("labs/lab02/sudo_report.json")

DEFAULT_ALERT_COMMANDS = [
    "chmod 777",
    "nc",
    "nmap",
    "dd",
    "/etc/shadow",
]


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze sudo logs and detect suspicious commands."
    )
    parser.add_argument(
        "--sudo-log",
        type=Path,
        default=DEFAULT_LOG,
        help="Path to the sudo log file.",
    )
    parser.add_argument(
        "--alert-commands",
        default=",".join(DEFAULT_ALERT_COMMANDS),
        help="Comma-separated suspicious command patterns.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the JSON report.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level.",
    )
    return parser.parse_args()


def parse_sudo_line(line):
    """Parse one sudo log line."""
    pattern = (
        r"^(?P<timestamp>\S+)\s+"
        r"(?P<host>\S+)\s+sudo:\s*"
        r"(?P<user>[^:]+?)\s*:\s*"
        r"TTY=(?P<tty>.*?)\s*;\s*"
        r"PWD=(?P<pwd>.*?)\s*;\s*"
        r"USER\s*=\s*(?P<target_user>.*?)\s*;\s*"
        r"COMMAND\s*=\s*(?P<command>.+?)\s*$"
    )

    match = re.match(pattern, line.strip())

    if not match:
        return None

    record = match.groupdict()

    for key, value in record.items():
        record[key] = value.strip()

    return record


def is_suspicious(command, alert_commands):
    """Check whether a command matches a suspicious pattern."""
    command_lower = command.lower()

    return any(
        pattern.strip().lower() in command_lower
        for pattern in alert_commands
        if pattern.strip()
    )


def analyze_log(log_path, alert_commands):
    """Analyze the log and collect root and suspicious command records."""
    root_commands = []
    suspicious_commands = []
    suspicious_by_user = Counter()
    total_parsed = 0
    total_unparsed = 0

    with log_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as log_file:
        for line_number, line in enumerate(log_file, start=1):
            if not line.strip():
                continue

            record = parse_sudo_line(line)

            if record is None:
                total_unparsed += 1
                logger.debug(
                    "Could not parse line %d",
                    line_number,
                )
                continue

            total_parsed += 1
            command = record["command"]

            if record["target_user"] == "root":
                root_commands.append(record)

                if is_suspicious(command, alert_commands):
                    suspicious_commands.append(record)
                    suspicious_by_user[record["user"]] += 1

    return {
        "source_file": str(log_path),
        "total_parsed": total_parsed,
        "total_unparsed": total_unparsed,
        "root_commands_count": len(root_commands),
        "root_commands": root_commands,
        "suspicious_commands_count": len(suspicious_commands),
        "suspicious_commands": suspicious_commands,
        "suspicious_by_user": dict(suspicious_by_user.most_common()),
    }


def main():
    """Run the sudo log analyzer."""
    args = parse_arguments()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    if not args.sudo_log.is_file():
        logger.error("Log file not found: %s", args.sudo_log)
        raise SystemExit(1)

    alert_commands = args.alert_commands.split(",")

    try:
        report = analyze_log(args.sudo_log, alert_commands)
        args.out_json.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with args.out_json.open(
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                report,
                output_file,
                ensure_ascii=False,
                indent=4,
            )

    except OSError as error:
        logger.error("File operation failed: %s", error)
        raise SystemExit(1) from error

    logger.info("Analysis completed.")
    print(f"Оброблено записів: {report['total_parsed']}")
    print(f"Команд від root: {report['root_commands_count']}")
    print(f"Підозрілих команд: {report['suspicious_commands_count']}")
    print("Підозрілі команди за користувачами:")

    for username, count in report["suspicious_by_user"].items():
        print(f" {username}: {count}")

    print(f"JSON-звіт збережено: {args.out_json}")


if __name__ == "__main__":
    main()
