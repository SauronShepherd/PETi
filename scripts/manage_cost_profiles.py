"""Explicit-input cost profile administration helper; never mutates by itself."""
import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Describe a cost-profile change for operator review")
    parser.add_argument("operation_type")
    parser.add_argument("credit_cost", type=int)
    parser.add_argument("--disabled", action="store_true")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    print({"operation_type": args.operation_type, "credit_cost": args.credit_cost, "enabled": not args.disabled, "requires_operator_confirmation": True})
