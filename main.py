import multiprocessing


def main() -> None:
    multiprocessing.freeze_support()

    # i18n MUST be initialized before any import that uses _()
    from src.whisperai.utils.i18n import detect_system_language, set_language
    lang = detect_system_language()
    set_language(lang)

    from src.whisperai.app import create_app
    create_app()


if __name__ == "__main__":
    main()
