import argparse
import logging
import sys
import time

from inverters import InverterModel, ModbusConfig, get_inverter_class

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("main")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poll inverter metrics over Modbus and push to MQTT."
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=[m.value for m in InverterModel],
        help="The specific hardware model string."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Polling interval in seconds"
    )

    parser.add_argument(
        "--port",
        type=str,
        default="/dev/ttyUSB0",
        help="Serial port connection path"
    )

    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Modbus serial baudrate"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Modbus response timeout in seconds"
    )

    parser.add_argument(
        "--slave-id",
        type=int,
        default=1,
        help="Modbus slave/unit ID address"
    )

    parser.add_argument(
        "--parity",
        type=str,
        default="N",
        choices=["N", "E", "O"],
        help="Serial parity"
    )

    parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress informational logs; only warnings and errors are emitted",
    )

    parser.add_argument(
        "--publisher",
        action="append",
        dest="publisher_configs",
        default=[],
        help="JSON string defining a publisher configuration. Must include a 'name' field."
    )

    args = parser.parse_args()

    if args.silent:
        logger.setLevel(logging.WARN)

    InverterClass = get_inverter_class(args.model)

    inverter = InverterClass(
        config=ModbusConfig(
            port=args.port,
            baudrate=args.baudrate,
            timeout=args.timeout,
            slave_id=args.slave_id,
            parity=args.parity
        )
    )

    print(
        f"Connected to {args.model} via {inverter.config.port} ({inverter.config.baudrate} baud)")
    print(f"Polling metrics every {args.interval}s...")

    try:
        while True:
            start_time = time.time()

            try:
                data = inverter.read_telemetry()
                logger.info(f"[Metrics]: {data}")
            except Exception as e:
                logger.exception(f"Modbus Read Failure", exc_info=e)

            elapsed = time.time() - start_time
            time.sleep(max(0, args.interval - elapsed))

    except KeyboardInterrupt:
        logger.info("\nExiting service daemon.")
        sys.exit(0)


if __name__ == "__main__":
    main()
