import sys

def main():
    """handing opens the gui, handing --cli [--live] runs in the terminal"""
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from handing.pipeline import cli
        cli.main()
    else:
        from handing.gui import app
        sys.exit(app.main())

if __name__ == "__main__":
    main()
