import sys
from agents.orchestrator import run


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<your workforce question>\"")
        print("\nExample:")
        print("  python main.py \"Should we increase compensation for software engineers in Ireland?\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"\nProcessing query: {query}\n")
    print("-" * 60)

    state, report = run(query)

    if state.errors:
        print("\n[Warnings]")
        for err in state.errors:
            print(f"  - {err}")
        print()

    print(report)


if __name__ == "__main__":
    main()
